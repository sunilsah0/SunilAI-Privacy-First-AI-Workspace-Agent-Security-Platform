import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

# The API connects as the LIMITED user, never the owner/superuser
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://verity_app:app_dev_password_change_me@127.0.0.1:5433/verity",
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

@event.listens_for(Session, "after_begin")
def apply_rls_context(session, transaction, connection):
    """Runs at the start of EVERY transaction: tell Postgres who is asking.
    The 'true' means the value lasts only for this transaction, so a pooled
    connection can never carry one user's identity to the next request."""
    uid = session.info.get("user_id", "")
    connection.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"), {"u": uid}
    )

def set_rls_user(db: Session, user_id) -> None:
    db.info["user_id"] = str(user_id)
    db.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(user_id)}
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()