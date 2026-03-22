from flask import Flask, request, jsonify, g
from flask_cors import CORS
from sqlalchemy import create_engine, text
from itsdangerous import URLSafeSerializer, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

# Simple SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./edulink.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SECRET_KEY = os.getenv("SECRET_KEY", "edulink-secret-key")
token_serializer = URLSafeSerializer(SECRET_KEY, salt="auth-token")

ALLOWED_ROLES = {"student", "instructor", "admin"}
ALLOWED_APPLICATION_STATUSES = {"pending", "approved", "rejected"}


def make_token(user_payload):
    return token_serializer.dumps(user_payload)


def parse_token(token):
    return token_serializer.loads(token)


def _extract_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Missing bearer token"}), 401
        try:
            payload = parse_token(token)
        except BadSignature:
            return jsonify({"error": "Invalid token"}), 401
        g.current_user = payload
        return func(*args, **kwargs)

    return wrapper

# Create tables
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'instructor'
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY,
            title TEXT,
            subject TEXT,
            region TEXT,
            rate INTEGER,
            owner_id INTEGER
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            posting_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    """))
    conn.commit()

@app.route("/")
def root():
    return {"message": "EDULINK API is running"}

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "student").strip().lower()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if role not in ALLOWED_ROLES:
        return jsonify({"error": "invalid role"}), 400

    hashed_password = generate_password_hash(password)

    with engine.connect() as conn:
        try:
            conn.execute(
                text("INSERT INTO users (email, password, role) VALUES (:email, :password, :role)"),
                {"email": email, "password": hashed_password, "role": role},
            )
            conn.commit()
            user_id = conn.execute(
                text("SELECT id FROM users WHERE email=:email"),
                {"email": email},
            ).scalar_one()
            user_payload = {"id": user_id, "email": email, "role": role}
            return jsonify(
                {
                    "message": "Registered",
                    "access_token": make_token(user_payload),
                    "token_type": "bearer",
                    "user": user_payload,
                }
            ), 201
        except Exception:
            return jsonify({"error": "Email already exists"}), 400

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, email, password, role FROM users WHERE email=:email"),
            {"email": email},
        ).mappings().first()
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        user_payload = {"id": user["id"], "email": user["email"], "role": user["role"]}
        return jsonify(
            {
                "access_token": make_token(user_payload),
                "token_type": "bearer",
                "user": user_payload,
            }
        )

@app.route("/auth/me", methods=["GET"])
@auth_required
def get_me():
    return jsonify(g.current_user)

@app.route("/postings", methods=["GET"])
def get_postings():
    subject = (request.args.get("subject") or "").strip().lower()
    region = (request.args.get("region") or "").strip().lower()
    min_rate = request.args.get("min_rate", type=int)

    filters = []
    params = {}
    if subject:
        filters.append("LOWER(subject)=:subject")
        params["subject"] = subject
    if region:
        filters.append("LOWER(region) LIKE :region")
        params["region"] = f"%{region}%"
    if min_rate is not None:
        filters.append("rate >= :min_rate")
        params["min_rate"] = min_rate

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"SELECT id, title, subject, region, rate, owner_id FROM postings {where_clause} ORDER BY id DESC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        postings = [dict(row) for row in result.mappings()]
        return jsonify(postings)

@app.route("/postings", methods=["POST"])
@auth_required
def create_posting():
    if g.current_user["role"] not in {"instructor", "admin"}:
        return jsonify({"error": "Only instructor/admin can create postings"}), 403

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    subject = (data.get("subject") or "").strip().lower()
    region = (data.get("region") or "").strip()
    rate = data.get("rate")
    owner_id = g.current_user["id"]

    if not title or not subject or not region or rate is None:
        return jsonify({"error": "title, subject, region, rate are required"}), 400

    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO postings (title, subject, region, rate, owner_id) "
                "VALUES (:title, :subject, :region, :rate, :owner_id)"
            ),
            {
                "title": title,
                "subject": subject,
                "region": region,
                "rate": rate,
                "owner_id": owner_id,
            },
        )
        conn.commit()
        posting_id = conn.execute(text("SELECT last_insert_rowid() ")).scalar_one()
        return jsonify({"message": "Posting created", "id": posting_id}), 201

@app.route("/postings/<int:id>", methods=["PUT"])
@auth_required
def update_posting(id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    subject = (data.get("subject") or "").strip().lower()
    region = (data.get("region") or "").strip()
    rate = data.get("rate")

    if not title or not subject or not region or rate is None:
        return jsonify({"error": "title, subject, region, rate are required"}), 400

    owner_id = g.current_user["id"]
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "UPDATE postings SET title=:title, subject=:subject, region=:region, rate=:rate "
                "WHERE id=:id AND owner_id=:owner_id"
            ),
            {
                "title": title,
                "subject": subject,
                "region": region,
                "rate": rate,
                "id": id,
                "owner_id": owner_id,
            },
        )
        conn.commit()
        if result.rowcount == 0:
            return jsonify({"error": "Posting not found or forbidden"}), 404
        return jsonify({"message": "Updated"})

@app.route("/postings/<int:id>", methods=["DELETE"])
@auth_required
def delete_posting(id):
    owner_id = g.current_user["id"]
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM postings WHERE id=:id AND owner_id=:owner_id"),
            {"id": id, "owner_id": owner_id},
        )
        conn.commit()
        if result.rowcount == 0:
            return jsonify({"error": "Posting not found or forbidden"}), 404
        return jsonify({"message": "Deleted"})

@app.route("/applications", methods=["GET"])
@auth_required
def get_applications():
    user = g.current_user
    status = (request.args.get("status") or "").strip().lower()
    if status and status not in ALLOWED_APPLICATION_STATUSES:
        return jsonify({"error": "Invalid status filter"}), 400

    with engine.connect() as conn:
        if user["role"] in {"instructor", "admin"}:
            query = (
                "SELECT a.id, a.posting_id, a.student_id, a.status "
                "FROM applications a JOIN postings p ON p.id = a.posting_id "
                "WHERE p.owner_id = :user_id"
            )
            params = {"user_id": user["id"]}
        else:
            query = "SELECT id, posting_id, student_id, status FROM applications WHERE student_id = :user_id"
            params = {"user_id": user["id"]}

        if status:
            if user["role"] in {"instructor", "admin"}:
                query += " AND a.status = :status"
            else:
                query += " AND status = :status"
            params["status"] = status

        if user["role"] in {"instructor", "admin"}:
            query += " ORDER BY a.id DESC"
        else:
            query += " ORDER BY id DESC"
        result = conn.execute(text(query), params)
        applications = [dict(row) for row in result.mappings()]
        return jsonify(applications)

@app.route("/applications", methods=["POST"])
@auth_required
def create_application():
    if g.current_user["role"] != "student":
        return jsonify({"error": "Only student can apply"}), 403

    data = request.get_json(silent=True) or {}
    posting_id = data.get("posting_id")
    if posting_id is None:
        return jsonify({"error": "posting_id is required"}), 400

    student_id = g.current_user["id"]

    with engine.connect() as conn:
        posting = conn.execute(
            text("SELECT id FROM postings WHERE id=:id"),
            {"id": posting_id},
        ).first()
        if not posting:
            return jsonify({"error": "Posting not found"}), 404

        exists = conn.execute(
            text("SELECT id FROM applications WHERE posting_id=:posting_id AND student_id=:student_id"),
            {"posting_id": posting_id, "student_id": student_id},
        ).first()
        if exists:
            return jsonify({"error": "Already applied"}), 409

        conn.execute(
            text("INSERT INTO applications (posting_id, student_id, status) VALUES (:posting_id, :student_id, 'pending')"),
            {"posting_id": posting_id, "student_id": student_id},
        )
        conn.commit()
        application_id = conn.execute(text("SELECT last_insert_rowid() ")).scalar_one()
        return jsonify({"message": "Applied", "id": application_id}), 201

@app.route("/applications/<int:id>", methods=["PATCH"])
@auth_required
def update_application(id):
    if g.current_user["role"] not in {"instructor", "admin"}:
        return jsonify({"error": "Only instructor/admin can update application status"}), 403

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()
    if status not in {"approved", "rejected"}:
        return jsonify({"error": "status must be approved or rejected"}), 400

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "UPDATE applications SET status=:status WHERE id=:id AND posting_id IN ("
                "SELECT id FROM postings WHERE owner_id=:owner_id)"
            ),
            {"status": status, "id": id, "owner_id": g.current_user["id"]},
        )
        conn.commit()
        if result.rowcount == 0:
            return jsonify({"error": "Application not found or forbidden"}), 404
        return jsonify({"message": "Updated"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)