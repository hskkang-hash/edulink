import os
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class OperationsSprint7To10Test(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_ops_sprint7_10.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"
        os.environ["SECRET_KEY"] = "test-secret-ops-sprint"
        os.environ["ALLOW_PRIVILEGED_SELF_REGISTER"] = "true"

        if "app_jwt" in sys.modules:
            del sys.modules["app_jwt"]

        from prometheus_client import REGISTRY

        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass

        import app_jwt

        self.app_module = app_jwt
        self.client = app_jwt.app.test_client()
        self.engine = app_jwt.engine

    def tearDown(self):
        try:
            self.engine.dispose()
        except Exception:
            pass
        try:
            self.tmpdir.cleanup()
        except Exception:
            pass

    def _register_and_login(self, email, role, password="TestPass123"):
        self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": role},
        )
        login_res = self.client.post(
            "/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(login_res.status_code, 200)
        return login_res.get_json()["access_token"]

    def test_posting_template_and_compare(self):
        institution_token = self._register_and_login(
            "inst.ops@edulink.local", "institution"
        )
        instructor_token = self._register_and_login(
            "teacher.ops@edulink.local", "instructor"
        )

        tpl_res = self.client.post(
            "/postings/templates",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={
                "name": "Weekly Math",
                "title": "Math Regular Class",
                "subject": "math",
                "region": "Seoul",
                "rate": 55000,
                "required_fields": ["title", "subject", "region", "rate"],
                "recurrence_type": "weekly",
                "recurrence_days": ["Mon", "Wed"],
            },
        )
        self.assertEqual(tpl_res.status_code, 201)
        template_id = tpl_res.get_json()["id"]

        create_from_tpl_res = self.client.post(
            f"/postings/templates/{template_id}/instantiate",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={"title": "Math Class A"},
        )
        self.assertEqual(create_from_tpl_res.status_code, 201)
        posting_id = create_from_tpl_res.get_json()["id"]

        # Instructor must have an approved profile before applying
        with self.engine.begin() as conn:
            instructor_uid = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "teacher.ops@edulink.local"},
            ).scalar()
            conn.execute(
                text("""
                    INSERT INTO instructor_profiles (
                        user_id, full_name, status,
                        background_check_consent, child_abuse_consent,
                        withholding_consent, created_at, updated_at
                    ) VALUES (
                        :user_id, 'Teacher Ops', 'approved',
                        1, 1, 1, datetime('now'), datetime('now')
                    )
                """),
                {"user_id": instructor_uid},
            )

        apply_res = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(apply_res.status_code, 201)

        compare_res = self.client.get(
            f"/applications/compare?posting_id={posting_id}",
            headers={"Authorization": f"Bearer {institution_token}"},
        )
        self.assertEqual(compare_res.status_code, 200)
        payload = compare_res.get_json()
        self.assertEqual(payload["posting"]["id"], posting_id)
        self.assertGreaterEqual(payload["count"], 1)

    def test_session_and_sos_events(self):
        institution_token = self._register_and_login(
            "inst.events@edulink.local", "institution"
        )
        instructor_token = self._register_and_login(
            "teacher.events@edulink.local", "instructor"
        )

        posting_res = self.client.post(
            "/postings",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={
                "title": "Science Sprint",
                "subject": "science",
                "region": "Busan",
                "rate": 60000,
            },
        )
        self.assertEqual(posting_res.status_code, 201)
        posting_id = posting_res.get_json()["id"]

        # Instructor must have an approved profile before applying
        with self.engine.begin() as conn:
            instructor_id = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "teacher.events@edulink.local"},
            ).scalar()
            conn.execute(
                text(
                    """
                    INSERT INTO instructor_profiles (
                        user_id, full_name, status,
                        background_check_consent, child_abuse_consent,
                        withholding_consent, created_at, updated_at
                    ) VALUES (
                        :user_id, 'Teacher Event', 'approved',
                        1, 1, 1, datetime('now'), datetime('now')
                    )
                    """
                ),
                {"user_id": instructor_id},
            )

        apply_res = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(apply_res.status_code, 201)
        app_id = apply_res.get_json()["id"]

        approve_res = self.client.patch(
            f"/applications/{app_id}",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={"status": "approved"},
        )
        self.assertEqual(approve_res.status_code, 200)

        create_session_res = self.client.post(
            "/sessions",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={
                "posting_id": posting_id,
                "instructor_id": instructor_id,
                "scheduled_at": "2026-03-31T10:00:00Z",
                "scheduled_duration_minutes": 60,
            },
        )
        self.assertEqual(create_session_res.status_code, 201)
        session_id = create_session_res.get_json()["id"]

        checkin_res = self.client.post(
            f"/sessions/{session_id}/checkin",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"lat": 37.5665, "lng": 126.9780},
        )
        self.assertEqual(checkin_res.status_code, 200)

        complete_res = self.client.post(
            f"/sessions/{session_id}/complete",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"journal_content": "Completed chapter 1", "actual_duration_minutes": 55},
        )
        self.assertEqual(complete_res.status_code, 200)

        sos_create_res = self.client.post(
            "/sos",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={
                "title": "Urgent replacement",
                "subject": "math",
                "region": "Seoul",
                "scheduled_at": "2026-04-01T09:00:00Z",
                "rate": 70000,
            },
        )
        self.assertEqual(sos_create_res.status_code, 201)
        sos_id = sos_create_res.get_json()["id"]

        sos_accept_res = self.client.post(
            f"/sos/{sos_id}/accept",
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        self.assertEqual(sos_accept_res.status_code, 200)

        with self.engine.connect() as conn:
            event_types = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT event_type FROM session_events WHERE event_type IN ('session_created','session_checkin','session_completed','sos_created','sos_accepted')"
                    )
                ).fetchall()
            }

        self.assertIn("session_created", event_types)
        self.assertIn("session_checkin", event_types)
        self.assertIn("session_completed", event_types)
        self.assertIn("sos_created", event_types)
        self.assertIn("sos_accepted", event_types)


if __name__ == "__main__":
    unittest.main()
