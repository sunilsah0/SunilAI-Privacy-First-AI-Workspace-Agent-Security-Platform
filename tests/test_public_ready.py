import uuid

import pytest
from starlette.requests import Request

from services.api.app import providers, rag, ratelimit, security
from services.api.app.main import app
from services.api.app.providers import FakeProvider, get_provider
from tests.helpers import client, make_user_info


@pytest.fixture
def limits_on():
    ratelimit.limiter.reset_all()
    ratelimit.ENABLED = True
    yield
    ratelimit.ENABLED = False
    ratelimit.limiter.reset_all()


def test_login_lockout_after_five_failures(limits_on):
    u = make_user_info()
    bad = {"email": u["email"], "password": "wrong-password-123"}
    for _ in range(5):
        assert client.post("/auth/login", json=bad).status_code == 401
    blocked = client.post("/auth/login", json=bad)
    assert blocked.status_code == 429 and "retry-after" in blocked.headers
    good = client.post("/auth/login", json={"email": u["email"], "password": "correct-horse-battery"})
    assert good.status_code == 429          # still locked, even with the right password
    other = make_user_info()                 # a different account is unaffected
    assert client.get("/me", headers=other["h"]).status_code == 200


def test_successful_login_resets_the_failure_count(limits_on):
    u = make_user_info()
    bad = {"email": u["email"], "password": "wrong-password-123"}
    good = {"email": u["email"], "password": "correct-horse-battery"}
    for _ in range(3):
        assert client.post("/auth/login", json=bad).status_code == 401
    assert client.post("/auth/login", json=good).status_code == 200
    for _ in range(4):
        assert client.post("/auth/login", json=bad).status_code == 401


def test_register_is_limited_per_address(limits_on):
    codes = []
    for _ in range(11):
        r = client.post("/auth/register", json={"email": f"{uuid.uuid4().hex[:8]}@test.com",
                                                "password": "correct-horse-battery"})
        codes.append(r.status_code)
    assert codes[:10] == [201] * 10
    assert codes[10] == 429


def test_expensive_endpoints_have_per_user_limits(limits_on):
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    try:
        u = make_user_info()
        codes = [client.post("/search", json={"query": "hello", "k": 1}, headers=u["h"]).status_code
                 for _ in range(61)]
        assert codes[:60] == [200] * 60
        assert codes[60] == 429
    finally:
        app.dependency_overrides.clear()


def test_global_address_limit_stops_floods(limits_on):
    codes = [client.get("/public-info").status_code for _ in range(301)]
    assert codes[:300] == [200] * 300
    assert codes[300] == 429


def test_registration_modes(monkeypatch):
    make_user_info()   # make sure at least one account exists

    def register(**extra):
        body = {"email": f"{uuid.uuid4().hex[:8]}@test.com", "password": "correct-horse-battery", **extra}
        return client.post("/auth/register", json=body)

    monkeypatch.setattr(security, "REGISTRATION_MODE", "closed")
    assert register().status_code == 403
    monkeypatch.setattr(security, "REGISTRATION_MODE", "first_user")
    assert register().status_code == 403          # an account already exists
    monkeypatch.setattr(security, "REGISTRATION_MODE", "invite")
    monkeypatch.setattr(security, "INVITE_CODE", "a-long-invite-code-123")
    assert register().status_code == 403
    assert register(invite_code="wrong-code").status_code == 403
    assert register(invite_code="a-long-invite-code-123").status_code == 201


def test_personal_edition_hides_enterprise_routes(monkeypatch):
    u = make_user_info()
    created = client.post("/orgs", json={"name": "Acme"}, headers=u["h"])
    assert created.status_code == 201
    org = created.json()["id"]
    assert client.get(f"/orgs/{org}/members", headers=u["h"]).status_code == 200
    monkeypatch.setattr(security, "EDITION", "personal")
    assert client.get("/orgs", headers=u["h"]).status_code == 404
    assert client.get(f"/orgs/{org}/members", headers=u["h"]).status_code == 404
    assert client.get("/documents", headers=u["h"]).status_code == 200


def test_public_info_reports_the_installation_settings(monkeypatch):
    assert client.get("/public-info").json() == {"edition": "enterprise", "demo": False, "registration": "open"}
    monkeypatch.setattr(security, "EDITION", "personal")
    monkeypatch.setattr(security, "DEMO_MODE", True)
    monkeypatch.setattr(security, "REGISTRATION_MODE", "closed")
    assert client.get("/public-info").json() == {"edition": "personal", "demo": True, "registration": "closed"}


def test_pdf_uploads_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(rag, "ALLOW_PDF", False)
    with pytest.raises(ValueError):
        rag.extract_text("report.pdf", b"%PDF-1.4")
    assert rag.extract_text("notes.txt", b"hello") == "hello"


def test_client_address_trusts_the_proxy_only_when_told_to(monkeypatch):
    request = Request({
        "type": "http", "method": "GET", "path": "/", "query_string": b"",
        "headers": [(b"x-forwarded-for", b"1.2.3.4, 9.9.9.9")],
        "client": ("10.0.0.1", 1234),
    })
    monkeypatch.setattr(ratelimit, "TRUST_PROXY", False)
    assert ratelimit.client_ip(request) == "10.0.0.1"
    monkeypatch.setattr(ratelimit, "TRUST_PROXY", True)
    assert ratelimit.client_ip(request) == "9.9.9.9"


def test_demo_provider_switch(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    assert isinstance(providers.get_provider(), providers.FakeProvider)
    monkeypatch.setenv("MODEL_PROVIDER", "ollama")
    assert isinstance(providers.get_provider(), providers.OllamaProvider)
