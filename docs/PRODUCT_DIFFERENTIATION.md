# Product differentiation

These are goals we **implemented and tested**, not claims that nobody else does them. Competitors are described in [COMPETITOR_ANALYSIS.md](COMPETITOR_ANALYSIS.md). For each item, "what we found" means what appeared in the documents we read.

## D1. Verifiable privacy controls

- **Claim:** the Privacy status page labels each statement `verified`, `configured`, `unverified` or `failed`, based on live checks (database account, Row-Level Security on every user-data table, audit-log privileges, in-app network guard) and never shows a single "secure" light.
- **Verify:** open **Privacy status**; run `pytest tests/test_privacy.py`; run `python scripts\verify_docker_offline.py` for the Docker network.
- **Limits:** the app cannot verify the firewall by itself. A failed probe may mean "blocked" or "no internet", so that line stays `configured` until you run the control experiment.
- **What we found elsewhere:** no equivalent status page in the documents we read (not proof that none exists).

## D2. Agent-independent authorization

- **Claim:** a tricked model cannot change what it is allowed to do. Permissions live in a policy engine and the database, and there is no tool that edits permissions.
- **Verify:** `pytest tests/test_agent.py` (a scripted "manipulated model" proposes forbidden actions and the server refuses).
- **Limits:** single-step tools only. The model can still say misleading things in plain chat.
- **What we found elsewhere:** Open WebUI documents roles, groups and sharing rules; we did not evaluate how it handles a manipulated model.

## D3. The same rules in personal and enterprise use

- **Claim (partial):** one codebase and one set of database rules serve a single person and an organization. A personal account and an organization member use the same isolation layer.
- **Verify:** `pytest tests/test_isolation.py tests/test_orgs.py`.
- **Limits:** there is **no desktop or mobile app** (Tauri and mobile were not built), so "personal edition" means running the same web app on your own computer.

## D4. Transparent data-flow visibility

- **Claim:** people can see where data lives and who touched it: the privacy page shows storage and network scope, the activity log shows decisions, and break-glass access to your documents is visible to you.
- **Verify:** **Privacy status**, **Agent permissions** (activity log), **My data** (exceptional access).
- **Limits:** audit entries record decisions, not content, and the privacy page describes only this app, not Ollama or Docker.

## D5. Security tests built into the product

- **Claim:** isolation, tenant, agent and break-glass attacks are tested on every push, and the status page runs live checks.
- **Verify:** `pytest` locally; the **CI** workflow on GitHub.
- **Limits:** passing tests show only the tested cases. There is no independent audit.

## Where we are not different

Chat quality, model choice, speed, interface polish and ecosystem. Use mature tools for those.
