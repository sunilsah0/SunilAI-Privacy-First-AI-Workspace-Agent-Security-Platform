import uuid
import pytest
from services.api.app.main import app
from services.api.app.providers import get_provider, FakeProvider
from tests.helpers import client, make_user

class Recorder:
    def __init__(self):
        self.calls = []
    def chat(self, messages, model):
        self.calls.append(messages)
        return "ok"

class Broken:
    def chat(self, messages, model):
        raise ConnectionError("model is down")

@pytest.fixture(autouse=True)
def fake_ai():
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    yield
    app.dependency_overrides.clear()

def new_conv(h, title="chat"):
    return client.post("/conversations", json={"title": title}, headers=h).json()["id"]

def test_chat_saves_messages_in_order():
    a = make_user(); cid = new_conv(a)
    r = client.post(f"/conversations/{cid}/messages", json={"content": "hi"}, headers=a)
    assert r.status_code == 200
    msgs = client.get(f"/conversations/{cid}", headers=a).json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "hi"

def test_user_b_cannot_read_post_or_delete_user_a_conversation():
    a, b = make_user(), make_user()
    cid = new_conv(a)
    assert client.get(f"/conversations/{cid}", headers=b).status_code == 404
    assert client.post(f"/conversations/{cid}/messages", json={"content": "x"}, headers=b).status_code == 404
    assert client.delete(f"/conversations/{cid}", headers=b).status_code == 404
    assert client.get(f"/conversations/{cid}", headers=a).status_code == 200

def test_conversation_list_is_private():
    a, b = make_user(), make_user()
    new_conv(a, "A-only-title")
    titles = [c["title"] for c in client.get("/conversations", headers=b).json()]
    assert "A-only-title" not in titles

def test_foreign_and_nonexistent_look_identical():
    a, b = make_user(), make_user()
    real, fake = new_conv(a), str(uuid.uuid4())
    r1 = client.get(f"/conversations/{real}", headers=b)
    r2 = client.get(f"/conversations/{fake}", headers=b)
    assert (r1.status_code, r1.json()) == (r2.status_code, r2.json())

def test_ai_prompt_never_contains_another_users_text():
    a, b = make_user(), make_user()
    rec = Recorder()
    app.dependency_overrides[get_provider] = lambda: rec
    ca, cb = new_conv(a), new_conv(b)
    client.post(f"/conversations/{ca}/messages", json={"content": "alpha-secret-123"}, headers=a)
    rec.calls.clear()
    client.post(f"/conversations/{cb}/messages", json={"content": "hello"}, headers=b)
    assert len(rec.calls) == 1
    assert "alpha-secret-123" not in str(rec.calls)

def test_ai_is_not_even_called_for_a_foreign_conversation():
    a, b = make_user(), make_user()
    rec = Recorder()
    app.dependency_overrides[get_provider] = lambda: rec
    ca = new_conv(a)
    client.post(f"/conversations/{ca}/messages", json={"content": "x"}, headers=b)
    assert rec.calls == []

def test_model_down_returns_503_and_saves_nothing():
    a = make_user(); cid = new_conv(a)
    app.dependency_overrides[get_provider] = lambda: Broken()
    r = client.post(f"/conversations/{cid}/messages", json={"content": "hi"}, headers=a)
    assert r.status_code == 503
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    assert client.get(f"/conversations/{cid}", headers=a).json()["messages"] == []