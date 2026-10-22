import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from services.api.app.db import DATABASE_URL, engine
from tests.helpers import client, make_user

def user_id(headers):
    return client.get("/me", headers=headers).json()["id"]

def make_doc(headers):
    r = client.post("/documents", json={"title": "t", "content": "secret"}, headers=headers)
    return r.json()["id"]

def as_user(conn, uid):
    conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": uid})

def test_app_role_cannot_bypass_rls():
    with engine.connect() as c:
        row = c.execute(text(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )).one()
    assert row == (False, False)

def test_no_identity_means_no_rows():
    a = make_user(); make_doc(a)
    with engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM documents")).scalar() == 0

def test_select_star_still_hides_other_users_rows():
    a, b = make_user(), make_user()
    make_doc(a)
    with engine.begin() as c:
        as_user(c, user_id(b))
        # No WHERE clause at all, like a developer who forgot the check
        assert c.execute(text("SELECT count(*) FROM documents")).scalar() == 0

def test_cannot_insert_document_for_someone_else():
    a, b = make_user(), make_user()
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            as_user(c, user_id(a))
            c.execute(text(
                "INSERT INTO documents (id, owner_id, title, content, created_at) "
                "VALUES (gen_random_uuid(), :o, 'x', 'y', now())"
            ), {"o": user_id(b)})

def test_pooled_connection_does_not_leak_identity():
    a = make_user(); make_doc(a)
    one_conn = create_engine(DATABASE_URL, pool_size=1, max_overflow=0)  # forces reuse
    with one_conn.begin() as c:
        as_user(c, user_id(a))
        assert c.execute(text("SELECT count(*) FROM documents")).scalar() >= 1
    with one_conn.begin() as c:  # same physical connection, new transaction
        assert c.execute(text("SELECT count(*) FROM documents")).scalar() == 0
    one_conn.dispose()