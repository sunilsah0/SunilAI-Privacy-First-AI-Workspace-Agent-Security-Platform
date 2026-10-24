import { useEffect, useState } from "react";
import { setToken, setUnauthorizedHandler } from "./api";
import Login from "./components/Login";
import Chat from "./components/Chat";
import Documents from "./components/Documents";
import Agent from "./components/Agent";
import Privacy from "./components/Privacy";
import Organization from "./components/Organization";
import YourData from "./components/YourData";

   type Tab = "chat" | "documents" | "organization" | "agent" | "data" | "privacy";
   const TABS: { id: Tab; label: string }[] = [
     { id: "chat", label: "Chat" },
     { id: "documents", label: "Documents" },
     { id: "organization", label: "Organization" },
     { id: "agent", label: "Agent permissions" },
     { id: "data", label: "My data" },
     { id: "privacy", label: "Privacy status" },
    
   ];

export default function App() {
  const [email, setEmail] = useState<string | null>(null);   // logged in when not null
  const [tab, setTab] = useState<Tab>("chat");

  useEffect(() => {
    setUnauthorizedHandler(() => { setToken(null); setEmail(null); });   // login expired
  }, []);

  function logout() {
    setToken(null);
    setEmail(null);
    setTab("chat");
  }

  return (
    <div className="app">
      <header className="top">
        <h1>VerityAI</h1>
        {email && (
          <div className="row">
            <span className="muted">{email}</span>
            <button onClick={logout}>Log out</button>
          </div>
        )}
      </header>

      {!email ? (
        <Login onLoggedIn={(token, em) => { setToken(token); setEmail(em); }} />
      ) : (
        <>
          <nav className="tabs" aria-label="Main">
            {TABS.map((t) => (
              <button key={t.id} aria-current={tab === t.id ? "page" : undefined} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </nav>
          <main>
            {tab === "chat" && <Chat />}
            {tab === "documents" && <Documents />}
            {tab === "agent" && <Agent />}
            {tab === "data" && <YourData onDeleted={logout} />}
            {tab === "privacy" && <Privacy />}
            {tab === "organization" && <Organization />}
          </main>
        </>
      )}
    </div>
  );
}