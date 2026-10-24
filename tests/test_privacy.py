from tests.helpers import client, make_user

ALLOWED = {"verified", "configured", "unverified", "failed"}

def checks(h):
    r = client.get("/privacy/status", headers=h)
    assert r.status_code == 200
    return {c["id"]: c for c in r.json()["checks"]}

def test_privacy_status_requires_login():
    assert client.get("/privacy/status").status_code in (401, 403)

def test_database_checks_are_verified_live():
    c = checks(make_user())
    assert c["db_role"]["status"] == "verified"
    assert c["rls_tables"]["status"] == "verified"
    assert c["audit_append_only"]["status"] == "verified"

def test_app_guard_check_is_verified():
    assert checks(make_user())["app_guard"]["status"] == "verified"

def test_firewall_is_not_claimed_verified_without_a_test():
    c = checks(make_user())
    assert all(x["status"] in ALLOWED for x in c.values())
    assert c["os_firewall"]["status"] == "unverified"

def test_network_probe_needs_explicit_confirmation():
    h = make_user()
    assert client.post("/privacy/verify-network", json={"confirm": False}, headers=h).status_code == 400