# Development roadmap

## Done

1. Project setup, Git, Docker database
2. Authentication (Argon2, tokens) and tests
3. Document ownership and isolation tests
4. Row-Level Security, migrations
5. Local AI chat (Ollama), provider interface
6. Document upload and private search (pgvector)
7. Policy engine, agent tools, approvals, audit log
8. Offline guard, Windows firewall scripts, privacy status
9. React web interface
10. Organizations, roles, tenant isolation (backend and screen)
11. Break-glass access, retention, export and deletion
12. CI, Docker release with a private network, documentation set

## Next, in a sensible order

1. **Rate limiting and lockout** for login and uploads.
2. **TLS guide** (reverse proxy such as Caddy) and secure cookies or token handling review.
3. **Pin dependencies and images**, triage scan results, add `pip-audit` and `npm audit` as failing checks once clean.
4. **Automated restore test** and an upgrade/downgrade migration test.
5. **Browser end-to-end tests** (for example Playwright) and an accessibility pass.
6. **Organization-wide AI search** and **teams**, using the same Row-Level Security pattern.
7. **Invitation links**, then **single sign-on and multi-factor authentication** through an identity server such as Keycloak.
8. **Encryption at rest guidance** and an application-level option for the personal edition.
9. **Break-glass screen** in the web app, narrower scopes, and conversations as a scope.
10. **Desktop packaging** (Tauri) with signed installers, then more file types.
11. **Independent security review** before any claim of audit or certification.
