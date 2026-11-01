import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { api, errorText } from "../api";
import { Icon } from "./Icons";

type Conv = { id: string; title: string };
type Msg = { role: string; content: string };

const STARTERS = [
  { text: "Explain Row-Level Security in simple words", docs: false },
  { text: "Summarize the documents I uploaded", docs: true },
  { text: "What can an AI agent do here, and what can it not do?", docs: false },
];

export default function Chat() {
  const [convs, setConvs] = useState<Conv[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [useDocs, setUseDocs] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showList, setShowList] = useState(false);
  const boxRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    api<Conv[]>("/conversations")
      .then(setConvs)
      .catch((e) => setError(errorText(e)));
  }, []);

  useEffect(() => {
    const box = boxRef.current;
    if (!box) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    box.scrollTo({ top: box.scrollHeight, behavior: reduce ? "auto" : "smooth" });
  }, [messages, busy]);

  async function open(id: string) {
    setError("");
    setActiveId(id);
    setShowList(false);
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
    setShowList(false);
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

  async function submit() {
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

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void submit();
    }
  }

  return (
    <div className="chat">
      <div>
        <button className="convs-toggle small" onClick={() => setShowList((v) => !v)} aria-expanded={showList}>
          Conversations ({convs.length})
        </button>
        <aside className={showList ? "convs open" : "convs"} aria-label="Conversations">
          <button className="primary" onClick={newChat}>New chat</button>
          <ul className="list">
            {convs.map((c) => (
              <li key={c.id}>
                <button className={c.id === activeId ? "link active" : "link"} onClick={() => void open(c.id)}>
                  {c.title}
                </button>
                <button className="small" aria-label={`Delete ${c.title}`} onClick={() => void remove(c.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>

      <section className="card thread">
        <div className="transcript" ref={boxRef} aria-live="polite">
          {messages.length === 0 && !busy && (
            <div className="empty">
              <Icon name="chat" size={32} />
              <h2>Start a private conversation</h2>
              <p className="muted">
                Runs on your own machine or server. By design, nothing is sent to an outside AI service.
              </p>
              <div className="chips">
                {STARTERS.map((s) => (
                  <button
                    key={s.text}
                    className="chip small"
                    onClick={() => {
                      setText(s.text);
                      setUseDocs(s.docs);
                    }}
                  >
                    {s.text}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`turn ${m.role}`}>
              <div className="who">{m.role === "user" ? "You" : "SunilAI"}</div>
              <div className="said"><p>{m.content}</p></div>
            </div>
          ))}
          {busy && (
            <div className="turn assistant">
              <div className="who">SunilAI</div>
              <div className="said">
                <span className="typing" role="status" aria-label="The local model is thinking"><i /><i /><i /></span>
                <p className="muted small-print">The first reply can take a minute while the model loads.</p>
              </div>
            </div>
          )}
        </div>

        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
        >
          <label htmlFor="msg" className="sr-only">Message</label>
          <textarea
            id="msg"
            rows={2}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Write a message. Enter sends, Shift+Enter adds a new line."
          />
          {error && <p className="error" role="alert">{error}</p>}
          <div className="row spread">
            <label className="inline">
              <input type="checkbox" checked={useDocs} onChange={(e) => setUseDocs(e.target.checked)} />
              Use my documents
            </label>
            <button className="primary" disabled={busy || !text.trim()}>Send</button>
          </div>
        </form>
      </section>
    </div>
  );
}
