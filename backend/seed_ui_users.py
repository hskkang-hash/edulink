from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash


USERS = [
    {
        "email": "ui.instructor@edulink.local",
        "password": "Pass1234!",
        "role": "instructor",
        "organization": "Instructor Team",
    },
    {
        "email": "ui.student@edulink.local",
        "password": "Pass1234!",
        "role": "student",
        "organization": "Student Team",
    },
    {
        "email": "ui.admin@edulink.local",
        "password": "Pass1234!",
        "role": "admin",
        "organization": "Admin Team",
    },
    {
        "email": "ui.superadmin@edulink.local",
        "password": "Pass1234!",
        "role": "super_admin",
        "organization": "Super Admin Team",
    },
]


def main() -> None:
    engine = create_engine("sqlite:///./edulink.db", echo=False)

    with engine.begin() as conn:
        for user in USERS:
            existing = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user["email"]},
            ).fetchone()

            params = {
                "email": user["email"],
                "password": generate_password_hash(user["password"]),
                "role": user["role"],
                "organization": user["organization"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE users
                        SET password = :password,
                            role = :role,
                            organization = :organization
                        WHERE email = :email
                        """
                    ),
                    params,
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (email, password, role, organization, created_at)
                        VALUES (:email, :password, :role, :organization, :created_at)
                        """
                    ),
                    params,
                )

    print("Seeded UI users:")
    for user in USERS:
        print(f"- {user['email']} ({user['role']}) / Pass1234!")


if __name__ == "__main__":
    main()
