import uuid
from tests.helpers import client, make_user

def make_doc(headers, title="Secret plan", content="my private text"):
    r = client.post("/documents", json={"title": title, "content": content}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]

def test_owner_can_read_own_document():
    a = make_user()
    doc_id = make_doc(a)
    r = client.get(f"/documents/{doc_id}", headers=a)
    assert r.status_code == 200
    assert r.json()["content"] == "my private text"

def test_user_b_cannot_read_user_a_document():
    a, b = make_user(), make_user()
    doc_id = make_doc(a)
    r = client.get(f"/documents/{doc_id}", headers=b)
    assert r.status_code == 404
    assert "private" not in r.text

def test_list_shows_only_own_documents():
    a, b = make_user(), make_user()
    make_doc(a, title="A-only")
    titles_seen_by_b = [d["title"] for d in client.get("/documents", headers=b).json()]
    assert "A-only" not in titles_seen_by_b

def test_user_b_cannot_delete_user_a_document():
    a, b = make_user(), make_user()
    doc_id = make_doc(a)
    assert client.delete(f"/documents/{doc_id}", headers=b).status_code == 404
    assert client.get(f"/documents/{doc_id}", headers=a).status_code == 200  # still there

def test_foreign_and_nonexistent_look_identical():
    a, b = make_user(), make_user()
    real_id = make_doc(a)
    fake_id = str(uuid.uuid4())
    r1 = client.get(f"/documents/{real_id}", headers=b)
    r2 = client.get(f"/documents/{fake_id}", headers=b)
    assert (r1.status_code, r1.json()) == (r2.status_code, r2.json())

def test_documents_require_login():
    assert client.get("/documents").status_code in (401, 403)