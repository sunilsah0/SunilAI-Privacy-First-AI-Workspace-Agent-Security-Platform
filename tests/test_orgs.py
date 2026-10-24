import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from services.api.app.db import engine
from tests.helpers import client, make_user_info

def new_org(u, name="Acme"):
    r = client.post("/orgs", json={"name": name}, headers=u["h"])
    assert r.status_code == 201
    return r.json()["id"]

def add(org, actor, target, role):
    return client.post(f"/orgs/{org}/members", json={"email": target["email"], "role": role}, headers=actor["h"])

def setup(*roles):
    """An org with an owner plus one new user per role. Returns (org, owner, [users])."""
    owner = make_user_info()
    org = new_org(owner)
    users = []
    for role in roles:
        u = make_user_info()
        assert add(org, owner, u, role).status_code == 201
        users.append(u)
    return org, owner, users

def shared_doc(org, u, title="Plan", content="shared body"):
    r = client.post(f"/orgs/{org}/documents", json={"title": title, "content": content}, headers=u["h"])
    assert r.status_code == 201
    return r.json()["id"]

def as_user(conn, uid):
    conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": uid})

def test_creator_becomes_owner():
    u = make_user_info(); org = new_org(u)
    orgs = client.get("/orgs", headers=u["h"]).json()
    assert [(o["id"], o["role"]) for o in orgs] == [(org, "owner")]

def test_other_tenant_gets_404_everywhere():
    org1, owner1, _ = setup("member")
    d1 = shared_doc(org1, owner1)
    b = make_user_info(); new_org(b, "Other Inc")
    for path in ("members", "documents", "audit", f"documents/{d1}"):
        assert client.get(f"/orgs/{org1}/{path}", headers=b["h"]).status_code == 404
    r = client.post(f"/orgs/{org1}/documents", json={"title": "x", "content": "y"}, headers=b["h"])
    assert r.status_code == 404
    assert org1 not in [o["id"] for o in client.get("/orgs", headers=b["h"]).json()]

def test_members_share_documents():
    org, owner, (m1, m2) = setup("member", "member")
    did = shared_doc(org, m1)
    r = client.get(f"/orgs/{org}/documents/{did}", headers=m2["h"])
    assert r.status_code == 200 and r.json()["content"] == "shared body"
    titles = [d["title"] for d in client.get(f"/orgs/{org}/documents", headers=m2["h"]).json()]
    assert "Plan" in titles

def test_shared_document_not_reachable_from_another_org():
    org1, owner1, _ = setup()
    did = shared_doc(org1, owner1)
    owner2 = make_user_info(); org2 = new_org(owner2, "Other")
    assert client.get(f"/orgs/{org2}/documents/{did}", headers=owner2["h"]).status_code == 404
    assert client.get(f"/orgs/{org1}/documents/{did}", headers=owner2["h"]).status_code == 404

def test_security_admin_and_auditor_cannot_read_shared_content():
    org, owner, (sec, aud, mem) = setup("security_admin", "auditor", "member")
    did = shared_doc(org, mem)
    for u in (sec, aud):
        assert client.get(f"/orgs/{org}/documents", headers=u["h"]).status_code == 403
        assert client.get(f"/orgs/{org}/documents/{did}", headers=u["h"]).status_code == 403
    assert client.get(f"/orgs/{org}/documents/{did}", headers=owner["h"]).status_code == 200

def test_database_blocks_admin_content_access_even_without_python_checks():
    org, owner, (sec,) = setup("security_admin")
    shared_doc(org, owner)
    with engine.begin() as c:
        as_user(c, sec["id"])
        assert c.execute(text("SELECT count(*) FROM org_documents")).scalar() == 0
    with engine.begin() as c:
        as_user(c, owner["id"])
        assert c.execute(text("SELECT count(*) FROM org_documents")).scalar() >= 1

def test_admins_cannot_read_members_private_documents_or_chats():
    org, owner, (sec, mem) = setup("security_admin", "member")
    doc = client.post("/documents", json={"title": "diary", "content": "private"}, headers=mem["h"]).json()["id"]
    conv = client.post("/conversations", json={"title": "mine"}, headers=mem["h"]).json()["id"]
    for admin in (owner, sec):
        assert client.get(f"/documents/{doc}", headers=admin["h"]).status_code == 404
        assert client.get(f"/conversations/{conv}", headers=admin["h"]).status_code == 404
        assert client.get("/documents", headers=admin["h"]).json() == []

def test_non_admin_roles_cannot_manage_members():
    org, owner, people = setup("team_admin", "member", "auditor")
    newbie = make_user_info()
    for u in people:
        assert add(org, u, newbie, "member").status_code == 403

