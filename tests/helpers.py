import uuid
from fastapi.testclient import TestClient
from services.api.app.main import app
from sqlalchemy import text

client = TestClient(app)

def make_user_info():
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    pw = "correct-horse-battery"
    client.post("/auth/register", json={"email": email, "password": pw})
    token = client.post("/auth/login", json={"email": email, "password": pw}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    uid = client.get("/me", headers=headers).json()["id"]
    return {"h": headers, "email": email, "id": uid}

def make_user():
    return make_user_info()["h"]

def as_user(conn, uid):
    conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": uid})

def new_org(u, name="Acme"):
    r = client.post("/orgs", json={"name": name}, headers=u["h"])
    assert r.status_code == 201
    return r.json()["id"]

def add_member(org, actor, target, role):
    return client.post(f"/orgs/{org}/members", json={"email": target["email"], "role": role}, headers=actor["h"])

def build_org(*roles):
    """An org with an owner plus one new user per role. Returns (org, owner, [users])."""
    owner = make_user_info()
    org = new_org(owner)
    users = []
    for role in roles:
        u = make_user_info()
        assert add_member(org, owner, u, role).status_code == 201
        users.append(u)
    return org, owner, users