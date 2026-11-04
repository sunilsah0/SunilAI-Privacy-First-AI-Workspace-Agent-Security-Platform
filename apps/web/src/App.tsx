import { useEffect, useState } from "react";
import { api, setToken, setUnauthorizedHandler } from "./api";
import type { PublicInfo } from "./types";
import Login from "./components/Login";
import Chat from "./components/Chat";
import Documents from "./components/Documents";
import Organization from "./components/Organization";
import Agent from "./components/Agent";
import YourData from "./components/YourData";
import Privacy from "./components/Privacy";
import { Icon, type IconName } from "./components/Icons";
import { Seal, type Status } from "./components/Seal";

type Tab = "chat" | "documents" | "organization" | "agent" | "data" | "privacy";

const TABS: { id: Tab; label: string; icon: IconName; blurb: string }[] = [
  { id: "chat", label: "Chat", icon: "chat", blurb: "Talk to a model that runs on your own machine or server." },
  { id: "documents", label: "Documents", icon: "file", blurb: "Upload files and search them by meaning. Your documents stay in your own database." },
  { id: "organization", label: "Organization", icon: "building", blurb: "Shared workspaces, roles and an audit trail for your team." },
  { id: "agent", label: "Agent", icon: "agent", blurb: "Decide what the AI may do. It can only propose; the server and you decide." },
  { id: "data", label: "My data", icon: "data", blurb: "Download your data, set clean-up rules, or delete your account." },
  { id: "privacy", label: "Privacy", icon: "shield", blurb: "What we checked, what is only a setting, and what we have not tested." },
];

type Theme = "auto" | "light" | "dark";
const THEME_KEY = "sunilai-theme";

function readTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    return saved === "light" || saved === "dark" ? saved : "auto";
  } catch {
    return "auto";
  }
}

export const DEMO_NOTICE =
  "Demo: AI replies are simulated and this server is wiped regularly. Please do not enter real or personal information.";

export default function App() {
  const [email, setEmail] = useState<string | null>(null); // logged in when not null
  const [tab, setTab] = useState<Tab>("chat");
  const [theme, setTheme] = useState<Theme>(readTheme);
  const [statuses, setStatuses] = useState<Status[]>([]);
  const [info, setInfo] = useState<PublicInfo | null>(null);
  const onPrivacy = tab === "privacy";

  useEffect(() => {
    api<PublicInfo>("/public-info")
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setEmail(null);
    });
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "auto") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* storage may be unavailable; the theme still works for this visit */
    }
  }, [theme]);

  useEffect(() => {
    if (!email) return;
    api<{ checks: { status: Status }[] }>("/privacy/status")
      .then((r) => setStatuses(r.checks.map((c) => c.status)))
      .catch(() => setStatuses([]));
  }, [email, onPrivacy]);

  function cycleTheme() {
    setTheme((t) => (t === "auto" ? "light" : t === "light" ? "dark" : "auto"));
  }

  function logout() {
    setToken(null);
    setEmail(null);
    setTab("chat");
    setStatuses([]);
  }

  if (!email) {
    return <Login info={info} onLoggedIn={(token, em) => { setToken(token); setEmail(em); }} />;
  }

  const tabs = info?.edition === "personal" ? TABS.filter((t) => t.id !== "organization") : TABS;
  const current = tabs.find((t) => t.id === tab) ?? tabs[0];
  const verified = statuses.filter((s) => s === "verified").length;
  const trustText = statuses.length ? `${verified} of ${statuses.length} checks verified` : "Checking...";

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      {info?.demo && <div className="banner" role="note">{DEMO_NOTICE}</div>}
      <header className="masthead">
        <div className="mast-inner">
          <span className="wordmark">SunilAI</span>
          <nav className="tabs" aria-label="Main">
            {tabs.map((t) => (
              <button
                key={t.id}
                className="tab"
                aria-current={current.id === t.id ? "page" : undefined}
                onClick={() => setTab(t.id)}
              >
                <Icon name={t.icon} />
                <span>{t.label}</span>
              </button>
            ))}
          </nav>
          <div className="mast-tools">
            <button className="trust" onClick={() => setTab("privacy")} aria-label={`Privacy status: ${trustText}. Open the privacy page.`}>
              <Seal statuses={statuses} size={40} animate />
              <span className="trust-text">{trustText}</span>
            </button>
            <button className="tool small" onClick={cycleTheme} aria-label={`Colour theme: ${theme}. Press to change.`}>
              {theme}
            </button>
            <span className="avatar" title={email} aria-hidden="true">{email.charAt(0).toUpperCase()}</span>
            <button className="tool small" onClick={logout}>Log out</button>
          </div>
        </div>
      </header>
      <main className="page" id="main">
        <div className="page-head">
          <h1>{current.label}</h1>
          <p>{current.blurb}</p>
        </div>
        {current.id === "chat" && <Chat />}
        {current.id === "documents" && <Documents />}
        {current.id === "organization" && <Organization />}
        {current.id === "agent" && <Agent />}
        {current.id === "data" && <YourData onDeleted={logout} />}
        {current.id === "privacy" && <Privacy />}
      </main>
    </>
  );
}
