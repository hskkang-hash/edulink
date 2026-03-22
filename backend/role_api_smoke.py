import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.getenv("EDULINK_BASE_URL", "http://localhost:8000")

USERS = [
    ("ui.instructor@edulink.local", "Pass1234!", "instructor"),
    ("ui.student@edulink.local", "Pass1234!", "student"),
    ("ui.admin@edulink.local", "Pass1234!", "admin"),
    ("ui.superadmin@edulink.local", "Pass1234!", "super_admin"),
]


def post_json(path, payload, headers=None):
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        payload = e.read().decode("utf-8")
        return e.code, json.loads(payload) if payload else {}


def get_json(path, headers=None):
    req = Request(f"{BASE_URL}{path}", method="GET", headers=headers or {})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        payload = e.read().decode("utf-8")
        return e.code, json.loads(payload) if payload else {}


def assert_true(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        sys.exit(1)


def main():
    print(f"[INFO] Running role smoke against {BASE_URL}")
    tokens = {}

    for email, password, expected_role in USERS:
        status, login_payload = post_json(
            "/auth/login", {"email": email, "password": password}
        )
        assert_true(status == 200, f"login failed for {email}: {status}")

        token = login_payload.get("access_token")
        assert_true(bool(token), f"missing access_token for {email}")
        tokens[expected_role] = token

        me_status, me_payload = get_json(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert_true(me_status == 200, f"/auth/me failed for {email}: {me_status}")
        assert_true(
            me_payload.get("role") == expected_role,
            f"role mismatch for {email}: expected={expected_role}, got={me_payload.get('role')}",
        )

    student_status, _ = get_json(
        "/api/network/admin/summary?period=2026-03",
        headers={"Authorization": f"Bearer {tokens['student']}"},
    )
    assert_true(student_status == 403, f"student should be forbidden, got {student_status}")

    admin_status, _ = get_json(
        "/api/network/admin/summary?period=2026-03",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    super_status, _ = get_json(
        "/api/network/admin/summary?period=2026-03",
        headers={"Authorization": f"Bearer {tokens['super_admin']}"},
    )

    assert_true(admin_status == 200, f"admin access failed: {admin_status}")
    assert_true(super_status == 200, f"super_admin access failed: {super_status}")

    print("[PASS] Role-based API smoke checks passed")


if __name__ == "__main__":
    try:
        main()
    except URLError as e:
        print(f"[FAIL] Network error: {e}")
        sys.exit(1)
