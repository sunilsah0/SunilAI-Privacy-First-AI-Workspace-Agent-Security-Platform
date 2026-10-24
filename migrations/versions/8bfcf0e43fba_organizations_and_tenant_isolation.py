"""organizations and tenant isolation

Revision ID: 8bfcf0e43fba
Revises: 038e2b271c28
Create Date: 2026-10-24 14:25:57.889785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bfcf0e43fba'
down_revision: Union[str, Sequence[str], None] = '038e2b271c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ADMINS = "('owner','security_admin')"
NON_OWNER_ROLES = "('security_admin','team_admin','member','auditor')"
CONTENT_ROLES = "('owner','team_admin','member')"

def upgrade() -> None:
    # ---- tables ----
    op.execute("""
    CREATE TABLE organizations (
        id uuid PRIMARY KEY,
        name varchar(200) NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    op.execute("""
    CREATE TABLE memberships (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role varchar(30) NOT NULL CHECK (role IN ('owner','security_admin','team_admin','member','auditor')),
        status varchar(20) NOT NULL CHECK (status IN ('active','suspended')),
        created_at timestamptz NOT NULL,
        UNIQUE (org_id, user_id)
    )""")
    op.execute("CREATE INDEX ix_memberships_user_id ON memberships (user_id)")
    op.execute("""
    CREATE TABLE org_documents (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        created_by uuid NOT NULL REFERENCES users(id),
        title varchar(200) NOT NULL,
        content text NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    op.execute("CREATE INDEX ix_org_documents_org_id ON org_documents (org_id)")
    op.execute("""
    CREATE TABLE org_audit_events (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        actor_id uuid NOT NULL REFERENCES users(id),
        event varchar(50) NOT NULL,
        detail varchar(300) NOT NULL,
        created_at timestamptz NOT NULL
    )""")
    op.execute("CREATE INDEX ix_org_audit_events_org_id ON org_audit_events (org_id)")

    # ---- small trusted helper functions ----
    op.execute("""
    CREATE FUNCTION app_current_user() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$ SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid $$
    """)
    op.execute("""
    CREATE FUNCTION app_org_role(org uuid) RETURNS text
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp
    AS $$ SELECT role FROM memberships
          WHERE org_id = org AND user_id = app_current_user() AND status = 'active' $$
    """)
    op.execute("""
    CREATE FUNCTION create_organization(org_name text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp
    AS $$
    DECLARE
        uid uuid := app_current_user();
        new_id uuid := gen_random_uuid();
    BEGIN
        IF uid IS NULL THEN
            RAISE EXCEPTION 'not authenticated';
        END IF;
        INSERT INTO organizations (id, name, created_at) VALUES (new_id, org_name, now());
        INSERT INTO memberships (id, org_id, user_id, role, status, created_at)
        VALUES (gen_random_uuid(), new_id, uid, 'owner', 'active', now());
        RETURN new_id;
    END
    $$
    """)
    for fn in ("app_current_user()", "app_org_role(uuid)", "create_organization(text)"):
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO verity_app")

    # ---- what the app account may do ----
    op.execute("GRANT SELECT ON organizations TO verity_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON memberships TO verity_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON org_documents TO verity_app")
    op.execute("GRANT SELECT, INSERT ON org_audit_events TO verity_app")      # append-only

    # ---- Row-Level Security ----
    for t in ("organizations", "memberships", "org_documents", "org_audit_events"):
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")

    policies = [
        # organizations: you only see orgs you are an active member of
        "CREATE POLICY org_select ON organizations FOR SELECT USING (app_org_role(id) IS NOT NULL)",

        # memberships: members see colleagues; only admins change things
        "CREATE POLICY memberships_select ON memberships FOR SELECT USING (app_org_role(org_id) IS NOT NULL)",
        f"""CREATE POLICY memberships_insert ON memberships FOR INSERT WITH CHECK (
              app_org_role(org_id) = 'owner'
              OR (app_org_role(org_id) = 'security_admin' AND role IN {NON_OWNER_ROLES}))""",
        f"""CREATE POLICY memberships_update ON memberships FOR UPDATE
              USING (app_org_role(org_id) = 'owner'
                     OR (app_org_role(org_id) = 'security_admin' AND role <> 'owner'))
              WITH CHECK (app_org_role(org_id) = 'owner'
                     OR (app_org_role(org_id) = 'security_admin' AND role IN {NON_OWNER_ROLES}))""",

        # shared documents: content roles only. Admin roles get NO content access.
        f"CREATE POLICY org_docs_select ON org_documents FOR SELECT USING (app_org_role(org_id) IN {CONTENT_ROLES})",
        f"""CREATE POLICY org_docs_insert ON org_documents FOR INSERT
              WITH CHECK (app_org_role(org_id) IN {CONTENT_ROLES} AND created_by = app_current_user())""",
        """CREATE POLICY org_docs_delete ON org_documents FOR DELETE
              USING (app_org_role(org_id) IN ('owner','team_admin')
                     OR (app_org_role(org_id) = 'member' AND created_by = app_current_user()))""",

        # org audit log: readable by owner / security_admin / auditor, append-only
        """CREATE POLICY org_audit_select ON org_audit_events FOR SELECT
              USING (app_org_role(org_id) IN ('owner','security_admin','auditor'))""",
        """CREATE POLICY org_audit_insert ON org_audit_events FOR INSERT
              WITH CHECK (app_org_role(org_id) IS NOT NULL AND actor_id = app_current_user())""",
    ]
    for p in policies:
        op.execute(p)


def downgrade() -> None:
    for t in ("org_audit_events", "org_documents", "memberships", "organizations"):
        op.execute(f"DROP TABLE IF EXISTS {t}")
    op.execute("DROP FUNCTION IF EXISTS create_organization(text)")
    op.execute("DROP FUNCTION IF EXISTS app_org_role(uuid)")
    op.execute("DROP FUNCTION IF EXISTS app_current_user()")