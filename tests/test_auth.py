import uuid
from tests.helpers import client, make_user
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

def make_user():
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/register", json={"email": email, "password": "correct-horse-battery"})
    token = client.post("/auth/login", json={"email": email, "password": "correct-horse-battery"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_me_requires_login():
    assert client.get("/me").status_code in (401, 403)

def test_login_and_me():
    headers = make_user()
    assert client.get("/me", headers=headers).status_code == 200

def test_wrong_password_rejected():
    r = client.post("/auth/login", json={"email": "nobody@test.com", "password": "wrong-password-123"})
    assert r.status_code == 401