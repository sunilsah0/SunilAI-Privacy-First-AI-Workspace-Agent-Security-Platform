"""break glass, retention, account deletion

Revision ID: 4543c15c4bed
Revises: 8bfcf0e43fba
Create Date: 2026-10-24 19:05:16.513973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4543c15c4bed'
down_revision: Union[str, Sequence[str], None] = '8bfcf0e43fba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- 1. personal settings (retention) ----
    op.execute("""
    CREATE TABLE user_settings (
        owner_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        conversation_retention_days integer
            CHECK (conversation_retention_days IS NULL OR conversation_retention_days >= 1)
    )""")

    # ---- 2. account deletion: shared records stay, the author is blanked ----
    for table, col in (("org_documents", "created_by"), ("org_audit_events", "actor_id")):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL")
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_{col}_fkey")
        op.execute(f"""ALTER TABLE {table} ADD CONSTRAINT {table}_{col}_fkey
                       FOREIGN KEY ({col}) REFERENCES users(id) ON DELETE SET NULL""")

    # ---- 3. break-glass tables ----
    op.execute("""
    CREATE TABLE break_glass_grants (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        requester_id uuid REFERENCES users(id) ON DELETE SET NULL,
        target_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        approver_id uuid REFERENCES users(id) ON DELETE SET NULL,
        reason varchar(500) NOT NULL CHECK (char_length(reason) >= 20),
        duration_minutes integer NOT NULL CHECK (duration_minutes BETWEEN 5 AND 60),
        status varchar(20) NOT NULL CHECK (status IN ('pending','approved','denied','revoked')),
        requested_at timestamptz NOT NULL,
        decided_at timestamptz,
        expires_at timestamptz,
        CHECK (expires_at IS NULL OR (decided_at IS NOT NULL AND expires_at <= decided_at + interval '61 minutes'))
    )""")
    op.execute("CREATE INDEX ix_bg_grants_org_id ON break_glass_grants (org_id)")
    op.execute("CREATE INDEX ix_bg_grants_lookup ON break_glass_grants (requester_id, target_user_id)")
    op.execute("""
    CREATE TABLE break_glass_access_log (
        id uuid PRIMARY KEY,
        grant_id uuid NOT NULL REFERENCES break_glass_grants(id) ON DELETE CASCADE,
        org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        accessor_id uuid REFERENCES users(id) ON DELETE SET NULL,
        target_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
        document_id uuid,
        action varchar(20) NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    op.execute("CREATE INDEX ix_bg_log_org_id ON break_glass_access_log (org_id)")
    op.execute("CREATE INDEX ix_bg_log_target ON break_glass_access_log (target_user_id)")

    # ---- 4. helper: is this person a member of this org? (only answers to org members) ----
    op.execute("""
    CREATE FUNCTION app_user_in_org(org uuid, uid uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp
    AS $$ SELECT app_org_role(org) IS NOT NULL
            AND EXISTS (SELECT 1 FROM memberships WHERE org_id = org AND user_id = uid) $$
    """)
    op.execute("REVOKE ALL ON FUNCTION app_user_in_org(uuid, uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION app_user_in_org(uuid, uuid) TO verity_app")

    # ---- 5. what the app account may do ----
    op.execute("GRANT SELECT, INSERT, UPDATE ON user_settings TO verity_app")
    op.execute("GRANT SELECT, INSERT ON break_glass_grants TO verity_app")
    # Only these four columns can change. Who asked, about whom, and why can never be edited.
    op.execute("GRANT UPDATE (status, approver_id, decided_at, expires_at) ON break_glass_grants TO verity_app")
    op.execute("GRANT SELECT, INSERT ON break_glass_access_log TO verity_app")   # append-only

    # ---- 6. Row-Level Security ----
    for t in ("user_settings", "break_glass_grants", "break_glass_access_log", "users"):
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    policies = [
        # settings: owner only
        """CREATE POLICY user_settings_owner_only ON user_settings
             USING      (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
             WITH CHECK (owner_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)""",

        # users: login needs to look people up and register needs to add, but only YOU can change or delete YOU
        "CREATE POLICY users_select ON users FOR SELECT USING (true)",
        "CREATE POLICY users_insert ON users FOR INSERT WITH CHECK (true)",
        "CREATE POLICY users_update ON users FOR UPDATE USING (id = app_current_user()) WITH CHECK (id = app_current_user())",
        "CREATE POLICY users_delete ON users FOR DELETE USING (id = app_current_user())",

        # grants: who can see them
        """CREATE POLICY bg_grants_select ON break_glass_grants FOR SELECT USING (
             requester_id = app_current_user()
             OR app_org_role(org_id) IN ('owner','auditor')
             OR (target_user_id = app_current_user() AND status = 'approved'))""",
        # grants: who can ask. The target MUST belong to the same organization.
        """CREATE POLICY bg_grants_insert ON break_glass_grants FOR INSERT WITH CHECK (
             requester_id = app_current_user()
             AND app_org_role(org_id) IN ('owner','security_admin')
             AND status = 'pending' AND approver_id IS NULL
             AND target_user_id <> requester_id
             AND app_user_in_org(org_id, target_user_id))""",
        # grants: only owners decide, and never their own request (two-person rule)
        """CREATE POLICY bg_grants_update ON break_glass_grants FOR UPDATE
             USING (app_org_role(org_id) = 'owner' AND status IN ('pending','approved'))
             WITH CHECK (
               (status = 'revoked' AND app_org_role(org_id) = 'owner')
               OR (status IN ('approved','denied')
                   AND approver_id = app_current_user() AND approver_id <> requester_id))""",

        # access log: the accessor, the person being accessed, and org owners/auditors can read it
        """CREATE POLICY bg_log_select ON break_glass_access_log FOR SELECT USING (
             accessor_id = app_current_user()
             OR target_user_id = app_current_user()
             OR app_org_role(org_id) IN ('owner','auditor'))""",
        """CREATE POLICY bg_log_insert ON break_glass_access_log FOR INSERT WITH CHECK (
             accessor_id = app_current_user()
             AND EXISTS (SELECT 1 FROM break_glass_grants g
                         WHERE g.id = grant_id AND g.requester_id = app_current_user()
                           AND g.status = 'approved' AND g.expires_at > now()))""",

        # THE break-glass rule: read-only, only for the requester, only while approved and unexpired,
        # and only while the requester still holds an admin role
        """CREATE POLICY documents_break_glass_read ON documents FOR SELECT USING (
             EXISTS (SELECT 1 FROM break_glass_grants g
                     WHERE g.requester_id = app_current_user()
                       AND g.target_user_id = documents.owner_id
                       AND g.status = 'approved'
                       AND g.expires_at > now()
                       AND app_org_role(g.org_id) IN ('owner','security_admin')))""",
    ]
    for p in policies:
        op.execute(p)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS documents_break_glass_read ON documents")
    for t in ("break_glass_access_log", "break_glass_grants", "user_settings"):
        op.execute(f"DROP TABLE IF EXISTS {t}")
    op.execute("DROP FUNCTION IF EXISTS app_user_in_org(uuid, uuid)")
    for p in ("users_select", "users_insert", "users_update", "users_delete"):
        op.execute(f"DROP POLICY IF EXISTS {p} ON users")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    # The foreign keys on org_documents / org_audit_events are left as they are.