def test_security_admin_cannot_create_or_touch_owner():
    org, owner, (sec,) = setup("security_admin")
    assert add(org, sec, make_user_info(), "owner").status_code == 403
    for body in ({"role": "member"}, {"status": "suspended"}):
        r = client.patch(f"/orgs/{org}/members/{owner['id']}", json=body, headers=sec["h"])
        assert r.status_code == 403
    assert [o["role"] for o in client.get("/orgs", headers=owner["h"]).json()] == ["owner"]

def test_role_change_is_audited_and_audit_is_restricted():
    org, owner, (mem, aud) = setup("member", "auditor")
    r = client.patch(f"/orgs/{org}/members/{mem['id']}", json={"role": "team_admin"}, headers=owner["h"])
    assert r.status_code == 200
    events = client.get(f"/orgs/{org}/audit", headers=aud["h"])
    assert events.status_code == 200
    assert "member_updated" in [e["event"] for e in events.json()]
    assert client.get(f"/orgs/{org}/audit", headers=mem["h"]).status_code == 403

def test_suspended_member_loses_org_access_but_keeps_personal_data():
    org, owner, (mem,) = setup("member")
    shared_doc(org, owner)
    mine = client.post("/documents", json={"title": "mine", "content": "x"}, headers=mem["h"]).json()["id"]
    assert client.get(f"/orgs/{org}/documents", headers=mem["h"]).status_code == 200
    url = f"/orgs/{org}/members/{mem['id']}"
    assert client.patch(url, json={"status": "suspended"}, headers=owner["h"]).status_code == 200
    assert client.get(f"/orgs/{org}/documents", headers=mem["h"]).status_code == 404
    assert org not in [o["id"] for o in client.get("/orgs", headers=mem["h"]).json()]
    assert client.get(f"/documents/{mine}", headers=mem["h"]).status_code == 200
    assert client.patch(url, json={"status": "active"}, headers=owner["h"]).status_code == 200
    assert client.get(f"/orgs/{org}/documents", headers=mem["h"]).status_code == 200

def test_cannot_change_own_membership():
    org, owner, _ = setup()
    r = client.patch(f"/orgs/{org}/members/{owner['id']}", json={"role": "member"}, headers=owner["h"])
    assert r.status_code == 400

def test_outsider_cannot_insert_membership_in_database():
    org, owner, (mem,) = setup("member")
    outsider = make_user_info()
    sql = ("INSERT INTO memberships (id, org_id, user_id, role, status, created_at) "
           "VALUES (gen_random_uuid(), :o, :u, 'owner', 'active', now())")
    for actor in (outsider, mem):          # an outsider, and a plain member, both try to add an owner
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                as_user(c, actor["id"])
                c.execute(text(sql), {"o": org, "u": outsider["id"]})

def test_outsider_and_member_cannot_escalate_roles_in_database():
    org, owner, (mem,) = setup("member")
    outsider = make_user_info()
    for actor in (outsider, mem):
        with engine.begin() as c:
            as_user(c, actor["id"])
            res = c.execute(text("UPDATE memberships SET role = 'owner' WHERE org_id = :o"), {"o": org})
            assert res.rowcount == 0
    assert [o["role"] for o in client.get("/orgs", headers=mem["h"]).json()] == ["member"]

def test_org_audit_log_is_append_only():
    for sql in ("UPDATE org_audit_events SET detail = 'x'", "DELETE FROM org_audit_events"):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(sql))

def test_all_tenant_tables_have_forced_rls():
    with engine.connect() as c:
        rows = c.execute(text("""
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND (c.relname = 'organizations' OR EXISTS (
                    SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid
                      AND a.attname = 'org_id' AND NOT a.attisdropped))
        """)).all()
    assert {"organizations", "memberships", "org_documents", "org_audit_events"} <= {r[0] for r in rows}
    for name, rls, forced in rows:
        assert rls and forced, f"{name} is missing Row-Level Security"

def test_add_member_errors():
    org, owner, (mem,) = setup("member")
    assert add(org, owner, {"email": "nobody-here@test.com"}, "member").status_code == 404
    assert add(org, owner, mem, "member").status_code == 409
    assert add(org, owner, make_user_info(), "emperor").status_code == 403

def test_delete_shared_document_rules():
    org, owner, (m1, m2, adm) = setup("member", "member", "team_admin")
    d1 = shared_doc(org, m1)
    assert client.delete(f"/orgs/{org}/documents/{d1}", headers=m2["h"]).status_code == 403
    assert client.delete(f"/orgs/{org}/documents/{d1}", headers=m1["h"]).status_code == 204
    d2 = shared_doc(org, m1)
    assert client.delete(f"/orgs/{org}/documents/{d2}", headers=adm["h"]).status_code == 204

def test_create_organization_requires_identity():
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            c.execute(text("SELECT create_organization('No identity')"))