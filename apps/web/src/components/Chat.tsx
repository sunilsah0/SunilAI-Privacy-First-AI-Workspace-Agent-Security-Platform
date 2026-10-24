import {  useEffect, useState, type FormEvent } from "react";
import { api, errorText } from "../api";

type Conv = { id: string; title: string };
type Msg = { role: string; content: string };

export default function Chat() {
  const [convs, setConvs] = useState<Conv[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [useDocs, setUseDocs] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

    useEffect(() => {
    api<Conv[]>("/conversations")
      .then(setConvs)
      .catch((e) => setError(errorText(e)));
  }, []);
  async function open(id: string) {
    setError("");
    setActiveId(id);
    try {
      const c = await api<{ messages: Msg[] }>(`/conversations/${id}`);
      setMessages(c.messages);
    } catch (e) {
      setError(errorText(e));
    }
  }

  function newChat() {
    setActiveId(null);
    setMessages([]);
    setError("");
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await api(`/conversations/${id}`, { method: "DELETE" });
      setConvs((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) newChat();
    } catch (e) {
      setError(errorText(e));
    }
  }

  async function send(e: FormEvent) {
    e.preventDefault();
    const content = text.trim();
    if (!content || busy) return;
    setBusy(true);
    setError("");
    try {
      let id = activeId;
      if (!id) {
        const c = await api<Conv>("/conversations", { method: "POST", body: { title: content.slice(0, 40) } });
        id = c.id;
        setActiveId(id);
        setConvs((prev) => [...prev, c]);
      }
      const r = await api<{ reply: string }>(`/conversations/${id}/messages`, {
        method: "POST",
        body: { content, use_documents: useDocs },
      });
      setMessages((prev) => [...prev, { role: "user", content }, { role: "assistant", content: r.reply }]);
      setText("");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="layout">
      <aside aria-label="Conversations">
        <button onClick={newChat}>+ New chat</button>
        <ul className="list">
          {convs.map((c) => (
            <li key={c.id}>
              <button className={c.id === activeId ? "link active" : "link"} onClick={() => void open(c.id)}>
                {c.title}
              </button>
              <button className="small" aria-label={`Delete ${c.title}`} onClick={() => void remove(c.id)}>✕</button>
            </li>
          ))}
        </ul>
      </aside>

      <section>
        <div className="messages" aria-live="polite">
          {messages.length === 0 && <p className="muted">Ask something. The AI runs on this computer.</p>}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <strong>{m.role === "user" ? "You" : "AI"}</strong>
              <p>{m.content}</p>
            </div>
          ))}
          {busy && <p className="muted">The local model is thinking… (the first reply can take a minute)</p>}
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        <form onSubmit={send} className="composer">
          <label htmlFor="msg" className="sr-only">Message</label>
          <textarea id="msg" rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder="Type a message…" />
          <div className="row">
            <label className="inline">
              <input type="checkbox" checked={useDocs} onChange={(e) => setUseDocs(e.target.checked)} />
              Use my documents
            </label>
            <button disabled={busy || !text.trim()}>Send</button>
          </div>
        </form>
      </section>
    </div>
  );
}