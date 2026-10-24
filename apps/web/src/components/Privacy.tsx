import { useCallback, useEffect, useState } from "react";
import { api, errorText } from "../api";

type Status = "verified" | "configured" | "unverified" | "failed";
type Check = { id: string; title: string; status: Status; detail: string };
type Report = { checks: Check[]; info: Record<string, string> };

const ICON: Record<Status, string> = { verified: "✔", configured: "◐", unverified: "?", failed: "✖" };

export default function Privacy() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setReport(await api<Report>("/privacy/status"));
    } catch (e) {
      setError(errorText(e));
    }
  }, []);
    useEffect(() => {
    api<Report>("/privacy/status")
      .then(setReport)
      .catch((e) => setError(errorText(e)));
  }, []);

  async function probe() {
    const ok = window.confirm(
      "This makes ONE connection attempt to 1.1.1.1 (port 443) to test whether your firewall blocks it. No data is sent. Continue?"
    );
    if (!ok) return;
    try {
      await api("/privacy/verify-network", { method: "POST", body: { confirm: true } });
      await load();
    } catch (e) {
      setError(errorText(e));
    }
  }

  return (
    <div>
      <h2>Privacy and security status</h2>
      <p className="muted">
        ✔ verified = observed or tested just now · ◐ configured = a setting says so, not proven ·
        ? unverified = not tested · ✖ failed. Passing checks are evidence for these cases only, not a guarantee.
      </p>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="row">
        <button onClick={() => void load()}>Re-run checks</button>
        <button onClick={() => void probe()}>Test the firewall (one connection attempt)</button>
      </div>

      {report && (
        <>
          {report.checks.map((c) => (
            <div key={c.id} className={`card ${c.status}`}>
              <span className="badge">{ICON[c.status]} {c.status}</span> <strong>{c.title}</strong>
              <p>{c.detail}</p>
            </div>
          ))}
          <div className="card">
            <h3>Where things happen</h3>
            <dl>
              {Object.entries(report.info).map(([k, v]) => (
                <div key={k}>
                  <dt><strong>{k.replace(/_/g, " ")}</strong></dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </>
      )}
    </div>
  );
}