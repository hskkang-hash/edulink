import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
EMAIL = "smoke_activity_file@example.com"
PASSWORD = "password"


def post_json(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req)


try:
    post_json("/auth/register", {"email": EMAIL, "password": PASSWORD, "role": "student"})
except urllib.error.HTTPError:
    pass

login_resp = post_json("/auth/login", {"email": EMAIL, "password": PASSWORD})
login_data = json.loads(login_resp.read().decode("utf-8"))
token = login_data["access_token"]

activity_req = urllib.request.Request(
    BASE + "/dashboard/activity",
    headers={"Authorization": f"Bearer {token}"},
)
activity_resp = urllib.request.urlopen(activity_req)
activity_data = json.loads(activity_resp.read().decode("utf-8"))

print("activity_status=200")
print(f"activity_items={len(activity_data)}")
