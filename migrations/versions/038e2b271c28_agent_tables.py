"""agent tables

Revision ID: 038e2b271c28
Revises: 85bc89a8f0f0
Create Date: 2026-10-23 14:47:55.270464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '038e2b271c28'
down_revision: Union[str, Sequence[str], None] = '85bc89a8f0f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE tool_permissions (
        id uuid PRIMARY KEY,
        owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        tool varchar(100) NOT NULL,
        enabled boolean NOT NULL,
        UNIQUE (owner_id, tool)
    )""")
    op.execute("""
    CREATE TABLE pending_actions (
        id uuid PRIMARY KEY,
        owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        tool varchar(100) NOT NULL,
        args jsonb NOT NULL,
        status varchar(20) NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    op.execute("""
    CREATE TABLE audit_events (
        id uuid PRIMARY KEY,
        owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        event varchar(50) NOT NULL,
        tool varchar(100) NOT NULL,
        outcome varchar(30) NOT NULL,
        reason varchar(500) NOT NULL,
        target varchar(100) NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    for t in ("tool_permissions", "pending_actions", "audit_events"):
        op.execute(f"CREATE INDEX ix_{t}_owner_id ON {t} (owner_id)")

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tool_permissions, pending_actions TO verity_app")
    op.execute("GRANT SELECT, INSERT ON audit_events TO verity_app")   # append-only!

    for t in ("tool_permissions", "pending_actions", "audit_events"):
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
        CREATE POLICY {t}_owner_only ON {t}
          USING      (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
          WITH CHECK (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
        """)


def downgrade() -> None:
    for t in ("audit_events", "pending_actions", "tool_permissions"):
        op.execute(f"DROP TABLE IF EXISTS {t}")
