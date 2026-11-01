import { useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../api";

type Access = { time: string; action: string; document_id: string | null; accessor: string; organization: string | null };

export default function YourData({ onDeleted }: { onDeleted: () => void }) {
  const [days, setDays] = useState("");
  const [saved, setSaved] = useState("");
  const [access, setAccess] = useState<Access[]>([]);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<{ conversation_retention_days: number | null }>("/me/settings"),
      api<Access[]>("/me/access-log"),
    ])
      .then(([s, a]) => {
        setDays(s.conversation_retention_days ? String(s.conversation_retention_days) : "");
        setAccess(a);
      })
      .catch((e) => setError(errorText(e)));
  }, []);

  async function saveRetention(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaved("");
    try {
      await api("/me/settings", {
        method: "PUT",
        body: { conversation_retention_days: days.trim() ? Number(days) : null },
      });
      setSaved("Saved. Old conversations are removed when the cleanup job runs.");
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function download() {
    setError("");
    try {
      const data = await api<unknown>("/me/export");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "verityai-export.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function deleteAccount(e: FormEvent) {
    e.preventDefault();
    if (!window.confirm("This permanently deletes your account and all your personal data. Continue?")) return;
    try {
      await api("/me", { method: "DELETE", body: { password, confirm: true } });
      onDeleted();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <div>
     
      {error && <p className="error" role="alert">{error}</p>}

      <div className="card">
        <h3>Download everything</h3>
        <p className="muted">Your documents, conversations, permissions and activity as one file.</p>
        <button onClick={() => void download()}>Download my data</button>
      </div>

      <form className="card" onSubmit={saveRetention}>
        <h3>Automatic cleanup</h3>
        <label htmlFor="days">Delete conversations after this many days of inactivity (empty = keep forever)</label>
        <input id="days" type="number" min={1} max={3650} value={days} onChange={(e) => setDays(e.target.value)} />
        <p><button>Save</button> {saved && <span role="status">{saved}</span>}</p>
      </form>

      <div className="card">
        <h3>Exceptional access to my documents</h3>
        <p className="muted">
          If an organization ever reads your documents under break-glass access, it appears here.
        </p>
        {access.length === 0 ? (
          <p>No one has accessed your documents this way.</p>
        ) : (
          <table>
            <thead><tr><th>Time</th><th>Who</th><th>Organization</th><th>Action</th></tr></thead>
            <tbody>
              {access.map((a, i) => (
                <tr key={`${a.time}-${i}`}>
                  <td>{new Date(a.time).toLocaleString()}</td><td>{a.accessor}</td>
                  <td>{a.organization ?? "(an organization)"}</td><td>{a.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form className="card" onSubmit={deleteAccount}>
        <h3>Delete my account</h3>
        <p className="muted">
          Removes your documents, conversations, search data, permissions and settings. Shared organization
          documents you wrote stay with the organization without your name.
        </p>
        <label htmlFor="pw">Your password</label>
        <input id="pw" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <p><button>Delete my account</button></p>
      </form>
    </div>
  );
}