"""chunks with pgvector

Revision ID: 85bc89a8f0f0
Revises: f5a16ac89b57
Create Date: 2026-10-23 13:41:24.580321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85bc89a8f0f0'
down_revision: Union[str, Sequence[str], None] = 'f5a16ac89b57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
    CREATE TABLE chunks (
        id uuid PRIMARY KEY,
        document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        position integer NOT NULL,
        content text NOT NULL,
        embedding vector(768) NOT NULL,
        UNIQUE (document_id, position)
    )
    """)
    op.execute("CREATE INDEX ix_chunks_document_id ON chunks (document_id)")
    op.execute("CREATE INDEX ix_chunks_owner_id ON chunks (owner_id)")

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON chunks TO verity_app")
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chunks FORCE ROW LEVEL SECURITY")
    op.execute("""
    CREATE POLICY chunks_owner_only ON chunks
      USING      (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
      WITH CHECK (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks")
