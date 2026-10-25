import socket
import os
from datetime import datetime, timezone
import httpx

from sqlalchemy import text
from . import network_guard
from .providers import OLLAMA_URL

last_probe = {"result": None, "time": None}   # kept in memory only

INFO = {
    "database": "PostgreSQL. Development: 127.0.0.1:5433. Docker release: a private Docker network.",
    "model_server": OLLAMA_URL,
    "network_scope": ("This computer and private networks only" if network_guard.ALLOW_PRIVATE_NETWORK
                      else "This computer only"),
    "network_enforcement": os.getenv("NETWORK_ENFORCEMENT_NOTE",
                                     "Windows Firewall rule (scripts/offline-on.ps1), if you turned it on"),
    "uploaded_files": "Files are not kept as files. Extracted text and its embeddings are stored in the database only.",
    "telemetry": "This app contains no analytics or telemetry code.",
    "not_covered": "Ollama and Docker are separate programs with their own network behavior (updates, model downloads). Restrict them separately.",
}

def record_probe(reachable: bool) -> None:
    last_probe["result"] = "reachable" if reachable else "blocked"
    last_probe["time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

def _c(id, title, status, detail):
    return {"id": id, "title": title, "status": status, "detail": detail}

def run_checks(db) -> list[dict]:
    out = []

    # 1. Is the AI model server local?
    title = "AI model runs on this computer"
    try:
        httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2).raise_for_status()
        out.append(_c("model_local", title, "verified",
                      f"A model server answered at {OLLAMA_URL}."))
    except Exception:
        out.append(_c("model_local", title, "unverified",
                      f"Configured for {OLLAMA_URL} but nothing answered. Is Ollama running?"))

    # 2. The setting itself
    title = "Strict offline mode setting"
    if network_guard.OFFLINE_MODE:
        out.append(_c("offline_setting", title, "configured",
                      "OFFLINE_MODE is on. A setting alone proves nothing, so see the next two checks."))
    else:
        out.append(_c("offline_setting", title, "failed",
                      "OFFLINE_MODE is off: external connections are allowed."))

    # 3. In-app guard, tested live (the guard refuses before any packet is sent)
    title = "In-app network guard"
    if not network_guard.is_installed():
        out.append(_c("app_guard", title, "failed", "The guard is not installed."))
    else:
        try:
            socket.create_connection(("1.1.1.1", 443), timeout=1)   # the guard refuses this before any packet is sent
            out.append(_c("app_guard", title, "failed", "An external connection was NOT blocked."))
        except PermissionError:
            out.append(_c("app_guard", title, "verified",
                          "A test connection to an external address was refused. This guard covers this "
                          "program only. Child programs and native code can bypass it, so the OS firewall matters."))
        except OSError:
            out.append(_c("app_guard", title, "failed", "Unexpected network error during the self-test."))

    # 4. OS firewall: only as good as the last real test
    title = "Operating-system firewall"
    if last_probe["result"] is None:
        out.append(_c("os_firewall", title, "unverified",
                      "Not tested yet. Run scripts/check_network.py or POST /privacy/verify-network."))
    elif last_probe["result"] == "reachable":
        out.append(_c("os_firewall", title, "failed",
                      f"At {last_probe['time']} this program reached the internet. The firewall is NOT blocking it."))
    else:
        out.append(_c("os_firewall", title, "configured",
                      f"At {last_probe['time']} a connection attempt failed. That means blocked OR no internet "
                      "at that moment. Use the 2-step check in scripts/check_network.py to be sure."))

    # 5. Database role cannot bypass Row-Level Security
    row = db.execute(text(
        "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")).one()
    title = "Database account cannot bypass row security"
    out.append(_c("db_role", title, "verified" if row == (False, False) else "failed",
                  "Checked live against the database."))

    # 6. Every table with an owner has forced Row-Level Security
    bad = db.execute(text("""
        SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
                    AND (c.relname = 'organizations' OR EXISTS (
                SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid
                  AND a.attname IN ('owner_id', 'org_id') AND NOT a.attisdropped))
          AND NOT (c.relrowsecurity AND c.relforcerowsecurity)
    """)).scalars().all()
    title = "Row-Level Security on all user-data tables"
    out.append(_c("rls_tables", title, "verified" if not bad else "failed",
                  "Checked live against the database." if not bad else f"Missing on: {', '.join(bad)}"))

    # 7. Audit log is append-only for the app account
    upd, dele = db.execute(text(
        "SELECT has_table_privilege(current_user, 'audit_events', 'UPDATE'), "
        "has_table_privilege(current_user, 'audit_events', 'DELETE')")).one()
    title = "Audit log cannot be edited or deleted by the app"
    out.append(_c("audit_append_only", title, "verified" if not (upd or dele) else "failed",
                  "Checked live against database privileges."))
    return out