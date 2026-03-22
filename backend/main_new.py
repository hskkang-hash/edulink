from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./edulink.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default='instructor')
    created_at = Column(DateTime, default=datetime.utcnow)

class Posting(Base):
    __tablename__ = 'postings'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    region = Column(String, nullable=False)
    rate = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True, index=True)
    posting_id = Column(Integer, ForeignKey('postings.id'), nullable=False)
    instructor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

TOKENS = {}

def get_current_user_id():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    return TOKENS.get(token)

@app.route('/')
def root():
    return jsonify({'message': 'EDULINK API is running'})

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'instructor')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    with engine.connect() as conn:
        existing = conn.execute('SELECT id FROM users WHERE email = :email', {'email': email}).fetchone()
        if existing:
            return jsonify({'error': 'Email already registered'}), 400
        conn.execute('INSERT INTO users (email, password, role, created_at) VALUES (:email, :password, :role, :created_at)', {'email': email, 'password': password, 'role': role, 'created_at': datetime.utcnow()})
        return jsonify({'message': 'registered'})

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    with engine.connect() as conn:
        row = conn.execute('SELECT id FROM users WHERE email = :email AND password = :password', {'email': email, 'password': password}).fetchone()
        if not row:
            return jsonify({'error': 'Invalid credentials'}), 401
        token = f'demo_token_{row[0]}'
        TOKENS[token] = row[0]
        return jsonify({'access_token': token, 'token_type': 'bearer'})

@app.route('/postings', methods=['GET'])
def list_postings():
    with engine.connect() as conn:
        rows = conn.execute('SELECT id, title, subject, region, rate FROM postings').fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/postings', methods=['POST'])
def create_posting():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    for key in ('title', 'subject', 'region', 'rate'):
        if key not in data:
            return jsonify({'error': f'{key} required'}), 400

    with engine.connect() as conn:
        conn.execute('INSERT INTO postings (title, subject, region, rate, created_at) VALUES (:title, :subject, :region, :rate, :created_at)', {
            'title': data['title'], 'subject': data['subject'], 'region': data['region'], 'rate': data['rate'], 'created_at': datetime.utcnow()
        })
        return jsonify({'message': 'Posting created'})

@app.route('/applications', methods=['POST'])
def create_application():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    posting_id = data.get('posting_id')
    if not posting_id:
        return jsonify({'error': 'posting_id required'}), 400

    with engine.connect() as conn:
        exists = conn.execute('SELECT id FROM postings WHERE id = :id', {'id': posting_id}).fetchone()
        if not exists:
            return jsonify({'error': 'Posting not found'}), 404
        conn.execute('INSERT INTO applications (posting_id, instructor_id, status, created_at) VALUES (:posting_id, :instructor_id, :status, :created_at)', {
            'posting_id': posting_id,
            'instructor_id': user_id,
            'status': 'pending',
            'created_at': datetime.utcnow()
        })
        return jsonify({'message': 'Application submitted'})

@app.route('/applications', methods=['GET'])
def list_applications():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        rows = conn.execute('SELECT id, posting_id, status FROM applications WHERE instructor_id = :instructor_id', {'instructor_id': user_id}).fetchall()
        return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
