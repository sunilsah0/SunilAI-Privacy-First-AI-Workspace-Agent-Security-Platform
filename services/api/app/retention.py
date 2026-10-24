from sqlalchemy import select, text
from .db import SessionLocal, set_rls_user
from .models import User, UserSettings

DELETE_OLD = text("""
    DELETE FROM conversations c
    WHERE c.owner_id = :uid
      AND GREATEST(c.created_at,
                   COALESCE((SELECT max(m.created_at) FROM messages m WHERE m.conversation_id = c.id),
                            c.created_at))
          < now() - make_interval(days => :days)
""")

def run_retention() -> int:
    """Runs as the LIMITED app account. For each person it acts AS that person,
    so Row-Level Security applies and the job cannot touch anyone else's data."""
    with SessionLocal() as db:
        user_ids = db.scalars(select(User.id)).all()
    deleted = 0
    for uid in user_ids:
        with SessionLocal() as db:
            set_rls_user(db, uid)
            days = db.scalar(select(UserSettings.conversation_retention_days)
                             .where(UserSettings.owner_id == uid))
            if days:
                deleted += db.execute(DELETE_OLD, {"uid": uid, "days": days}).rowcount
                db.commit()
    return deleted