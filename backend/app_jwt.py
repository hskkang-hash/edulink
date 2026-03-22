from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

engine = create_engine('sqlite:///./edulink.db', echo=False)

# DB init
with engine.connect() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'instructor',
            organization TEXT,
            created_at TEXT
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS postings (
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
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    '''))

    posting_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(postings)')).fetchall()]
    if 'owner_id' not in posting_cols:
        conn.execute(text('ALTER TABLE postings ADD COLUMN owner_id INTEGER'))
    if 'created_at' not in posting_cols:
        conn.execute(text('ALTER TABLE postings ADD COLUMN created_at TEXT'))

    user_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(users)')).fetchall()]
    if 'organization' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN organization TEXT'))
    if 'created_at' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN created_at TEXT'))

    app_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(applications)')).fetchall()]
    if 'student_id' not in app_cols and 'instructor_id' in app_cols:
        conn.execute(text('ALTER TABLE applications ADD COLUMN student_id INTEGER'))
    if 'created_at' not in app_cols:
        conn.execute(text('ALTER TABLE applications ADD COLUMN created_at TEXT'))

# helper

def create_token(payload):
    return serializer.dumps(payload)


def verify_token(token):
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24)
        return data
    except (BadSignature, SignatureExpired):
        return None


@app.route('/')
def root():
    frontend_dir = Path(__file__).resolve().parent.parent / 'frontend'
    index_file = frontend_dir / 'index.html'
    if index_file.exists():
        return send_from_directory(str(frontend_dir), 'index.html')
    return jsonify({'message': 'EDULINK API is running'})


@app.route('/health')
def health():
    return jsonify({'message': 'EDULINK API is running'})


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email/password required'}), 400

    with engine.begin() as conn:
        existing = conn.execute(text('SELECT id FROM users WHERE email = :email'), {'email': data['email']}).fetchone()
        if existing:
            return jsonify({'error': 'Email already registered'}), 400
        conn.execute(text('INSERT INTO users (email, password, role, organization, created_at) VALUES (:email,:password,:role,:org,:created_at)'),
                     {'email': data['email'], 'password': data['password'], 'role': data.get('role', 'instructor'), 'org': data.get('organization', ''), 'created_at': datetime.utcnow().isoformat()})

    return jsonify({'message': 'registered'}), 201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email/password required'}), 400

    with engine.connect() as conn:
        user = conn.execute(
            text('SELECT id,email,role FROM users WHERE email = :email AND password = :password'),
            {'email': data['email'], 'password': data['password']}
        ).mappings().first()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token({'user_id': user['id'], 'email': user['email'], 'role': user['role']})
    return jsonify({'access_token': token, 'token_type': 'bearer', 'user': {'id': user['id'], 'email': user['email'], 'role': user['role']}})


def get_current_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    return verify_token(token)


@app.route('/auth/me', methods=['GET'])
def auth_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        row = conn.execute(text('SELECT id,email,role FROM users WHERE id = :id'), {'id': user['user_id']}).mappings().first()
        if not row:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'id': row['id'], 'email': row['email'], 'role': row['role']})


@app.route('/postings', methods=['GET'])
def get_postings():
    with engine.connect() as conn:
        result = conn.execute(text('SELECT id, title, subject, region, rate, created_at, owner_id FROM postings')).mappings().all()
        return jsonify([dict(row) for row in result])


@app.route('/postings', methods=['POST'])
def create_posting():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    for key in ('title', 'subject', 'region', 'rate'):
        if key not in data:
            return jsonify({'error': f'{key} required'}), 400

    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO postings (title, subject, region, rate, created_at, owner_id) VALUES (:title,:subject,:region,:rate,:created_at,:owner_id)'),
            {
                'title': data['title'],
                'subject': data['subject'],
                'region': data['region'],
                'rate': data['rate'],
                'created_at': datetime.utcnow().isoformat(),
                'owner_id': user['user_id']
            }
        )
    return jsonify({'message': 'Posting created'}), 201


@app.route('/postings/<int:posting_id>', methods=['PUT'])
def update_posting(posting_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    with engine.begin() as conn:
        posting = conn.execute(
            text('SELECT id FROM postings WHERE id = :id AND owner_id = :owner_id'),
            {'id': posting_id, 'owner_id': user['user_id']}
        ).first()
        if not posting:
            return jsonify({'error': 'Posting not found or not owned'}), 404

        conn.execute(
            text('UPDATE postings SET title=:title, subject=:subject, region=:region, rate=:rate WHERE id=:id'),
            {
                'title': data.get('title', ''),
                'subject': data.get('subject', ''),
                'region': data.get('region', ''),
                'rate': data.get('rate', 0),
                'id': posting_id
            }
        )

    return jsonify({'message': 'Posting updated'})


@app.route('/postings/<int:posting_id>', methods=['DELETE'])
def delete_posting(posting_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.begin() as conn:
        result = conn.execute(
            text('DELETE FROM postings WHERE id = :id AND owner_id = :owner_id'),
            {'id': posting_id, 'owner_id': user['user_id']}
        )
        if result.rowcount == 0:
            return jsonify({'error': 'Posting not found or not owned'}), 404

    return jsonify({'message': 'Posting deleted'})


@app.route('/applications', methods=['POST'])
def apply_posting():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if 'posting_id' not in data:
        return jsonify({'error': 'posting_id required'}), 400

    with engine.begin() as conn:
        existing = conn.execute(
            text('SELECT id FROM applications WHERE posting_id = :posting_id AND student_id = :student_id'),
            {'posting_id': data['posting_id'], 'student_id': user['user_id']}
        ).first()
        if existing:
            return jsonify({'error': 'Already applied'}), 400

        conn.execute(
            text('INSERT INTO applications (posting_id, student_id, status, created_at) VALUES (:p,:s,:status,:c)'),
            {'p': data['posting_id'], 's': user['user_id'], 'status': data.get('status', 'pending'), 'c': datetime.utcnow().isoformat()}
        )
    return jsonify({'message': 'Applied'}), 201


@app.route('/applications', methods=['GET'])
def get_applications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        if user.get('role') == 'instructor':
            rows = conn.execute(
                text('''
                    SELECT a.id, a.posting_id, a.student_id, a.status, a.created_at
                    FROM applications a
                    JOIN postings p ON p.id = a.posting_id
                    WHERE p.owner_id = :owner_id
                    ORDER BY a.id DESC
                '''),
                {'owner_id': user['user_id']}
            ).mappings().all()
        else:
            rows = conn.execute(
                text('SELECT id, posting_id, student_id, status, created_at FROM applications WHERE student_id = :student_id ORDER BY id DESC'),
                {'student_id': user['user_id']}
            ).mappings().all()
        return jsonify([dict(row) for row in rows])


@app.route('/applications/<int:application_id>', methods=['PATCH'])
def update_application(application_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if user.get('role') != 'instructor':
        return jsonify({'error': 'Only instructors can update applications'}), 403

    data = request.get_json() or {}
    status = data.get('status')
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    with engine.begin() as conn:
        row = conn.execute(
            text('''
                SELECT a.id
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                WHERE a.id = :application_id AND p.owner_id = :owner_id
            '''),
            {'application_id': application_id, 'owner_id': user['user_id']}
        ).first()
        if not row:
            return jsonify({'error': 'Application not found or not owned'}), 404

        conn.execute(
            text('UPDATE applications SET status = :status WHERE id = :application_id'),
            {'status': status, 'application_id': application_id}
        )

    return jsonify({'message': 'Application updated'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
