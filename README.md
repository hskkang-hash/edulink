# EDULINK MVP

## Overview
EDULINK is a tutoring-matching MVP where instructors create postings and students apply.
This repository is currently implemented as a Flask + SQLite app with a plain HTML/JS frontend.

## Current Stack
- Backend: Flask
- Database: SQLite (`backend/edulink.db`)
- Auth token: `itsdangerous` signed token (Bearer)
- Frontend: vanilla HTML/CSS/JS (served by backend root)

## Quick Start

### 1) Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2) Run server
```bash
cd backend
python app_jwt.py
```

### 3) Open app
Use:
```text
http://localhost:8000
```

The backend serves `frontend/index.html` at `/`.

## Main Features (Implemented)
- Register / Login / Logout
- Role-aware UI (instructor vs student)
- Instructor posting CRUD
- Student application submit
- Instructor application approve/reject
- "My postings only" toggle for instructors
- Enter-key submit on register/login forms
- Posting creation success toast + auto-scroll to postings

## API Endpoints

### Health / Root
- `GET /` frontend page (or API message fallback)
- `GET /health` API health check

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Postings
- `GET /postings`
- `POST /postings` (auth)
- `PUT /postings/<posting_id>` (owner only)
- `DELETE /postings/<posting_id>` (owner only)

### Applications
- `GET /applications` (auth, role-based list)
- `POST /applications` (auth)
- `PATCH /applications/<application_id>` (instructor only)

## Notes
- Existing SQLite schemas are auto-migrated for missing columns on startup.
- For local development, always use `http://` on localhost.

## Suggested Next Steps
- Add password hashing migration for legacy plain-text users
- Add instructor dashboard metrics (counts by status)
- Add test cases for auth/role permissions
- Add Docker-based local run profile