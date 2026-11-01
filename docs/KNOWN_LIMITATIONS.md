# Known limitations

Read this before trusting SunilAI with real data. Nothing here is hidden on purpose, and none of it is fixed yet.

## Security gaps

- **No rate limiting or account lockout** on login or any other endpoint.
- **No multi-factor authentication, single sign-on, password reset or email verification.**
- **Tokens are stateless** and last 30 minutes. Logging out only forgets the token in the browser.
- **No TLS.** The release serves plain HTTP on `127.0.0.1` only. A team deployment needs HTTPS in front of it.
- **No encryption at rest inside the app** and no key management. Use full-disk encryption (BitLocker, FileVault, LUKS).
- **The database trusts the API to state who the user is.** SQL injection would let an attacker pick any identity. We use bound parameters only.
- **Email addresses can be discovered**: sign-up reports "already registered" and adding a member reports "no registered user".
- **Other signed-in sessions can look up users by email** (login needs it).
- **PDF parsing runs inside the API process.** A hostile PDF could exploit the parser. No malware scanning.
- **Break-glass** exposes all of a person's personal documents (not chats), needs two admins, and the reason is not verified.
- **The gateway container can reach the internet** (it must be reachable from your computer). It holds no data but passes traffic.
- **The in-app network guard** covers only the API process. Child programs and native code can bypass it.
- **Dependencies and container images are not pinned** to exact versions or digests. Vulnerability scans are informational and untriaged.
- **The web app has no automated browser tests**, its accessibility is unaudited, and the Content-Security-Policy still allows inline styles.

## Missing features compared with the original brief

- No desktop (Tauri) or mobile apps; no signed installers.
- No separate "personal memory" feature.
- No teams (sub-groups) and no organization-wide AI search.
- No invitation links, organization-level model/tool policies or organization retention policies.
- File types: `.txt`, `.md`, `.pdf` only (no DOCX, CSV, OCR).
- No validation of model files; the models come from Ollama's registry.
- No dedicated model workers per organization.
- Retention covers conversations only.
- Backups are manual and untested in CI.

## Operational limits

- Docker CPU-only models are slower than native Ollama on a GPU, and native Ollama is outside the Docker network guarantee.
- The Windows firewall script covers Python only, needs Administrator rights, and blocks `pip` while it is on.
- A failed network probe cannot distinguish "blocked" from "no internet".
- Ollama and Docker have their own update and download behavior.
- GitHub Actions and similar free tiers have limits. Public hosting is never free forever.

## Not done

No independent security review, audit or certification has taken place.
