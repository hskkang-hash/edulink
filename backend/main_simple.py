from fastapi import FastAPI, Form
from sqlalchemy import create_engine, text

app = FastAPI()

# Simple SQLite database
engine = create_engine("sqlite:///./edulink.db", echo=True)

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
            rate INTEGER
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            posting_id INTEGER,
            instructor_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    """))
    conn.commit()

@app.get("/")
def root():
    return {"message": "EDULINK API is running"}

@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...)):
    if email == "demo@example.com" and password == "password":
        return {"access_token": "demo_token", "token_type": "bearer"}
    return {"error": "Invalid credentials"}

@app.get("/postings")
def get_postings():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM postings"))
        postings = [dict(row) for row in result.mappings()]
        return postings

@app.post("/postings")
def create_posting(title: str = Form(...), subject: str = Form(...), region: str = Form(...), rate: int = Form(...)):
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO postings (title, subject, region, rate) VALUES (?, ?, ?, ?)"),
                    (title, subject, region, rate))
        conn.commit()
        return {"message": "Posting created"}

@app.post("/applications")
def apply_to_posting(posting_id: int = Form(...)):
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO applications (posting_id, instructor_id) VALUES (?, ?)"),
                    (posting_id, 1))
        conn.commit()
        return {"message": "Application submitted"}

@app.get("/applications")
def get_applications():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM applications WHERE instructor_id = ?"), (1,))
        applications = [dict(row) for row in result.mappings()]
        return applications