export const ALL_ROLES = ["owner", "security_admin", "team_admin", "member", "auditor"] as const;

// UI hints only. The server is what actually enforces these rules.
export const canManageMembers = (r: string) => r === "owner" || r === "security_admin";
export const canViewMembers = (r: string) => ["owner", "security_admin", "team_admin", "auditor"].includes(r);
export const canUseDocs = (r: string) => ["owner", "team_admin", "member"].includes(r);
export const canViewAudit = (r: string) => ["owner", "security_admin", "auditor"].includes(r);
export const canDeleteAnyDoc = (r: string) => r === "owner" || r === "team_admin";

export function assignableRoles(r: string): string[] {
  if (r === "owner") return [...ALL_ROLES];
  if (r === "security_admin") return ALL_ROLES.filter((x) => x !== "owner");
  return [];
}

export const ROLE_HELP: Record<string, string> = {
  owner: "Manage members and roles, use shared documents, read the audit log.",
  security_admin: "Manage members (not owners) and read the audit log. No access to document content.",
  team_admin: "Use and moderate shared documents, see the member list.",
  member: "Read and add shared documents, delete your own.",
  auditor: "Read-only: member list and audit log. No access to document content.",
};