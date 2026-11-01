import { useState, type FormEvent } from "react";
import { api, errorText } from "../api";
import { Seal, Stamp, type Status } from "./Seal";

const SAMPLE: { status: Status; text: string }[] = [
  { status: "verified", text: "The database account cannot bypass row security" },
  { status: "configured", text: "Firewall: a setting we have not proven" },
  { status: "unverified", text: "Offline answers: not tested yet" },
];

export default function Login({ onLoggedIn }: { onLoggedIn: (token: string, email: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api("/auth/register", { method: "POST", body: { email, password } });
      }
      const r = await api<{ access_token: string }>("/auth/login", { method: "POST", body: { email, password } });
      onLoggedIn(r.access_token, email);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <section className="auth-hero">
        <Seal size={112} animate label="SunilAI seal" />
        <h1>SunilAI</h1>
        <p className="tagline">Privacy-First AI Workspace &amp; Agent Security Platform</p>
        <div className="sample">
          <h2>Every claim wears a stamp</h2>
          <ul>
            {SAMPLE.map((s) => (
              <li key={s.text}>
                <Stamp status={s.status} />
                <span>{s.text}</span>
              </li>
            ))}
          </ul>
          <p className="muted small-print">Example only. Your own checks appear after you sign in.</p>
        </div>
        <p className="muted small-print">A learning project. It has not been independently audited.</p>
      </section>

      <form onSubmit={submit} className="card auth-card">
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p className="muted">
          {mode === "login" ? "Sign in to your private workspace." : "It takes a minute. Your data stays in your own database."}
        </p>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="password">Password{mode === "register" && " (at least 10 characters)"}</label>
        <div className="row">
          <input
            id="password"
            type={show ? "text" : "password"}
            required
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ flex: 1, minWidth: 0 }}
          />
          <button type="button" className="small" onClick={() => setShow((v) => !v)} aria-pressed={show}>
            {show ? "Hide" : "Show"}
          </button>
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        <p className="row">
          <button className="primary" disabled={busy}>
            {busy ? "One moment..." : mode === "login" ? "Sign in" : "Register and sign in"}
          </button>
          <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "I need an account" : "I already have an account"}
          </button>
        </p>
      </form>
    </div>
  );
}
