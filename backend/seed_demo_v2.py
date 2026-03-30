from datetime import datetime, timedelta, timezone
import argparse
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash


PASSWORD = "DemoPass123!"
DEMO_PASSWORD_HASH = generate_password_hash(PASSWORD)
TOTAL_USERS = 1000
INSTRUCTOR_COUNT = 10
SCHOOL_COUNT = 5
INSTITUTION_COUNT = 5
ADMIN_COUNT = 2
STUDENT_COUNT = TOTAL_USERS - INSTRUCTOR_COUNT - SCHOOL_COUNT - INSTITUTION_COUNT - ADMIN_COUNT
POSTING_COUNT = 100

REGIONS = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"]
SUBJECTS = ["math", "english", "science", "coding", "art"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_core_tables(conn) -> None:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'instructor',
            organization TEXT,
            created_at TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            region TEXT,
            rate INTEGER,
            status TEXT DEFAULT 'open',
            deadline TEXT,
            created_at TEXT,
            owner_id INTEGER
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS instructor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            subjects TEXT,
            regions TEXT,
            available_hours TEXT,
            status TEXT DEFAULT 'pending',
            background_check_consent INTEGER DEFAULT 0,
            child_abuse_consent INTEGER DEFAULT 0,
            withholding_consent INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            instructor_id INTEGER,
            org_id INTEGER,
            scheduled_at TEXT,
            scheduled_duration_minutes INTEGER DEFAULT 60,
            checkin_at TEXT,
            completed_at TEXT,
            actual_duration_minutes INTEGER,
            status TEXT DEFAULT 'scheduled',
            journal_content TEXT,
            student_rating INTEGER,
            gross_amount INTEGER,
            withholding_amount INTEGER,
            net_amount INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            reviewer_id INTEGER,
            instructor_id INTEGER,
            rating INTEGER,
            comment TEXT,
            reviewer_type TEXT DEFAULT 'institution',
            created_at TEXT
        )
    """))


def upsert_user(conn, email: str, role: str, organization: str) -> int:
    row = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).mappings().first()

    params = {
        "email": email,
        "password": DEMO_PASSWORD_HASH,
        "role": role,
        "organization": organization,
        "created_at": now_iso(),
    }

    if row:
        conn.execute(
            text("""
                UPDATE users
                SET password = :password,
                    role = :role,
                    organization = :organization
                WHERE email = :email
            """),
            params,
        )
        return int(row["id"])

    conn.execute(
        text("""
            INSERT INTO users (email, password, role, organization, created_at)
            VALUES (:email, :password, :role, :organization, :created_at)
        """),
        params,
    )
    created = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).mappings().first()
    return int(created["id"])


def seed_users(conn):
    instructors = []
    schools = []
    institutions = []
    admins = []
    students = []

    for i in range(1, INSTRUCTOR_COUNT + 1):
        uid = upsert_user(conn, f"instructor{i:02d}@demo.edulink.local", "instructor", f"Instructor Group {((i - 1) % 5) + 1}")
        instructors.append(uid)

    for i in range(1, SCHOOL_COUNT + 1):
        uid = upsert_user(conn, f"school{i:02d}@demo.edulink.local", "school", f"Demo School {i}")
        schools.append(uid)

    for i in range(1, INSTITUTION_COUNT + 1):
        uid = upsert_user(conn, f"institution{i:02d}@demo.edulink.local", "institution", f"Demo Education Center {i}")
        institutions.append(uid)

    for i in range(1, ADMIN_COUNT + 1):
        uid = upsert_user(conn, f"ops{i:02d}@demo.edulink.local", "admin", "System Operations Center")
        admins.append(uid)

    for i in range(1, STUDENT_COUNT + 1):
        uid = upsert_user(conn, f"student{i:04d}@demo.edulink.local", "student", f"Learner Cohort {((i - 1) % 20) + 1}")
        students.append(uid)

    return {
        "instructors": instructors,
        "schools": schools,
        "institutions": institutions,
        "admins": admins,
        "students": students,
    }


def seed_instructor_profiles(conn, instructor_ids):
    for idx, user_id in enumerate(instructor_ids, start=1):
        subject_set = [SUBJECTS[(idx - 1) % len(SUBJECTS)], SUBJECTS[(idx) % len(SUBJECTS)]]
        region_set = [REGIONS[(idx - 1) % len(REGIONS)], REGIONS[(idx) % len(REGIONS)]]
        conn.execute(
            text("""
                INSERT INTO instructor_profiles (
                    user_id, full_name, subjects, regions, available_hours,
                    status, background_check_consent, child_abuse_consent,
                    withholding_consent, created_at, updated_at
                )
                VALUES (
                    :user_id, :full_name, :subjects, :regions, :available_hours,
                    'approved', 1, 1, 1, :created_at, :updated_at
                )
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    subjects = excluded.subjects,
                    regions = excluded.regions,
                    available_hours = excluded.available_hours,
                    status = 'approved',
                    updated_at = excluded.updated_at
            """),
            {
                "user_id": user_id,
                "full_name": f"Demo Instructor {idx}",
                "subjects": ",".join(subject_set),
                "regions": ",".join(region_set),
                "available_hours": "Mon-Fri 09:00-18:00",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            },
        )


def seed_postings(conn, owner_ids):
    posting_ids = []
    base = datetime.now(timezone.utc)
    for i in range(1, POSTING_COUNT + 1):
        owner_id = owner_ids[((i - 1) // 20) % len(owner_ids)]
        subject = SUBJECTS[(i - 1) % len(SUBJECTS)]
        region = REGIONS[(i - 1) % len(REGIONS)]
        deadline = (base + timedelta(days=14 + (i % 7))).isoformat()
        created_at = (base - timedelta(days=i % 28)).isoformat()
        rate = 45000 + ((i % 6) * 5000)

        conn.execute(
            text("""
                INSERT INTO postings (title, subject, region, rate, status, deadline, created_at, owner_id)
                VALUES (:title, :subject, :region, :rate, 'open', :deadline, :created_at, :owner_id)
            """),
            {
                "title": f"{subject.title()} Demo Class #{i:02d}",
                "subject": subject,
                "region": region,
                "rate": rate,
                "deadline": deadline,
                "created_at": created_at,
                "owner_id": owner_id,
            },
        )
        row = conn.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()
        posting_ids.append(int(row["id"]))

    return posting_ids


def seed_applications_sessions_reviews(conn, posting_ids, owner_ids, instructor_ids):
    for idx, posting_id in enumerate(posting_ids, start=1):
        primary_instructor_id = instructor_ids[(idx - 1) % len(instructor_ids)]
        secondary_instructor_id = instructor_ids[(idx + 1) % len(instructor_ids)]
        tertiary_instructor_id = instructor_ids[(idx + 3) % len(instructor_ids)]
        candidates = [
            (primary_instructor_id, "approved"),
            (secondary_instructor_id, "pending"),
            (tertiary_instructor_id, "rejected"),
        ]

        for instructor_id, status in candidates:
            conn.execute(
                text("""
                    INSERT INTO applications (posting_id, student_id, status, created_at)
                    VALUES (:posting_id, :student_id, :status, :created_at)
                """),
                {
                    "posting_id": posting_id,
                    "student_id": instructor_id,
                    "status": status,
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=idx % 28)).isoformat(),
                },
            )
        owner_id = owner_ids[(idx - 1) % len(owner_ids)]
        scheduled = datetime.now(timezone.utc) - timedelta(days=((idx - 1) % 28), hours=(idx % 6))
        is_completed = idx % 10 != 0

        gross = 72000 + ((idx % 4) * 6000) + (8000 if idx % 3 == 0 else 0)
        withholding = int(round(gross * 0.033))
        net = gross - withholding

        conn.execute(
            text("""
                INSERT INTO sessions (
                    posting_id, instructor_id, org_id, scheduled_at,
                    scheduled_duration_minutes, checkin_at, completed_at,
                    actual_duration_minutes, status, journal_content, student_rating,
                    gross_amount, withholding_amount, net_amount, created_at, updated_at
                )
                VALUES (
                    :posting_id, :instructor_id, :org_id, :scheduled_at,
                    90, :checkin_at, :completed_at,
                    :actual_duration_minutes, :status, :journal_content, :student_rating,
                    :gross_amount, :withholding_amount, :net_amount, :created_at, :updated_at
                )
            """),
            {
                "posting_id": posting_id,
                "instructor_id": primary_instructor_id,
                "org_id": owner_id,
                "scheduled_at": scheduled.isoformat(),
                "checkin_at": (scheduled + timedelta(minutes=3)).isoformat() if is_completed else None,
                "completed_at": (scheduled + timedelta(minutes=90)).isoformat() if is_completed else None,
                "actual_duration_minutes": 90 if is_completed else None,
                "status": "completed" if is_completed else "scheduled",
                "journal_content": f"Month-long class log for instructor {(idx - 1) % len(instructor_ids) + 1}" if is_completed else None,
                "student_rating": 4 + (idx % 2) if is_completed else None,
                "gross_amount": gross,
                "withholding_amount": withholding,
                "net_amount": net,
                "created_at": scheduled.isoformat(),
                "updated_at": now_iso(),
            },
        )

        session_id = conn.execute(text("SELECT last_insert_rowid() AS id")).mappings().first()["id"]
        if is_completed and idx % 2 == 0:
            conn.execute(
                text("""
                    INSERT INTO reviews (
                        session_id, reviewer_id, instructor_id, rating, comment, reviewer_type, created_at
                    )
                    VALUES (
                        :session_id, :reviewer_id, :instructor_id, :rating, :comment, 'institution', :created_at
                    )
                """),
                {
                    "session_id": session_id,
                    "reviewer_id": owner_id,
                    "instructor_id": primary_instructor_id,
                    "rating": 4 + (idx % 2),
                    "comment": "Punctual, well prepared, and incentive-eligible performance",
                    "created_at": now_iso(),
                },
            )


def run_seed(engine, reset_demo_data: bool, seed_activity: bool) -> None:
    with engine.begin() as conn:
        conn.execute(text("PRAGMA busy_timeout = 30000"))
        ensure_core_tables(conn)

        if reset_demo_data:
            # Reset only demo namespace data for repeatable runs.
            conn.execute(text("""
                DELETE FROM reviews
                WHERE instructor_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
            """), {"pattern": "%@demo.edulink.local"})
            conn.execute(text("""
                DELETE FROM sessions
                WHERE instructor_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
                   OR org_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
            """), {"pattern": "%@demo.edulink.local"})
            conn.execute(text("""
                DELETE FROM applications
                WHERE student_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
                   OR posting_id IN (
                    SELECT id FROM postings WHERE owner_id IN (
                        SELECT id FROM users WHERE email LIKE :pattern
                    )
                )
            """), {"pattern": "%@demo.edulink.local"})
            conn.execute(text("""
                DELETE FROM postings
                WHERE owner_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
            """), {"pattern": "%@demo.edulink.local"})
            conn.execute(text("""
                DELETE FROM instructor_profiles
                WHERE user_id IN (
                    SELECT id FROM users WHERE email LIKE :pattern
                )
            """), {"pattern": "%@demo.edulink.local"})
            conn.execute(text("DELETE FROM users WHERE email LIKE :pattern"), {"pattern": "%@demo.edulink.local"})

        user_groups = seed_users(conn)
        seed_instructor_profiles(conn, user_groups["instructors"])
        if seed_activity:
            owners = user_groups["schools"] + user_groups["institutions"]
            posting_ids = seed_postings(conn, owners)
            seed_applications_sessions_reviews(conn, posting_ids, owners, user_groups["instructors"])


def parse_args():
    parser = argparse.ArgumentParser(description='Seed EduLink v2 demo data safely')
    parser.add_argument('--db-url', default='sqlite:///./edulinks_demo.db', help='Database URL for demo seed target')
    parser.add_argument('--allow-prod-db', action='store_true', help='Allow using a non-demo DB URL')
    parser.add_argument('--reset-demo-data', action='store_true', help='Delete existing demo namespace before seeding')
    parser.add_argument('--seed-activity', action='store_true', help='Seed postings/applications/sessions/reviews in addition to users')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_url = str(args.db_url or '').strip()
    if not args.allow_prod_db and 'demo' not in db_url.lower():
        raise RuntimeError('Refusing to seed non-demo DB. Use --allow-prod-db if you really want this.')

    engine = create_engine(db_url, echo=False, connect_args={"timeout": 30})

    last_exc = None
    for attempt in range(1, 6):
        try:
            run_seed(
                engine,
                reset_demo_data=bool(args.reset_demo_data),
                seed_activity=bool(args.seed_activity),
            )
            last_exc = None
            break
        except OperationalError as exc:
            last_exc = exc
            if 'database is locked' not in str(exc).lower() or attempt == 5:
                raise
            wait_seconds = attempt * 2
            print(f"Database is locked. Retry {attempt}/5 in {wait_seconds}s...")
            time.sleep(wait_seconds)

    if last_exc is not None:
        raise last_exc

    print("Demo v2 dataset seeded.")
    print(f"- Target DB URL: {db_url}")
    print(f"- Reset demo namespace: {bool(args.reset_demo_data)}")
    print(f"- Seed activity datasets: {bool(args.seed_activity)}")
    print(f"- Total users: {TOTAL_USERS}")
    print(f"- Instructors: {INSTRUCTOR_COUNT}")
    print(f"- Schools: {SCHOOL_COUNT}")
    print(f"- Institutions: {INSTITUTION_COUNT}")
    print(f"- System operators (admin): {ADMIN_COUNT}")
    print(f"- Students: {STUDENT_COUNT}")
    print(f"- Login password for demo users: {PASSWORD}")
    print("- Example social login payload provider: google | kakao")


if __name__ == "__main__":
    main()
