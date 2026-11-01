import { useCallback, useEffect, useState } from "react";
import { api, errorText } from "../api";
import { Seal, Stamp, type Status } from "./Seal";

type Check = { id: string; title: string; status: Status; detail: string };
type Report = { checks: Check[]; info: Record<string, string> };

const ORDER: Status[] = ["verified", "configured", "unverified", "failed"];
const LABEL: Record<Status, string> = {
  verified: "checked just now",
  configured: "a setting, not proven",
  unverified: "not tested yet",
  failed: "failed",
};

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

  const checks = report?.checks ?? [];
  const count = (s: Status) => checks.filter((c) => c.status === s).length;

  return (
    <div>
      {error && <p className="error" role="alert">{error}</p>}

      <section className="summary" aria-label="Summary">
        <Seal statuses={checks.map((c) => c.status)} size={132} animate label="Ring of check results" />
        <div>
          <h2>{checks.length ? `${count("verified")} of ${checks.length} checks verified` : "Running checks..."}</h2>
          <p className="muted prose">
            Each line is something we checked just now, a setting we have not proven, something not tested yet, or a
            failure. Nothing on this page is a guarantee.
          </p>
          <ul className="tally">
            {ORDER.map((s) => (
              <li key={s}>
                <Stamp status={s} />
                <span>{count(s)} {LABEL[s]}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <div className="row">
        <button onClick={() => void load()}>Check again</button>
        <button onClick={() => void probe()}>Test the firewall (one connection attempt)</button>
      </div>

      {report && (
        <>
          <ul className="ledger">
            {checks.map((c) => (
              <li key={c.id} className={`ledger-row ${c.status}`}>
                <Stamp status={c.status} />
                <div>
                  <strong>{c.title}</strong>
                  <p className="muted">{c.detail}</p>
                </div>
                <span className="verdict">{LABEL[c.status]}</span>
              </li>
            ))}
          </ul>

          <section className="card">
            <h3>Where things happen</h3>
            <dl className="facts">
              {Object.entries(report.info).map(([k, v]) => (
                <div key={k} className="fact">
                  <dt>{k.replace(/_/g, " ")}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          </section>
        </>
      )}
    </div>
  );
}
