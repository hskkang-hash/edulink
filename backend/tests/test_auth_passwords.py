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

        self.original_engine = app_jwt.engine
        app_jwt.engine = self.engine
        self.client = app_jwt.app.test_client()

    def tearDown(self):
        app_jwt.engine = self.original_engine

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


if __name__ == '__main__':
    unittest.main()
