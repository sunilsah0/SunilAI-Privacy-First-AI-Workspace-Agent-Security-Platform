import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { api, errorText } from "../api";

type Doc = { id: string; title: string };
type Hit = { document_id: string; title: string; text: string; distance: number };

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setDocs(await api<Doc[]>("/documents"));
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
    useEffect(() => {
    api<Doc[]>("/documents")
      .then(setDocs)
      .catch((e) => setError(errorText(e)));
  }, []);

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const input = e.target;
    const file = input.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    setNote("");
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await api<{ title: string; chunks: number }>("/documents/upload", { method: "POST", form });
      setNote(`Uploaded "${r.title}" (${r.chunks} searchable pieces).`);
      await load();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
      input.value = "";
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this document and its search data?")) return;
    try {
      await api(`/documents/${id}`, { method: "DELETE" });
      setHits(null);
      await load();
    } catch (e) {
      setError(errorText(e));
    }
  }

  async function search(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setError("");
    try {
      setHits(await api<Hit[]>("/search", { method: "POST", body: { query, k: 4 } }));
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <div>
      <div className="card">
        <h2>Upload a document</h2>
        <p className="muted">.txt, .md or .pdf, up to 5 MB. It is processed on this computer.</p>
        <label htmlFor="file" className="sr-only">Choose a file</label>
        <input id="file" type="file" accept=".txt,.md,.pdf" onChange={(e) => void upload(e)} disabled={busy} />
        {busy && <p className="muted">Reading and indexing…</p>}
        {note && <p role="status">{note}</p>}
      </div>

      {error && <p className="error" role="alert">{error}</p>}

      <div className="card">
        <h2>Your documents</h2>
        {docs.length === 0 && <p className="muted">Nothing here yet.</p>}
        <ul className="list">
          {docs.map((d) => (
            <li key={d.id}>
              <span className="link">{d.title}</span>
              <button className="small" aria-label={`Delete ${d.title}`} onClick={() => void remove(d.id)}>Delete</button>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2>Search by meaning</h2>
        <form onSubmit={search} className="row">
          <label htmlFor="q" className="sr-only">Search query</label>
          <input id="q" type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. which port does the database use?" />
          <button>Search</button>
        </form>
        {hits && hits.length === 0 && <p className="muted">No results.</p>}
        {hits && hits.map((h, i) => (
          <div key={i} className="card">
            <strong>{h.title}</strong>
            <span className="muted"> closeness {(1 - h.distance).toFixed(2)}</span>
            <p style={{ whiteSpace: "pre-wrap" }}>{h.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}