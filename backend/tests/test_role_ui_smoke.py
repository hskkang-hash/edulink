import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

import app_jwt


class RoleBasedUiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', echo=False)
        with self.engine.begin() as conn:
            conn.execute(text('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT,
                    role TEXT DEFAULT 'instructor',
                    organization TEXT,
                    created_at TEXT
                )
            '''))
            conn.execute(text('''
                CREATE TABLE postings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    subject TEXT,
                    region TEXT,
                    rate INTEGER,
                    created_at TEXT,
                    owner_id INTEGER
                )
            '''))
            conn.execute(text('''
                CREATE TABLE applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    posting_id INTEGER,
                    student_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                )
            '''))
            conn.execute(text('''
                CREATE TABLE network_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_user_id INTEGER,
                    base_price INTEGER,
                    pv INTEGER,
                    bv INTEGER,
                    created_at TEXT
                )
            '''))
            conn.execute(text('''
                CREATE TABLE network_bonus_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    beneficiary_user_id INTEGER,
                    amount_paid INTEGER,
                    scale_factor REAL DEFAULT 1.0,
                    created_at TEXT
                )
            '''))

        self.original_engine = app_jwt.engine
        app_jwt.engine = self.engine
        self.client = app_jwt.app.test_client()

    def tearDown(self):
        app_jwt.engine = self.original_engine

    def _register_and_login(self, email, role):
        register_response = self.client.post('/auth/register', json={
            'email': email,
            'password': 'Secure123',
            'role': role,
            'organization': 'UI-Test'
        })
        self.assertEqual(register_response.status_code, 201)

        login_response = self.client.post('/auth/login', json={
            'email': email,
            'password': 'Secure123'
        })
        self.assertEqual(login_response.status_code, 200)
        token = login_response.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}

    def _seed_posting(self, owner_id, title='Linear Algebra', subject='math', region='Seoul', rate=50000):
        with self.engine.begin() as conn:
            conn.execute(
                text('''
                    INSERT INTO postings (title, subject, region, rate, created_at, owner_id)
                    VALUES (:title, :subject, :region, :rate, :created_at, :owner_id)
                '''),
                {
                    'title': title,
                    'subject': subject,
                    'region': region,
                    'rate': rate,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'owner_id': owner_id,
                }
            )

    def _seed_application(self, posting_id, student_id, status):
        with self.engine.begin() as conn:
            conn.execute(
                text('''
                    INSERT INTO applications (posting_id, student_id, status, created_at)
                    VALUES (:posting_id, :student_id, :status, :created_at)
                '''),
                {
                    'posting_id': posting_id,
                    'student_id': student_id,
                    'status': status,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                }
            )

    def test_auth_me_reflects_logged_in_role(self):
        headers = self._register_and_login('ui-instructor@test.com', 'instructor')

        me_response = self.client.get('/auth/me', headers=headers)
        self.assertEqual(me_response.status_code, 200)
        payload = me_response.get_json()
        self.assertEqual(payload.get('email'), 'ui-instructor@test.com')
        self.assertEqual(payload.get('role'), 'instructor')

    def test_dashboard_stats_changes_by_role(self):
        instructor_headers = self._register_and_login('stats-instructor@test.com', 'instructor')
        student_headers = self._register_and_login('stats-student@test.com', 'student')

        instructor_stats = self.client.get('/dashboard/stats', headers=instructor_headers)
        student_stats = self.client.get('/dashboard/stats', headers=student_headers)

        self.assertEqual(instructor_stats.status_code, 200)
        self.assertEqual(student_stats.status_code, 200)

        instructor_payload = instructor_stats.get_json()
        student_payload = student_stats.get_json()

        self.assertEqual(instructor_payload.get('role'), 'instructor')
        self.assertIn('postings_count', instructor_payload)

        self.assertEqual(student_payload.get('role'), 'student')
        self.assertNotIn('postings_count', student_payload)

    def test_admin_insights_forbidden_for_student(self):
        student_headers = self._register_and_login('ui-student@test.com', 'student')

        response = self.client.get(
            '/api/network/admin/summary?period=2026-03',
            headers=student_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_student_application_status_filter_returns_only_requested_status(self):
        student_headers = self._register_and_login('filter-student@test.com', 'student')
        self._register_and_login('filter-instructor@test.com', 'instructor')

        self._seed_posting(owner_id=2)
        self._seed_application(posting_id=1, student_id=1, status='pending')
        self._seed_application(posting_id=1, student_id=1, status='approved')

        response = self.client.get('/applications?status=pending', headers=student_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0].get('status'), 'pending')
        self.assertEqual(payload[0].get('student_id'), 1)

    def test_instructor_application_status_filter_scopes_to_owned_postings(self):
        instructor_headers = self._register_and_login('owned-instructor@test.com', 'instructor')
        other_instructor_headers = self._register_and_login('other-instructor@test.com', 'instructor')
        self._register_and_login('owned-student@test.com', 'student')

        self._seed_posting(owner_id=1, title='Owned Posting')
        self._seed_posting(owner_id=2, title='Other Posting')
        self._seed_application(posting_id=1, student_id=3, status='rejected')
        self._seed_application(posting_id=2, student_id=3, status='rejected')

        response = self.client.get('/applications?status=rejected', headers=instructor_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0].get('posting_title'), 'Owned Posting')

        other_response = self.client.get('/applications?status=rejected', headers=other_instructor_headers)
        self.assertEqual(other_response.status_code, 200)
        self.assertEqual(len(other_response.get_json()), 1)

    def test_invalid_application_status_filter_returns_bad_request(self):
        headers = self._register_and_login('invalid-filter@test.com', 'student')

        response = self.client.get('/applications?status=archived', headers=headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid status filter', response.get_json().get('error', ''))

    def test_applications_search_query_filters_by_posting_title(self):
        student_headers = self._register_and_login('search-student@test.com', 'student')
        self._register_and_login('search-instructor@test.com', 'instructor')

        self._seed_posting(owner_id=2, title='Algebra Crash Course')
        self._seed_posting(owner_id=2, title='English Essay Lab')
        self._seed_application(posting_id=1, student_id=1, status='pending')
        self._seed_application(posting_id=2, student_id=1, status='pending')

        response = self.client.get('/applications?q=algebra', headers=student_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0].get('posting_title'), 'Algebra Crash Course')

    def test_instructor_applications_sort_status_prioritizes_pending(self):
        instructor_headers = self._register_and_login('sort-instructor@test.com', 'instructor')
        self._register_and_login('sort-student@test.com', 'student')

        self._seed_posting(owner_id=1, title='Sorting Posting')
        self._seed_application(posting_id=1, student_id=2, status='rejected')
        self._seed_application(posting_id=1, student_id=2, status='approved')
        self._seed_application(posting_id=1, student_id=2, status='pending')

        response = self.client.get('/applications?sort=status', headers=instructor_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload), 3)
        self.assertEqual(payload[0].get('status'), 'pending')

    def test_instructor_applications_include_applicant_email_and_support_email_search(self):
        instructor_headers = self._register_and_login('detail-instructor@test.com', 'instructor')
        self._register_and_login('detail-student@test.com', 'student')

        self._seed_posting(owner_id=1, title='Detail Posting')
        self._seed_application(posting_id=1, student_id=2, status='pending')

        full_response = self.client.get('/applications', headers=instructor_headers)
        self.assertEqual(full_response.status_code, 200)
        full_payload = full_response.get_json()
        self.assertEqual(full_payload[0].get('student_email'), 'detail-student@test.com')

        filtered_response = self.client.get('/applications?q=detail-student@test.com', headers=instructor_headers)
        self.assertEqual(filtered_response.status_code, 200)
        filtered_payload = filtered_response.get_json()
        self.assertEqual(len(filtered_payload), 1)
        self.assertEqual(filtered_payload[0].get('student_email'), 'detail-student@test.com')

    def test_instructor_can_view_applicant_summary_for_owned_postings(self):
        instructor_headers = self._register_and_login('summary-instructor@test.com', 'instructor')
        self._register_and_login('summary-student@test.com', 'student')

        self._seed_posting(owner_id=1, title='Summary Posting')
        self._seed_application(posting_id=1, student_id=2, status='pending')
        self._seed_application(posting_id=1, student_id=2, status='approved')

        response = self.client.get('/applications/applicants/2/summary', headers=instructor_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload.get('student_email'), 'summary-student@test.com')
        self.assertEqual(payload.get('total_applications_to_you'), 2)
        self.assertEqual(payload.get('status_counts', {}).get('pending'), 1)
        self.assertEqual(payload.get('status_counts', {}).get('approved'), 1)

    def test_instructor_applicant_summary_is_scoped_to_owned_postings(self):
        instructor_headers = self._register_and_login('scope-instructor@test.com', 'instructor')
        self._register_and_login('scope-other-instructor@test.com', 'instructor')
        self._register_and_login('scope-student@test.com', 'student')

        self._seed_posting(owner_id=2, title='Other Owner Posting')
        self._seed_application(posting_id=1, student_id=3, status='pending')

        response = self.client.get('/applications/applicants/3/summary', headers=instructor_headers)

        self.assertEqual(response.status_code, 404)
        self.assertIn('Applicant not found in your postings', response.get_json().get('error', ''))

    def test_student_cannot_view_applicant_summary(self):
        student_headers = self._register_and_login('summary-student-role@test.com', 'student')

        response = self.client.get('/applications/applicants/1/summary', headers=student_headers)

        self.assertEqual(response.status_code, 403)
        self.assertIn('Only instructors can view applicant summaries', response.get_json().get('error', ''))

    def test_invalid_applications_sort_returns_bad_request(self):
        headers = self._register_and_login('invalid-sort@test.com', 'student')

        response = self.client.get('/applications?sort=priority', headers=headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid sort option', response.get_json().get('error', ''))

    def test_admin_insights_allowed_for_admin_and_super_admin(self):
        admin_headers = self._register_and_login('ui-admin@test.com', 'admin')
        super_admin_headers = self._register_and_login('ui-super@test.com', 'super_admin')

        now_iso = datetime.now(timezone.utc).isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text('''
                    INSERT INTO network_sales (seller_user_id, base_price, pv, bv, created_at)
                    VALUES (:seller_user_id, :base_price, :pv, :bv, :created_at)
                '''),
                {
                    'seller_user_id': 1,
                    'base_price': 100000,
                    'pv': 100,
                    'bv': 60,
                    'created_at': now_iso,
                }
            )
            conn.execute(
                text('''
                    INSERT INTO network_bonus_allocations (sale_id, beneficiary_user_id, amount_paid, scale_factor, created_at)
                    VALUES (:sale_id, :beneficiary_user_id, :amount_paid, :scale_factor, :created_at)
                '''),
                {
                    'sale_id': 1,
                    'beneficiary_user_id': 1,
                    'amount_paid': 15000,
                    'scale_factor': 1.0,
                    'created_at': now_iso,
                }
            )

        admin_response = self.client.get(
            '/api/network/admin/summary?period=2026-03',
            headers=admin_headers
        )
        super_admin_response = self.client.get(
            '/api/network/admin/summary?period=2026-03',
            headers=super_admin_headers
        )

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(super_admin_response.status_code, 200)

        self.assertEqual(admin_response.get_json().get('period'), '2026-03')
        self.assertEqual(super_admin_response.get_json().get('period'), '2026-03')


if __name__ == '__main__':
    unittest.main()
