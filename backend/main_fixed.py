from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('SECRET_KEY', 'edulink-secret-key')
serializer = URLSafeTimedSerializer(SECRET_KEY)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./edulink.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False}, echo=False)
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

def create_token(user_id):
    token = serializer.dumps({'user_id': user_id})
    TOKENS[token] = user_id
    return token

def verify_token(token):
    if token in TOKENS:
        return TOKENS[token]
    try:
        data = serializer.loads(token, max_age=60*60*24)
        return data.get('user_id')
    except (BadSignature, SignatureExpired):
        return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_auth(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing Authorization header'}), 401

        token = auth_header.split(' ', 1)[1]
        user_id = verify_token(token)
        if user_id is None:
            return jsonify({'error': 'Invalid or expired token'}), 401

        request.user_id = user_id
        return func(*args, **kwargs)

    return wrapper


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

    db = next(get_db())
    if db.query(User).filter(User.email == email).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(email=email, password=generate_password_hash(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return jsonify({'id': user.id, 'email': user.email, 'role': user.role}), 201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if user is None or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token(user.id)
    return jsonify({'access_token': token, 'token_type': 'bearer'})


@app.route('/auth/me', methods=['GET'])
@require_auth
def me():
    db = next(get_db())
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'email': user.email, 'role': user.role})


@app.route('/postings', methods=['GET'])
def get_postings():
    db = next(get_db())
    postings = db.query(Posting).all()
    return jsonify([{'id': p.id, 'title': p.title, 'subject': p.subject, 'region': p.region, 'rate': p.rate} for p in postings])


@app.route('/postings', methods=['POST'])
@require_auth
def create_posting():
    data = request.get_json() or {}
    for field in ['title', 'subject', 'region', 'rate']:
        if field not in data:
            return jsonify({'error': f'{field} required'}), 400

    db = next(get_db())
    posting = Posting(title=data['title'], subject=data['subject'], region=data['region'], rate=data['rate'])
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return jsonify({'id': posting.id, 'title': posting.title, 'subject': posting.subject, 'region': posting.region, 'rate': posting.rate}), 201


@app.route('/applications', methods=['GET'])
@require_auth
def get_applications():
    db = next(get_db())
    applications = db.query(Application).filter(Application.instructor_id == request.user_id).all()
    return jsonify([{'id': a.id, 'posting_id': a.posting_id, 'status': a.status} for a in applications])


@app.route('/applications', methods=['POST'])
@require_auth
def create_application():
    data = request.get_json() or {}
    posting_id = data.get('posting_id')
    if posting_id is None:
        return jsonify({'error': 'posting_id required'}), 400

    db = next(get_db())
    if not db.query(Posting).filter(Posting.id == posting_id).first():
        return jsonify({'error': 'Posting not found'}), 404

    application = Application(posting_id=posting_id, instructor_id=request.user_id, status='pending')
    db.add(application)
    db.commit()
    db.refresh(application)
    return jsonify({'id': application.id, 'posting_id': application.posting_id, 'status': application.status}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
