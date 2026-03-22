import os
import tempfile
import unittest
from importlib import reload
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class MvpFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_edulink.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"
        os.environ["SECRET_KEY"] = "test-secret"

        # Import after env vars so app binds to test DB.
        import app as app_module

        self.app_module = reload(app_module)
        self.client = self.app_module.app.test_client()

    def tearDown(self):
        self.app_module.engine.dispose()
        try:
            self.tmpdir.cleanup()
        except PermissionError:
            # On Windows, SQLite file handles can be released slightly later.
            pass
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("SECRET_KEY", None)

    def register(self, email, role):
        response = self.client.post(
            "/auth/register",
            json={"email": email, "password": "Pass1234", "role": role},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIn("access_token", payload)
        return payload["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_student_cannot_create_posting(self):
        student_token = self.register("student1@test.com", "student")

        response = self.client.post(
            "/postings",
            headers=self.auth_header(student_token),
            json={"title": "Math", "subject": "math", "region": "Seoul", "rate": 30000},
        )

        self.assertEqual(response.status_code, 403)

    def test_instructor_can_create_and_manage_posting(self):
        instructor_token = self.register("inst1@test.com", "instructor")

        create_response = self.client.post(
            "/postings",
            headers=self.auth_header(instructor_token),
            json={"title": "Algebra", "subject": "math", "region": "Seoul", "rate": 50000},
        )
        self.assertEqual(create_response.status_code, 201)
        posting_id = create_response.get_json()["id"]

        update_response = self.client.put(
            f"/postings/{posting_id}",
            headers=self.auth_header(instructor_token),
            json={"title": "Algebra Advanced", "subject": "math", "region": "Seoul", "rate": 55000},
        )
        self.assertEqual(update_response.status_code, 200)

        delete_response = self.client.delete(
            f"/postings/{posting_id}",
            headers=self.auth_header(instructor_token),
        )
        self.assertEqual(delete_response.status_code, 200)

    def test_student_apply_and_instructor_approve(self):
        instructor_token = self.register("inst2@test.com", "instructor")
        student_token = self.register("student2@test.com", "student")

        create_response = self.client.post(
            "/postings",
            headers=self.auth_header(instructor_token),
            json={"title": "Physics", "subject": "science", "region": "Busan", "rate": 40000},
        )
        self.assertEqual(create_response.status_code, 201)
        posting_id = create_response.get_json()["id"]

        apply_response = self.client.post(
            "/applications",
            headers=self.auth_header(student_token),
            json={"posting_id": posting_id},
        )
        self.assertEqual(apply_response.status_code, 201)
        application_id = apply_response.get_json()["id"]

        # Duplicate apply should be blocked.
        duplicate_response = self.client.post(
            "/applications",
            headers=self.auth_header(student_token),
            json={"posting_id": posting_id},
        )
        self.assertEqual(duplicate_response.status_code, 409)

        approve_response = self.client.patch(
            f"/applications/{application_id}",
            headers=self.auth_header(instructor_token),
            json={"status": "approved"},
        )
        self.assertEqual(approve_response.status_code, 200)

        list_response = self.client.get(
            "/applications?status=approved",
            headers=self.auth_header(instructor_token),
        )
        self.assertEqual(list_response.status_code, 200)
        items = list_response.get_json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "approved")

    def test_auth_me_requires_valid_bearer(self):
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

        invalid_response = self.client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid"},
        )
        self.assertEqual(invalid_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
