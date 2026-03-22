import unittest
import tempfile
import os
from sqlalchemy import create_engine, text
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class FullUserJourneyTest(unittest.TestCase):
    """완전한 사용자 여정 테스트"""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_journey.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"
        os.environ["SECRET_KEY"] = "test-secret-key-journey"

        # Remove app_jwt from sys.modules to force reimport with new DATABASE_URL
        if 'app_jwt' in sys.modules:
            del sys.modules['app_jwt']
        
        # Clear Prometheus registry to avoid duplicate metric errors
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
        except:
            pass
        try:
            self.tmpdir.cleanup()
        except PermissionError:
            pass

    def test_full_journey_instructor_to_student(self):
        """완전한 여정: 회원가입 → 공고 → 지원 → 승인"""
        # 1. 강사 및 학생 등록 및 로그인
        inst_token = self._register_user('inst@journey.com', 'instructor', 'Journey123')
        student_token = self._register_user('student@journey.com', 'student', 'Journey123')

        # 2. 강사가 공고 작성
        posting_res = self.client.post(
            '/postings',
            headers={'Authorization': f'Bearer {inst_token}'},
            json={'title': 'Math Tutoring', 'subject': 'math', 'region': 'Seoul', 'rate': 50000}
        )
        self.assertEqual(posting_res.status_code, 201)
        posting_id = posting_res.get_json()['id']

        # 3. 학생이 공고 조회
        listings_res = self.client.get(
            '/postings?subject=math',
            headers={'Authorization': f'Bearer {student_token}'}
        )
        self.assertEqual(listings_res.status_code, 200)
        self.assertGreater(len(listings_res.get_json()), 0)

        # 4. 학생이 지원
        apply_res = self.client.post(
            '/applications',
            headers={'Authorization': f'Bearer {student_token}'},
            json={'posting_id': posting_id}
        )
        self.assertEqual(apply_res.status_code, 201)
        app_id = apply_res.get_json()['id']
        self.assertEqual(apply_res.get_json()['status'], 'pending')

        # 5. 강사가 지원 승인
        approve_res = self.client.patch(
            f'/applications/{app_id}',
            headers={'Authorization': f'Bearer {inst_token}'},
            json={'status': 'approved'}
        )
        self.assertEqual(approve_res.status_code, 200)
        self.assertEqual(approve_res.get_json()['status'], 'approved')

        # 6. 학생이 최종 상태 확인
        final_apps = self.client.get(
            '/applications?status=approved',
            headers={'Authorization': f'Bearer {student_token}'}
        )
        self.assertEqual(final_apps.status_code, 200)
        final = final_apps.get_json()
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]['status'], 'approved')

    def test_student_cannot_create_posting(self):
        """학생은 공고 생성 불가"""
        student_token = self._register_user('student@nopost.com', 'student')

        res = self.client.post(
            '/postings',
            headers={'Authorization': f'Bearer {student_token}'},
            json={'title': 'Try', 'subject': 'math', 'region': 'Seoul', 'rate': 40000}
        )
        self.assertEqual(res.status_code, 403)

    def test_duplicate_application_blocked(self):
        """중복 지원 방지"""
        inst_token = self._register_user('inst@dup.com', 'instructor')
        student_token = self._register_user('student@dup.com', 'student')

        posting_res = self.client.post(
            '/postings',
            headers={'Authorization': f'Bearer {inst_token}'},
            json={'title': 'Test', 'subject': 'math', 'region': 'Seoul', 'rate': 40000}
        )
        posting_id = posting_res.get_json()['id']

        # 첫 지원 - 성공
        first = self.client.post(
            '/applications',
            headers={'Authorization': f'Bearer {student_token}'},
            json={'posting_id': posting_id}
        )
        self.assertEqual(first.status_code, 201)

        # 중복 지원 - 실패
        dup = self.client.post(
            '/applications',
            headers={'Authorization': f'Bearer {student_token}'},
            json={'posting_id': posting_id}
        )
        self.assertEqual(dup.status_code, 409)

    def test_dashboard_stats_by_role(self):
        """역할별 대시보드 통계"""
        inst_token = self._register_user('inst@dash.com', 'instructor')
        student_token = self._register_user('student@dash.com', 'student')

        # 강사 통계
        inst_stats = self.client.get(
            '/dashboard/stats',
            headers={'Authorization': f'Bearer {inst_token}'}
        )
        self.assertEqual(inst_stats.status_code, 200)
        self.assertEqual(inst_stats.get_json()['role'], 'instructor')

        # 학생 통계
        student_stats = self.client.get(
            '/dashboard/stats',
            headers={'Authorization': f'Bearer {student_token}'}
        )
        self.assertEqual(student_stats.status_code, 200)
        self.assertEqual(student_stats.get_json()['role'], 'student')

    def test_admin_access_control(self):
        """관리자 API 접근 제어"""
        student_token = self._register_user('student@admin.com', 'student')
        admin_token = self._register_user('admin@test.com', 'admin')

        # 학생은 접근 불가
        student_res = self.client.get(
            '/api/network/admin/summary?period=2026-03',
            headers={'Authorization': f'Bearer {student_token}'}
        )
        self.assertEqual(student_res.status_code, 403)

        # 관리자는 접근 가능
        admin_res = self.client.get(
            '/api/network/admin/summary?period=2026-03',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        self.assertIn(admin_res.status_code, [200, 400])

    def _register_user(self, email, role, password='TestPass123'):
        """사용자 등록 및 로그인 헬퍼"""
        # 등록
        reg_res = self.client.post('/auth/register', json={
            'email': email,
            'password': password,
            'role': role
        })
        # app_jwt.py에서는 register가 201을 반환하고 message만 줌
        # 따라서 login으로 token을 얻어야 함
        if reg_res.status_code == 201:
            # app.py 방식 (register에서 token 반환)
            payload = reg_res.get_json()
            if 'access_token' in payload:
                return payload['access_token']
        
        # app_jwt.py 방식 (login으로 token 얻음)
        login_res = self.client.post('/auth/login', json={
            'email': email,
            'password': password
        })
        self.assertEqual(login_res.status_code, 200)
        return login_res.get_json()['access_token']


if __name__ == '__main__':
    unittest.main()
