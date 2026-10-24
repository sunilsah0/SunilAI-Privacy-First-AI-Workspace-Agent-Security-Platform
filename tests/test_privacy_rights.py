from sqlalchemy import text
from services.api.app.db import engine
from services.api.app.retention import run_retention
from tests.helpers import client, make_user_info, as_user, build_org

PW = "correct-horse-battery"

def doc(u, title, content="x"):
    assert client.post("/documents", json={"title": title, "content": content}, headers=u["h"]).status_code == 201

def conv(u, title):
    r = client.post("/conversations", json={"title": title}, headers=u["h"])
    assert r.status_code == 201
    return r.json()["id"]

def delete_account(u, password=PW, confirm=True):
    return client.request("DELETE", "/me", json={"password": password, "confirm": confirm}, headers=u["h"])

def age(u, conv_id, days=40):
    with engine.begin() as c:
        as_user(c, u["id"])
        c.execute(text("UPDATE conversations SET created_at = now() - make_interval(days => :d) "
                       "WHERE id = :c"), {"d": days, "c": conv_id})

def conv_exists(u, cid):
    return client.get(f"/conversations/{cid}", headers=u["h"]).status_code == 200

def test_export_contains_only_my_data():
    a, b = make_user_info(), make_user_info()
    doc(a, "a-doc-title", "a-secret-111"); conv(a, "a-conv-title")
    doc(b, "b-doc-title", "b-secret-222")
    r = client.get("/me/export", headers=a["h"])
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    assert "a-secret-111" in r.text and "a-conv-title" in r.text and a["email"] in r.text
    assert "b-secret-222" not in r.text and b["email"] not in r.text

def test_export_requires_login():
    assert client.get("/me/export").status_code in (401, 403)

def test_delete_needs_password_and_confirmation():
    a = make_user_info()
    assert delete_account(a, password="wrong-password-123").status_code == 403
    assert delete_account(a, confirm=False).status_code == 400
    assert client.get("/me", headers=a["h"]).status_code == 200

def test_delete_account_removes_my_data_and_only_mine():
    a, b = make_user_info(), make_user_info()
    doc(a, "mine"); conv(a, "mine"); doc(b, "keep-me")
    assert delete_account(a).status_code == 200
    assert client.get("/me", headers=a["h"]).status_code == 401
    assert client.post("/auth/login", json={"email": a["email"], "password": PW}).status_code == 401
    with engine.begin() as c:
        as_user(c, a["id"])
        for table in ("documents", "conversations", "tool_permissions", "user_settings"):
            n = c.execute(text(f"SELECT count(*) FROM {table} WHERE owner_id = :u"), {"u": a["id"]}).scalar()
            assert n == 0, table
        assert c.execute(text("SELECT count(*) FROM users WHERE id = :u"), {"u": a["id"]}).scalar() == 0
    assert [d["title"] for d in client.get("/documents", headers=b["h"]).json()] == ["keep-me"]

def test_sole_owner_cannot_delete_account_until_another_owner_exists():
    org, owner, (mem,) = build_org("member")
    assert delete_account(owner).status_code == 409
    r = client.patch(f"/orgs/{org}/members/{mem['id']}", json={"role": "owner"}, headers=owner["h"])
    assert r.status_code == 200
    assert delete_account(owner).status_code == 200
    assert [o["role"] for o in client.get("/orgs", headers=mem["h"]).json()] == ["owner"]

def test_shared_documents_and_audit_survive_the_authors_deletion():
    org, owner, (mem,) = build_org("member")
    r = client.post(f"/orgs/{org}/documents", json={"title": "Plan", "content": "shared"}, headers=mem["h"])
    assert r.status_code == 201
    assert delete_account(mem).status_code == 200
    docs = client.get(f"/orgs/{org}/documents", headers=owner["h"]).json()
    assert [(d["title"], d["created_by"]) for d in docs] == [("Plan", None)]
    audit = client.get(f"/orgs/{org}/audit", headers=owner["h"]).json()
    assert any(e["actor"] == "(deleted user)" for e in audit)

def test_users_table_blocks_changes_to_other_people_in_database():
    a, b = make_user_info(), make_user_info()
    with engine.begin() as c:
        as_user(c, a["id"])
        assert c.execute(text("DELETE FROM users WHERE id = :b"), {"b": b["id"]}).rowcount == 0
        assert c.execute(text("UPDATE users SET email = 'x@y.zz' WHERE id = :b"), {"b": b["id"]}).rowcount == 0
    assert client.get("/me", headers=b["h"]).status_code == 200

def test_retention_setting_roundtrip_and_validation():
    a = make_user_info()
    assert client.put("/me/settings", json={"conversation_retention_days": 30}, headers=a["h"]).status_code == 200
    assert client.get("/me/settings", headers=a["h"]).json()["conversation_retention_days"] == 30
    assert client.put("/me/settings", json={"conversation_retention_days": 0}, headers=a["h"]).status_code == 422
    assert client.put("/me/settings", json={"conversation_retention_days": None}, headers=a["h"]).status_code == 200
    assert client.get("/me/settings", headers=a["h"]).json()["conversation_retention_days"] is None

def test_retention_job_only_touches_people_who_opted_in():
    a, b = make_user_info(), make_user_info()
    client.put("/me/settings", json={"conversation_retention_days": 30}, headers=a["h"])
    a_old, a_new, b_old = conv(a, "old"), conv(a, "new"), conv(b, "old")
    age(a, a_old); age(b, b_old)
    assert run_retention() >= 1
    assert not conv_exists(a, a_old)
    assert conv_exists(a, a_new)
    assert conv_exists(b, b_old)          # b never opted in, so the job leaves it alone

def test_settings_are_hidden_without_identity():
    a = make_user_info()
    client.put("/me/settings", json={"conversation_retention_days": 7}, headers=a["h"])
    with engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM user_settings")).scalar() == 0