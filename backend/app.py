from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
CORS(app)

# Simple SQLite database
engine = create_engine("sqlite:///./edulink.db", echo=True)

# Create tables
with engine.connect() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'instructor'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY,
            title TEXT,
            subject TEXT,
            region TEXT,
            rate INTEGER,
            owner_id INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            posting_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    """)

@app.route("/")
def root():
    return {"message": "EDULINK API is running"}

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "student")
    with engine.connect() as conn:
        try:
            conn.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, password, role))
            conn.commit()
            return {"message": "Registered", "access_token": "dummy_token", "user": {"id": 1, "email": email, "role": role}}
        except:
            return {"error": "Email already exists"}, 400

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    with engine.connect() as conn:
        result = conn.execute("SELECT id, role FROM users WHERE email = ? AND password = ?", (email, password))
        user = result.fetchone()
        if user:
            return {"access_token": "dummy_token", "token_type": "bearer", "user": {"id": user[0], "email": email, "role": user[1]}}
        return {"error": "Invalid credentials"}, 401

@app.route("/auth/me", methods=["GET"])
def get_me():
    # Dummy auth
    return {"id": 1, "email": "user@example.com", "role": "instructor"}

@app.route("/postings", methods=["GET"])
def get_postings():
    with engine.connect() as conn:
        result = conn.execute("SELECT id, title, subject, region, rate, owner_id FROM postings")
        postings = [dict(zip(result.keys(), row)) for row in result]
        return jsonify(postings)

@app.route("/postings", methods=["POST"])
def create_posting():
    data = request.get_json()
    title = data.get("title")
    subject = data.get("subject")
    region = data.get("region")
    rate = data.get("rate")
    owner_id = 1  # dummy
    with engine.connect() as conn:
        conn.execute("INSERT INTO postings (title, subject, region, rate, owner_id) VALUES (?, ?, ?, ?, ?)",
                    (title, subject, region, rate, owner_id))
        conn.commit()
        return {"message": "Posting created"}

@app.route("/postings/<int:id>", methods=["PUT"])
def update_posting(id):
    data = request.get_json()
    title = data.get("title")
    subject = data.get("subject")
    region = data.get("region")
    rate = data.get("rate")
    with engine.connect() as conn:
        conn.execute("UPDATE postings SET title=?, subject=?, region=?, rate=? WHERE id=? AND owner_id=?",
                    (title, subject, region, rate, id, 1))
        conn.commit()
        return {"message": "Updated"}

@app.route("/postings/<int:id>", methods=["DELETE"])
def delete_posting(id):
    with engine.connect() as conn:
        conn.execute("DELETE FROM postings WHERE id=? AND owner_id=?", (id, 1))
        conn.commit()
        return {"message": "Deleted"}

@app.route("/applications", methods=["GET"])
def get_applications():
    with engine.connect() as conn:
        result = conn.execute("SELECT id, posting_id, student_id, status FROM applications")
        applications = [dict(zip(result.keys(), row)) for row in result]
        return jsonify(applications)

@app.route("/applications", methods=["POST"])
def create_application():
    data = request.get_json()
    posting_id = data.get("posting_id")
    student_id = 1  # dummy
    with engine.connect() as conn:
        conn.execute("INSERT INTO applications (posting_id, student_id) VALUES (?, ?)", (posting_id, student_id))
        conn.commit()
        return {"message": "Applied"}

@app.route("/applications/<int:id>", methods=["PATCH"])
def update_application(id):
    data = request.get_json()
    status = data.get("status")
    with engine.connect() as conn:
        conn.execute("UPDATE applications SET status=? WHERE id=?", (status, id))
        conn.commit()
        return {"message": "Updated"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)