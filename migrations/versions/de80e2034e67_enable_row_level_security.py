"""enable row level security

Revision ID: de80e2034e67
Revises: 168a97a46b95
Create Date: 2026-10-22 15:21:58.382947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
import re

APP_PASSWORD = os.getenv("APP_DB_PASSWORD", "app_dev_password_change_me")
if not re.fullmatch(r"[A-Za-z0-9_]{12,}", APP_PASSWORD):
    raise RuntimeError("APP_DB_PASSWORD must be at least 12 letters, digits or underscores")

# revision identifiers, used by Alembic.
revision: str = 'de80e2034e67'
down_revision: Union[str, Sequence[str], None] = '168a97a46b95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'verity_app') THEN
        CREATE ROLE verity_app LOGIN PASSWORD '{APP_PASSWORD}'
          NOSUPERUSER NOBYPASSRLS;
      END IF;
    END $$;
    """)
    op.execute("GRANT USAGE ON SCHEMA public TO verity_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON users, documents TO verity_app")

    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE documents FORCE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY documents_owner_only ON documents
      USING      (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
      WITH CHECK (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS documents_owner_only ON documents")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON users, documents FROM verity_app")
