import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class InstructorProfileSessionFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_profile_sessions.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"
        os.environ["SECRET_KEY"] = "test-secret-key-profile-sessions"

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
        self.engine = app_jwt.engine
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        try:
            self.engine.dispose()
        except Exception:
            pass
        try:
            self.tmpdir.cleanup()
        except PermissionError:
            pass

    def test_instructor_application_requires_approved_profile(self):
        institution_token = self._register_user("org@apps.com", "institution")
        instructor_token = self._register_user("teacher@apps.com", "instructor")
        admin_token = self._register_user("admin@apps.com", "admin")

        posting_res = self.client.post(
            "/postings",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={"title": "Science Class", "subject": "science", "region": "Busan", "rate": 55000},
        )
        self.assertEqual(posting_res.status_code, 201)
        posting_id = posting_res.get_json()["id"]

        blocked_without_profile = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(blocked_without_profile.status_code, 403)

        self._create_profile(instructor_token, subject="science", region="Busan")

        pending_apply = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(pending_apply.status_code, 403)

        self._approve_latest_profile(admin_token)

        approved_apply = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(approved_apply.status_code, 201)

    def test_session_lifecycle_and_instructor_dashboard_stats(self):
        institution_token = self._register_user("org@sessions.com", "institution")
        instructor_token = self._register_user("teacher@sessions.com", "instructor")
        admin_token = self._register_user("admin@sessions.com", "admin")

        self._create_profile(instructor_token, subject="math", region="Seoul")
        self._approve_latest_profile(admin_token)

        posting_res = self.client.post(
            "/postings",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={"title": "Algebra Intensive", "subject": "math", "region": "Seoul", "rate": 60000},
        )
        self.assertEqual(posting_res.status_code, 201)
        posting_id = posting_res.get_json()["id"]

        application_res = self.client.post(
            "/applications",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"posting_id": posting_id},
        )
        self.assertEqual(application_res.status_code, 201)
        application_id = application_res.get_json()["id"]

        approve_res = self.client.patch(
            f"/applications/{application_id}",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={"status": "approved"},
        )
        self.assertEqual(approve_res.status_code, 200)

        session_create = self.client.post(
            "/sessions",
            headers={"Authorization": f"Bearer {institution_token}"},
            json={
                "posting_id": posting_id,
                "instructor_id": self._user_id_from_token(instructor_token),
                "scheduled_at": "2030-03-24T09:00:00+00:00",
                "scheduled_duration_minutes": 60,
            },
        )
        self.assertEqual(session_create.status_code, 201)
        session_id = session_create.get_json()["id"]

        checkin_res = self.client.post(
            f"/sessions/{session_id}/checkin",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"lat": 37.5665, "lng": 126.9780},
        )
        self.assertEqual(checkin_res.status_code, 200)

        complete_res = self.client.post(
            f"/sessions/{session_id}/complete",
            headers={"Authorization": f"Bearer {instructor_token}"},
            json={"journal_content": "Completed algebra lesson", "actual_duration_minutes": 90},
        )
        self.assertEqual(complete_res.status_code, 200)
        self.assertEqual(complete_res.get_json()["gross_amount"], 90000)
        self.assertEqual(complete_res.get_json()["withholding_amount"], 2970)
        self.assertEqual(complete_res.get_json()["net_amount"], 87030)

        dashboard_res = self.client.get(
            "/dashboard/stats",
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        self.assertEqual(dashboard_res.status_code, 200)
        payload = dashboard_res.get_json()
        self.assertEqual(payload["role"], "instructor")
        self.assertEqual(payload["profile_status"], "approved")
        self.assertEqual(payload["completed_sessions_count"], 1)
        self.assertEqual(payload["upcoming_sessions_count"], 0)
        self.assertEqual(payload["income_summary"]["gross_amount"], 90000)
        self.assertEqual(payload["income_summary"]["withholding_amount"], 2970)
        self.assertEqual(payload["income_summary"]["net_amount"], 87030)

        activity_res = self.client.get(
            "/dashboard/activity?period=30d",
            headers={"Authorization": f"Bearer {instructor_token}"},
        )
        self.assertEqual(activity_res.status_code, 200)
        activity_types = [item["type"] for item in activity_res.get_json()]
        self.assertIn("session_completed", activity_types)
        self.assertIn("profile_reviewed", activity_types)

    def _create_profile(self, token, subject, region):
        profile_res = self.client.post(
            "/instructor/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Approved Instructor",
                "birth_date": "1990-01-01",
                "phone": "010-1234-5678",
                "subjects": [subject],
                "regions": [region],
                "available_hours": "weekday-evening",
                "education_level": "bachelor",
                "certifications": "teacher-license",
                "business_number": "123-45-67890",
                "bank_name": "KBank",
                "bank_account_masked": "123-***-7890",
                "background_check_consent": True,
                "child_abuse_consent": True,
                "withholding_consent": True,
            },
        )
        self.assertEqual(profile_res.status_code, 201)

    def _approve_latest_profile(self, admin_token):
        profiles_res = self.client.get(
            "/admin/profiles?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(profiles_res.status_code, 200)
        profiles = profiles_res.get_json()
        self.assertGreater(len(profiles), 0)
        profile_id = profiles[0]["id"]

        review_res = self.client.patch(
            f"/admin/profiles/{profile_id}/review",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"action": "approve", "admin_note": "verified"},
        )
        self.assertEqual(review_res.status_code, 200)

    def _register_user(self, email, role, password="TestPass123"):
        reg_res = self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": role},
        )
        if reg_res.status_code == 201:
            payload = reg_res.get_json()
            if "access_token" in payload:
                return payload["access_token"]

        login_res = self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(login_res.status_code, 200)
        return login_res.get_json()["access_token"]

    def _user_id_from_token(self, token):
        payload = self.app_module.verify_token(token)
        return payload["user_id"]


if __name__ == "__main__":
    unittest.main()
