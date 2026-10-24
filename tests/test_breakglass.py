import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from services.api.app.db import engine
from tests.helpers import client, make_user_info, as_user, build_org

REASON = "Investigating a suspected policy violation, ticket 4711"

def personal_doc(u, title="diary", content="secret-mem-777"):
    r = client.post("/documents", json={"title": title, "content": content}, headers=u["h"])
    assert r.status_code == 201
    return r.json()["id"]

def request_access(org, actor, target, minutes=15, reason=REASON):
    return client.post(f"/orgs/{org}/breakglass",
                       json={"target_user_id": target["id"], "reason": reason, "duration_minutes": minutes},
                       headers=actor["h"])

def decide(org, gid, actor, action):
    return client.post(f"/orgs/{org}/breakglass/{gid}/{action}", headers=actor["h"])

def approved_grant(org, owner, requester, target, minutes=15):
    r = request_access(org, requester, target, minutes)
    assert r.status_code == 201
    gid = r.json()["id"]
    assert decide(org, gid, owner, "approve").status_code == 200
    return gid

def visible_docs(uid, target_id):
    """How many of the target's documents the DATABASE lets this person see."""
    with engine.begin() as c:
        as_user(c, uid)
        return c.execute(text("SELECT count(*) FROM documents WHERE owner_id = :t"), {"t": target_id}).scalar()

def test_no_access_without_a_grant():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    doc = personal_doc(mem)
    assert client.get(f"/documents/{doc}", headers=sec["h"]).status_code == 404
    assert client.get("/breakglass/00000000-0000-0000-0000-000000000000/documents", headers=sec["h"]).status_code == 404
    assert visible_docs(sec["id"], mem["id"]) == 0

def test_full_flow_and_the_person_can_see_it():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    doc = personal_doc(mem)
    r = request_access(org, sec, mem)
    assert r.status_code == 201 and r.json()["status"] == "pending"
    gid = r.json()["id"]
    assert client.get(f"/breakglass/{gid}/documents", headers=sec["h"]).status_code == 404   # pending: nothing yet
    assert decide(org, gid, owner, "approve").status_code == 200
    listing = client.get(f"/breakglass/{gid}/documents", headers=sec["h"])
    assert listing.status_code == 200 and [d["title"] for d in listing.json()] == ["diary"]
    read = client.get(f"/breakglass/{gid}/documents/{doc}", headers=sec["h"])
    assert read.status_code == 200 and read.json()["content"] == "secret-mem-777"
    log = client.get("/me/access-log", headers=mem["h"]).json()
    assert {e["action"] for e in log} == {"list", "read"}
    assert all(e["accessor"] == sec["email"] for e in log)
    events = {e["event"] for e in client.get(f"/orgs/{org}/audit", headers=owner["h"]).json()}
    assert {"breakglass_requested", "breakglass_approved", "breakglass_read"} <= events

def test_two_person_rule():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    gid = request_access(org, owner, mem).json()["id"]              # the owner asks...
    assert decide(org, gid, owner, "approve").status_code == 400    # ...but cannot approve their own request
    assert decide(org, gid, sec, "approve").status_code == 403      # a security admin is not an owner

def test_only_admin_roles_can_request_access():
    org, owner, (sec, mem, aud) = build_org("security_admin", "member", "auditor")
    assert request_access(org, mem, sec).status_code == 403
    assert request_access(org, aud, mem).status_code == 403

def test_cannot_request_access_to_a_non_member():
    org, owner, (sec,) = build_org("security_admin")
    assert request_access(org, sec, make_user_info()).status_code == 404

def test_cross_tenant_request_is_blocked_by_the_database():
    org1, owner1, (sec, mem1) = build_org("security_admin", "member")
    org2, owner2, (victim,) = build_org("member")
    sql = ("INSERT INTO break_glass_grants (id, org_id, requester_id, target_user_id, reason, "
           "duration_minutes, status, requested_at) "
           "VALUES (gen_random_uuid(), :o, :r, :t, :why, 10, 'pending', now())")
    with engine.begin() as c:                      # control: a real member of org1 is accepted
        as_user(c, sec["id"])
        c.execute(text(sql), {"o": org1, "r": sec["id"], "t": mem1["id"], "why": REASON})
    with pytest.raises(DBAPIError):                # a person from another company is refused
        with engine.begin() as c:
            as_user(c, sec["id"])
            c.execute(text(sql), {"o": org1, "r": sec["id"], "t": victim["id"], "why": REASON})

