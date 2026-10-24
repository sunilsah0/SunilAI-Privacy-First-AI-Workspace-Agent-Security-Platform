from fastapi import HTTPException
from sqlalchemy import select
from .models import Membership, OrgAuditEvent

ROLES = ("owner", "security_admin", "team_admin", "member", "auditor")
CAN_MANAGE_MEMBERS = {"owner", "security_admin"}
CAN_VIEW_MEMBERS = {"owner", "security_admin", "team_admin", "auditor"}
CAN_VIEW_AUDIT = {"owner", "security_admin", "auditor"}
CAN_USE_SHARED_DOCS = {"owner", "team_admin", "member"}
CAN_DELETE_ANY_SHARED_DOC = {"owner", "team_admin"}
ASSIGNABLE_BY = {
    "owner": set(ROLES),
    "security_admin": {"security_admin", "team_admin", "member", "auditor"},
}

def require_role(db, user_id, org_id, allowed: set[str]) -> str:
    """Not a member (or suspended) -> 404, so outsiders learn nothing. Wrong role -> 403."""
    m = db.scalar(select(Membership).where(
        Membership.org_id == org_id, Membership.user_id == user_id, Membership.status == "active"))
    if m is None:
        raise HTTPException(404, "Organization not found")
    if m.role not in allowed:
        raise HTTPException(403, "Your role does not allow this")
    return m.role

def org_audit(db, org_id, actor_id, event: str, detail: str) -> None:
    """Never put document text or emails here. Only ids and role names."""
    db.add(OrgAuditEvent(org_id=org_id, actor_id=actor_id, event=event, detail=detail[:300]))