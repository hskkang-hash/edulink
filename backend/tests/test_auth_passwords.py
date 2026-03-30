import unittest

from sqlalchemy import create_engine, text

import app_jwt


class AuthPasswordFlowTest(unittest.TestCase):
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
                CREATE TABLE social_identities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    provider TEXT,
                    provider_user_id TEXT,
                    provider_email TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(provider, provider_user_id)
                )
            '''))

        self.original_engine = app_jwt.engine
        self.original_social_demo_mode = app_jwt.app.config.get('SOCIAL_LOGIN_DEMO_MODE')
        app_jwt.engine = self.engine
        self.client = app_jwt.app.test_client()

    def tearDown(self):
        app_jwt.engine = self.original_engine
        app_jwt.app.config['SOCIAL_LOGIN_DEMO_MODE'] = self.original_social_demo_mode

    def test_register_hashes_password(self):
        response = self.client.post('/auth/register', json={
            'email': 'hash@test.com',
            'password': 'Secure123',
            'role': 'student'
        })
        self.assertEqual(response.status_code, 201)

        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT password FROM users WHERE email = :email'), {'email': 'hash@test.com'}).mappings().first()

        self.assertIsNotNone(row)
        self.assertTrue(row['password'].startswith('scrypt:') or row['password'].startswith('pbkdf2:'))

    def test_register_rejects_weak_password(self):
        response = self.client.post('/auth/register', json={
            'email': 'weak@test.com',
            'password': 'password',
            'role': 'student'
        })
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn('password must include at least one number', payload.get('error', ''))

    def test_login_migrates_legacy_plaintext_password(self):
        with self.engine.begin() as conn:
            conn.execute(text('''
                INSERT INTO users (email, password, role, organization, created_at)
                VALUES (:email, :password, :role, :organization, :created_at)
            '''), {
                'email': 'legacy@test.com',
                'password': 'Legacy123',
                'role': 'student',
                'organization': '',
                'created_at': '2026-03-22T00:00:00'
            })

        response = self.client.post('/auth/login', json={
            'email': 'legacy@test.com',
            'password': 'Legacy123'
        })
        self.assertEqual(response.status_code, 200)

        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT password FROM users WHERE email = :email'), {'email': 'legacy@test.com'}).mappings().first()

        self.assertIsNotNone(row)
        self.assertNotEqual(row['password'], 'Legacy123')
        self.assertTrue(row['password'].startswith('scrypt:') or row['password'].startswith('pbkdf2:'))

    def test_password_change_requires_current_password(self):
        self.client.post('/auth/register', json={
            'email': 'change@test.com',
            'password': 'Secure123',
            'role': 'student'
        })
        login = self.client.post('/auth/login', json={'email': 'change@test.com', 'password': 'Secure123'})
        token = login.get_json()['access_token']

        response = self.client.post('/auth/password/change', json={
            'current_password': 'Wrong123',
            'new_password': 'NewPass123'
        }, headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 400)

    def test_password_change_updates_login_password(self):
        self.client.post('/auth/register', json={
            'email': 'change-ok@test.com',
            'password': 'Secure123',
            'role': 'student'
        })
        login = self.client.post('/auth/login', json={'email': 'change-ok@test.com', 'password': 'Secure123'})
        token = login.get_json()['access_token']

        response = self.client.post('/auth/password/change', json={
            'current_password': 'Secure123',
            'new_password': 'NewPass123'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)

        old_login = self.client.post('/auth/login', json={'email': 'change-ok@test.com', 'password': 'Secure123'})
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post('/auth/login', json={'email': 'change-ok@test.com', 'password': 'NewPass123'})
        self.assertEqual(new_login.status_code, 200)

    def test_password_reset_confirm_flow(self):
        self.client.post('/auth/register', json={
            'email': 'reset@test.com',
            'password': 'Secure123',
            'role': 'student'
        })

        request_response = self.client.post('/auth/password/reset/request', json={'email': 'reset@test.com'})
        self.assertEqual(request_response.status_code, 200)
        request_payload = request_response.get_json()
        self.assertEqual(request_payload.get('delivery'), 'mock-log')
        self.assertIsNone(request_payload.get('reset_token'))

        with self.engine.connect() as conn:
            row = conn.execute(
                text('SELECT id, email FROM users WHERE email = :email'),
                {'email': 'reset@test.com'}
            ).mappings().first()

        self.assertIsNotNone(row)
        reset_token = app_jwt.create_password_reset_token(row['id'], row['email'])

        confirm_response = self.client.post('/auth/password/reset/confirm', json={
            'token': reset_token,
            'new_password': 'Reset1234'
        })
        self.assertEqual(confirm_response.status_code, 200)

        login_old = self.client.post('/auth/login', json={'email': 'reset@test.com', 'password': 'Secure123'})
        self.assertEqual(login_old.status_code, 401)

        login_new = self.client.post('/auth/login', json={'email': 'reset@test.com', 'password': 'Reset1234'})
        self.assertEqual(login_new.status_code, 200)

    def test_social_login_creates_user_for_google(self):
        response = self.client.post('/auth/social-login', json={
            'provider': 'google',
            'access_token': 'google-test-token-123456',
            'provider_user_id': 'g-1001',
            'email': 'social.google@test.com',
            'role': 'instructor'
        })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload.get('created'))
        self.assertEqual(payload.get('provider'), 'google')

    def test_social_login_reuses_existing_identity(self):
        first = self.client.post('/auth/social-login', json={
            'provider': 'kakao',
            'access_token': 'kakao-test-token-123456',
            'provider_user_id': 'k-1001',
            'email': 'social.kakao@test.com',
            'role': 'school'
        })
        self.assertEqual(first.status_code, 200)

        second = self.client.post('/auth/social-login', json={
            'provider': 'kakao',
            'access_token': 'kakao-test-token-654321',
            'provider_user_id': 'k-1001',
            'email': 'social.kakao@test.com',
            'role': 'school'
        })
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.get_json().get('created'))

    def test_social_login_blocks_privileged_role(self):
        response = self.client.post('/auth/social-login', json={
            'provider': 'google',
            'access_token': 'google-test-token-123456',
            'provider_user_id': 'g-admin',
            'email': 'social.admin@test.com',
            'role': 'admin'
        })
        self.assertEqual(response.status_code, 403)

    def test_social_login_rejects_short_token_when_not_demo_mode(self):
        app_jwt.app.config['SOCIAL_LOGIN_DEMO_MODE'] = False
        response = self.client.post('/auth/social-login', json={
            'provider': 'google',
            'access_token': 'short-token',
            'provider_user_id': 'g-1100',
            'email': 'strict.social@test.com',
            'role': 'instructor'
        })
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
