import { useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../api";
import {
  ROLE_HELP, assignableRoles, canDeleteAnyDoc, canManageMembers,
  canUseDocs, canViewAudit, canViewMembers,
} from "../roles";

export type Org = { id: string; name: string; role: string };
type Member = { user_id: string; email: string; role: string; status: string };
type SharedDoc = { id: string; title: string; created_by: string | null };
type AuditRow = { time: string; actor: string; event: string; detail: string };

export default function OrgPanel({ org, me }: { org: Org; me: { id: string } }) {
  const role = org.role;
  const [members, setMembers] = useState<Member[]>([]);
  const [docs, setDocs] = useState<SharedDoc[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [openDoc, setOpenDoc] = useState<{ title: string; content: string } | null>(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const [email, setEmail] = useState("");
  const [newRole, setNewRole] = useState("member");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    const calls: Promise<void>[] = [];
    if (canViewMembers(role)) calls.push(api<Member[]>(`/orgs/${org.id}/members`).then(setMembers));
    if (canUseDocs(role)) calls.push(api<SharedDoc[]>(`/orgs/${org.id}/documents`).then(setDocs));
    if (canViewAudit(role)) calls.push(api<AuditRow[]>(`/orgs/${org.id}/audit`).then(setAudit));
    Promise.all(calls).catch((e) => setError(errorText(e)));
  }, [org.id, role, reloadKey]);

  async function act(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      setReloadKey((k) => k + 1);
    } catch (e) {
      setError(errorText(e));
    }
  }

  function addMember(e: FormEvent) {
    e.preventDefault();
    void act(async () => {
      await api(`/orgs/${org.id}/members`, { method: "POST", body: { email, role: newRole } });
      setEmail("");
    });
  }

  function addDoc(e: FormEvent) {
    e.preventDefault();
    void act(async () => {
      await api(`/orgs/${org.id}/documents`, { method: "POST", body: { title, content } });
      setTitle("");
      setContent("");
    });
  }

  async function open(id: string) {
    setError("");
    try {
      setOpenDoc(await api<{ title: string; content: string }>(`/orgs/${org.id}/documents/${id}`));
    } catch (e) {
      setError(errorText(e));
    }
  }

  function patchMember(userId: string, body: { role?: string; status?: string }) {
    void act(() => api(`/orgs/${org.id}/members/${userId}`, { method: "PATCH", body }));
  }

  return (
    <div>
      <div className="card">
        <h2>{org.name}</h2>
        <p>Your role: <strong>{role}</strong></p>
        <p className="muted">{ROLE_HELP[role]}</p>
        <p className="muted">
          No role in this organization can read another person's private chats, documents or memory.
        </p>
      </div>
      {error && <p className="error" role="alert">{error}</p>}

      {canViewMembers(role) && (
        <div className="card">
          <h3>Members</h3>
          <table>
            <thead><tr><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {members.map((m) => {
                const manageable = canManageMembers(role) && m.user_id !== me.id &&
                  !(role === "security_admin" && m.role === "owner");
                return (
                  <tr key={m.user_id}>
                    <td>{m.email}{m.user_id === me.id && " (you)"}</td>
                    <td>
                      {manageable ? (
                        <select
                          aria-label={`Role for ${m.email}`}
                          value={m.role}
                          onChange={(e) => patchMember(m.user_id, { role: e.target.value })}
                        >
                          {assignableRoles(role).map((r) => <option key={r} value={r}>{r}</option>)}
                        </select>
                      ) : m.role}
                    </td>
                    <td>{m.status}</td>
                    <td>
                      {manageable && (
                        <button
                          className="small"
                          onClick={() => patchMember(m.user_id, { status: m.status === "active" ? "suspended" : "active" })}
                        >
                          {m.status === "active" ? "Suspend" : "Reactivate"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {canManageMembers(role) && (
            <form onSubmit={addMember}>
              <h4>Add a member</h4>
              <p className="muted">The person must already have an account.</p>
              <div className="row">
                <label htmlFor="m-email" className="sr-only">Email</label>
                <input id="m-email" type="email" required placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <label htmlFor="m-role" className="sr-only">Role</label>
                <select id="m-role" value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                  {assignableRoles(role).map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
                <button>Add</button>
              </div>
            </form>
          )}
        </div>
      )}

      {canUseDocs(role) ? (
        <div className="card">
          <h3>Shared documents</h3>
          {docs.length === 0 && <p className="muted">No shared documents yet.</p>}
          <ul className="list">
            {docs.map((d) => (
              <li key={d.id}>
                <button className="link" onClick={() => void open(d.id)}>{d.title}</button>
                {(canDeleteAnyDoc(role) || d.created_by === me.id) && (
                  <button
                    className="small"
                    aria-label={`Delete ${d.title}`}
                    onClick={() => void act(async () => {
                      await api(`/orgs/${org.id}/documents/${d.id}`, { method: "DELETE" });
                      setOpenDoc(null);
                    })}
                  >
                    Delete
                  </button>
                )}
              </li>
            ))}
          </ul>
          {openDoc && (
            <div className="card">
              <strong>{openDoc.title}</strong>
              <p style={{ whiteSpace: "pre-wrap" }}>{openDoc.content}</p>
            </div>
          )}
          <form onSubmit={addDoc}>
            <h4>Add a shared document</h4>
            <label htmlFor="d-title">Title</label>
            <input id="d-title" type="text" required value={title} onChange={(e) => setTitle(e.target.value)} />
            <label htmlFor="d-content">Text</label>
            <textarea id="d-content" rows={4} required value={content} onChange={(e) => setContent(e.target.value)} />
            <p><button>Share with the organization</button></p>
          </form>
        </div>
      ) : (
        <div className="card">
          <h3>Shared documents</h3>
          <p className="muted">Your role manages people and policy. It does not include access to document content.</p>
        </div>
      )}

      {canViewAudit(role) && (
        <div className="card">
          <h3>Organization audit log</h3>
          <p className="muted">Who did what. Never document text.</p>
          <table>
            <thead><tr><th>Time</th><th>Who</th><th>Event</th><th>Detail</th></tr></thead>
            <tbody>
              {audit.map((a, i) => (
                <tr key={`${a.time}-${i}`}>
                  <td>{new Date(a.time).toLocaleString()}</td><td>{a.actor}</td><td>{a.event}</td><td>{a.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}