def test_expired_grant_stops_working_in_api_and_database():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    personal_doc(mem)
    gid = approved_grant(org, owner, sec, mem)
    assert visible_docs(sec["id"], mem["id"]) >= 1                 # the database allows it during the grant
    with engine.begin() as c:
        as_user(c, owner["id"])
        res = c.execute(text("UPDATE break_glass_grants SET expires_at = now() - interval '1 minute' "
                             "WHERE id = :g"), {"g": gid})
        assert res.rowcount == 1
    assert client.get(f"/breakglass/{gid}/documents", headers=sec["h"]).status_code == 404
    assert visible_docs(sec["id"], mem["id"]) == 0

def test_revoke_ends_access_immediately():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    personal_doc(mem)
    gid = approved_grant(org, owner, sec, mem)
    assert client.get(f"/breakglass/{gid}/documents", headers=sec["h"]).status_code == 200
    assert decide(org, gid, owner, "revoke").status_code == 200
    assert client.get(f"/breakglass/{gid}/documents", headers=sec["h"]).status_code == 404
    assert visible_docs(sec["id"], mem["id"]) == 0

def test_suspending_the_requester_ends_access():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    personal_doc(mem)
    gid = approved_grant(org, owner, sec, mem)
    r = client.patch(f"/orgs/{org}/members/{sec['id']}", json={"status": "suspended"}, headers=owner["h"])
    assert r.status_code == 200
    assert client.get(f"/breakglass/{gid}/documents", headers=sec["h"]).status_code == 404
    assert visible_docs(sec["id"], mem["id"]) == 0

def test_grant_duration_is_capped_at_one_hour():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    assert request_access(org, sec, mem, minutes=120).status_code == 422
    gid = approved_grant(org, owner, sec, mem, minutes=60)
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            as_user(c, owner["id"])
            c.execute(text("UPDATE break_glass_grants SET expires_at = now() + interval '5 hours' "
                           "WHERE id = :g"), {"g": gid})

def test_break_glass_is_read_only():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    doc = personal_doc(mem)
    approved_grant(org, owner, sec, mem)
    with engine.begin() as c:
        as_user(c, sec["id"])
        up = c.execute(text("UPDATE documents SET title = 'hacked' WHERE owner_id = :t"), {"t": mem["id"]})
        de = c.execute(text("DELETE FROM documents WHERE owner_id = :t"), {"t": mem["id"]})
        assert up.rowcount == 0 and de.rowcount == 0
    assert client.get(f"/documents/{doc}", headers=mem["h"]).json()["title"] == "diary"

def test_access_log_is_append_only():
    for sql in ("UPDATE break_glass_access_log SET action = 'x'", "DELETE FROM break_glass_access_log"):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(sql))

def test_person_cannot_see_pending_requests_about_them_but_sees_approved_ones():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    def grants_seen_by_target():
        with engine.begin() as c:
            as_user(c, mem["id"])
            return c.execute(text("SELECT count(*) FROM break_glass_grants WHERE target_user_id = :t"),
                             {"t": mem["id"]}).scalar()
    gid = request_access(org, sec, mem).json()["id"]
    assert grants_seen_by_target() == 0
    assert decide(org, gid, owner, "approve").status_code == 200
    assert grants_seen_by_target() == 1

def test_only_the_requester_can_use_a_grant():
    org, owner, (sec, mem) = build_org("security_admin", "member")
    personal_doc(mem)
    gid = approved_grant(org, owner, sec, mem)
    other = make_user_info()
    for u in (owner, other, mem):
        assert client.get(f"/breakglass/{gid}/documents", headers=u["h"]).status_code == 404
    assert visible_docs(owner["id"], mem["id"]) == 0
    assert visible_docs(other["id"], mem["id"]) == 0
    assert client.get("/me/access-log", headers=other["h"]).json() == []