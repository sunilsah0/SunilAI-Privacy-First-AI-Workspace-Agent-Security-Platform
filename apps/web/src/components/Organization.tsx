import { useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../api";
import OrgPanel, { type Org } from "./OrgPanel";

export default function Organization() {
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [me, setMe] = useState<{ id: string; email: string } | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    Promise.all([api<Org[]>("/orgs"), api<{ id: string; email: string }>("/me")])
      .then(([o, m]) => {
        setOrgs(o);
        setMe(m);
      })
      .catch((e) => setError(errorText(e)));
  }, [reload]);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const r = await api<Org>("/orgs", { method: "POST", body: { name } });
      setName("");
      setSelected(r.id);
      setReload((k) => k + 1);
    } catch (err) {
      setError(errorText(err));
    }
  }

  const current = orgs.find((o) => o.id === selected) ?? orgs[0] ?? null;

  return (
    <div>
      {error && <p className="error" role="alert">{error}</p>}

      {orgs.length > 0 && (
        <div className="row">
          <label htmlFor="org">Organization</label>
          <select id="org" value={current?.id ?? ""} onChange={(e) => setSelected(e.target.value)}>
            {orgs.map((o) => <option key={o.id} value={o.id}>{o.name} ({o.role})</option>)}
          </select>
          <button onClick={() => setReload((k) => k + 1)}>Refresh</button>
        </div>
      )}
      {orgs.length === 0 && (
        <p className="muted">You are not in an organization yet. Create one, or ask an admin to add you.</p>
      )}

      {current && me && <OrgPanel key={`${current.id}-${current.role}`} org={current} me={me} />}

      <form onSubmit={create} className="card">
        <h3>Create a new organization</h3>
        <div className="row">
          <label htmlFor="org-name" className="sr-only">Name</label>
          <input id="org-name" type="text" required placeholder="Organization name" value={name} onChange={(e) => setName(e.target.value)} />
          <button>Create (you become the owner)</button>
        </div>
      </form>
    </div>
  );
}