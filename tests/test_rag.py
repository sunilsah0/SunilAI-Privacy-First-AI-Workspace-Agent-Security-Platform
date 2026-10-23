import pytest
from sqlalchemy import text
from services.api.app.db import engine
from services.api.app.main import app
from services.api.app.providers import get_provider, FakeProvider
from tests.helpers import client, make_user

class RecordingFake(FakeProvider):
    def __init__(self):
        self.calls = []
    def chat(self, messages, model):
        self.calls.append(messages)
        return "ok"

class BrokenEmbed(FakeProvider):
    def embed(self, texts):
        raise ConnectionError("embedding model is down")

@pytest.fixture(autouse=True)
def fake_ai():
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    yield
    app.dependency_overrides.clear()

def upload(h, body, name="notes.txt"):
    return client.post("/documents/upload",
                       files={"file": (name, body.encode(), "text/plain")}, headers=h)

def search(h, q, k=4):
    return client.post("/search", json={"query": q, "k": k}, headers=h)

def test_upload_then_find_own_document():
    a = make_user()
    assert upload(a, "the banana smoothie uses frozen banana").status_code == 201
    hits = search(a, "banana").json()
    assert hits and "banana" in hits[0]["text"]

def test_search_never_returns_another_users_chunks():
    a, b = make_user(), make_user()
    upload(a, "zebra-secret-777 launch codes")
    upload(b, "apple pie recipe")
    r = search(b, "zebra-secret-777", k=10)
    assert r.status_code == 200
    assert "zebra-secret-777" not in r.text

def test_ai_prompt_contains_only_own_document_text():
    a, b = make_user(), make_user()
    upload(a, "zebra-secret-777 launch codes")
    upload(b, "apple pie recipe")
    rec = RecordingFake()
    app.dependency_overrides[get_provider] = lambda: rec
    cid = client.post("/conversations", json={"title": "t"}, headers=b).json()["id"]
    r = client.post(f"/conversations/{cid}/messages",
                    json={"content": "tell me about pie", "use_documents": True}, headers=b)
    assert r.status_code == 200
    assert "zebra-secret-777" not in str(rec.calls)
    assert "apple pie" in str(rec.calls)

def test_chunks_are_hidden_without_identity():
    a = make_user()
    upload(a, "some private text")
    with engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM chunks")).scalar() == 0

def test_deleting_document_deletes_its_chunks():
    a = make_user()
    doc_id = upload(a, "temporary banana notes").json()["id"]
    assert client.delete(f"/documents/{doc_id}", headers=a).status_code == 204
    assert search(a, "banana").json() == []

def test_unsupported_file_type_rejected():
    a = make_user()
    assert upload(a, "MZ fake program", name="virus.exe").status_code == 400

def test_too_large_file_rejected():
    a = make_user()
    assert upload(a, "a" * (5 * 1024 * 1024 + 1)).status_code == 413

def test_embedding_model_down_saves_nothing():
    a = make_user()
    app.dependency_overrides[get_provider] = lambda: BrokenEmbed()
    assert upload(a, "hello world").status_code == 503
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    assert client.get("/documents", headers=a).json() == []