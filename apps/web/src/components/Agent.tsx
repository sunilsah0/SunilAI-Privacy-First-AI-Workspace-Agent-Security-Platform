import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../api";

type Perm = {
  tool: string; description: string; enabled: boolean;
  requires_approval: boolean; needs_network: boolean; blocked_by_network_policy: boolean;
};
type Pending = { id: string; tool: string; args: Record<string, unknown> };
type AuditRow = { time: string; event: string; tool: string; outcome: string; reason: string; target: string };
type AskResult = { status: string; reason?: string; reply?: string; result?: unknown; pending_id?: string };

export default function Agent() {
  const [perms, setPerms] = useState<Perm[]>([]);
  const [pending, setPending] = useState<Pending[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [instruction, setInstruction] = useState("");
  const [useDocs, setUseDocs] = useState(false);
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [p, q, a] = await Promise.all([
        api<Perm[]>("/permissions"),
        api<Pending[]>("/agent/pending"),
        api<AuditRow[]>("/audit"),
      ]);
      setPerms(p);
      setPending(q);
      setAudit(a);
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
    useEffect(() => {
    Promise.all([
      api<Perm[]>("/permissions"),
      api<Pending[]>("/agent/pending"),
      api<AuditRow[]>("/audit"),
    ])
      .then(([p, q, a]) => {
        setPerms(p);
        setPending(q);
        setAudit(a);
      })
      .catch((e) => setError(errorText(e)));
  }, []);

  async function run(action: () => Promise<unknown>) {
    setError("");
    try {
      await action();
      await load();
    } catch (e) {
      setError(errorText(e));
    }
  }

  async function ask(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setResult(null);
    await run(async () => {
      setResult(await api<AskResult>("/agent/ask", {
        method: "POST",
        body: { instruction, use_documents: useDocs },
      }));
    });
    setBusy(false);
  }

  return (
    <div>
      {error && <p className="error" role="alert">{error}</p>}

      <div className="card">
        <h2>What the AI is allowed to do</h2>
        <p className="muted">
          The AI can only <em>propose</em> actions. These switches are checked by the server, and the AI cannot change them.
        </p>
        {perms.map((p) => (
          <div key={p.tool} className="row">
            <label className="inline">
              <input
                type="checkbox"
                checked={p.enabled}
                onChange={(e) => void run(() => api(`/permissions/${p.tool}`, { method: "PUT", body: { enabled: e.target.checked } }))}
              />
              <strong>{p.tool}</strong>
            </label>
            {p.requires_approval && <span className="badge">needs your approval</span>}
            {p.blocked_by_network_policy && <span className="badge">blocked: offline mode</span>}
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Ask the agent to do something</h2>
        <form onSubmit={ask}>
          <label htmlFor="ins">Instruction</label>
          <textarea id="ins" rows={2} value={instruction} onChange={(e) => setInstruction(e.target.value)} />
          <div className="row">
            <label className="inline">
              <input type="checkbox" checked={useDocs} onChange={(e) => setUseDocs(e.target.checked)} />
              Let it read my documents
            </label>
            <button disabled={busy || !instruction.trim()}>Ask</button>
          </div>
        </form>
        {busy && <p className="muted">Waiting for the local model…</p>}
        {result && (
          <div role="status">
            <strong>Result: {result.status}</strong>
            {result.reason && <p>{result.reason}</p>}
            {result.reply && <p>{result.reply}</p>}
            {result.result !== undefined && <pre>{JSON.stringify(result.result, null, 2)}</pre>}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Waiting for your approval</h2>
        {pending.length === 0 && <p className="muted">Nothing is waiting.</p>}
        {pending.map((p) => (
          <div key={p.id} className="card">
            <strong>{p.tool}</strong>
            <p className="muted">This is exactly what will run if you approve:</p>
            <pre>{JSON.stringify(p.args, null, 2)}</pre>
            <div className="row">
              <button onClick={() => void run(async () => setResult(await api<AskResult>(`/agent/pending/${p.id}/approve`, { method: "POST" })))}>Approve</button>
              <button onClick={() => void run(() => api(`/agent/pending/${p.id}/reject`, { method: "POST" }))}>Reject</button>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Activity log</h2>
        <p className="muted">Only you can see this. It records decisions, never document text.</p>
        <table>
          <thead><tr><th>Time</th><th>Event</th><th>Tool</th><th>Outcome</th><th>Reason</th></tr></thead>
          <tbody>
            {audit.map((a, i) => (
              <tr key={`${a.time}-${i}`}>
                <td>{new Date(a.time).toLocaleString()}</td><td>{a.event}</td><td>{a.tool}</td>
                <td>{a.outcome}</td><td>{a.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}