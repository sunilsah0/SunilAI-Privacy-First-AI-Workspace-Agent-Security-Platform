import { useState, type FormEvent } from "react";
import { api, errorText } from "../api";

export default function Login({ onLoggedIn }: { onLoggedIn: (token: string, email: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
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
    <form onSubmit={submit} className="card" style={{ maxWidth: 420 }}>
      <h2>{mode === "login" ? "Log in" : "Create account"}</h2>
      <label htmlFor="email">Email</label>
      <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      <label htmlFor="password">Password {mode === "register" && "(at least 10 characters)"}</label>
      <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
      {error && <p className="error" role="alert">{error}</p>}
      <p className="row">
        <button disabled={busy}>{mode === "login" ? "Log in" : "Register and log in"}</button>
        <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "I need an account" : "I already have an account"}
        </button>
      </p>
    </form>
  );
}