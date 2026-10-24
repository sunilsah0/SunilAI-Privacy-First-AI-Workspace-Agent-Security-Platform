import uuid
from fastapi.testclient import TestClient
from services.api.app.main import app

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