# Competitor analysis

**Researched on 2026-10-29** from public web pages. Vendor documentation is used where it was found; third-party pages are marked **(third-party)**. Products change quickly, so re-check before you publish. We list only what we found. "Not found" means we did not see it in the pages we read, not that the product lacks it.

## Summary table

| Product | What it is | License (as found) | Users and access control (as found) | Offline and privacy notes (as found) |
|---|---|---|---|---|
| Open WebUI | Self-hosted web chat interface | BSD-3-style license with a branding clause since v0.6.6 (April 2025) | Roles (admin, user, pending), permission settings, groups, and sharing of private models and knowledge with groups or individuals. Admins have broad access by default, with settings that can stop admins viewing other users' chats and private resources. | Works with local model servers. We did not research its telemetry. |
| AnythingLLM | Desktop app and Docker server for chat with documents | MIT **(third-party)** | Multi-user mode is Docker-only. Roles: admin, manager, default. Admins and managers can reach all workspaces; default users only workspaces they are added to. In single-user mode, anyone with the password can see all chats. | Desktop version is single-user. Third-party advisory summaries list multi-user data-scoping bugs fixed in later releases, which shows why a second enforcement layer matters. |
| Jan | Desktop local-AI app | Apache-2.0 | We found a single-user desktop app, a local API server and tool (MCP) support. Multi-user features: not found. | Runs offline with local models. Cloud providers are optional. |
| LM Studio | Desktop app for running local models | Closed source **(third-party)**; free for personal and work use since July 2025 (vendor blog) | An enterprise plan with single sign-on, model gating and private sharing is reported **(third-party)**. | Documentation reported to describe fully offline operation **(third-party)**. |
| Ollama | Local model runtime with an HTTP API | MIT **(third-party)** | The API has no built-in authentication (security research, including a Cloud Security Alliance note). Binds to localhost by default **(third-party)**. | Its official FAQ describes optional cloud features that can be turned off with `OLLAMA_NO_CLOUD=1`. We apply this in the release compose file. |
| GPT4All | Desktop chat app with local document search | MIT **(third-party)** | Multi-user features: not found. | LocalDocs searches your files locally **(third-party)**. |
| llama.cpp | Inference engine with a small server | MIT **(third-party)** | Optional API key flag and loopback-by-default server reported **(third-party)**. It is an engine, not a workspace product. | Runs locally. |

## Reference components (not compared)

- **PostgreSQL Row-Level Security:** the database feature this project builds on.
- **Keycloak:** an identity server we did not use. It is the natural next step for single sign-on and multi-factor authentication.
- **OWASP Top 10 for LLM Applications (2025):** used as a checklist in [THREAT_MODEL.md](THREAT_MODEL.md).

## What we did not verify

Telemetry behavior of each product, enterprise features beyond those listed, current maintenance status, and anything behind paid plans.

## Where the others are stronger

Broader model and GPU support, polished apps, large communities, groups and sharing rules (Open WebUI), single sign-on (reported for LM Studio's enterprise plan), and years of real-world use. This project is a learning project, not a replacement.

## Sources

- https://docs.openwebui.com/features/authentication-access/rbac/
- https://docs.openwebui.com/features/authentication-access/rbac/roles
- https://docs.openwebui.com/license/
- https://docs.anythingllm.com/features/security-and-access
- https://mintlify.wiki/Mintplex-Labs/anything-llm/features/multi-user (third-party)
- https://releasealert.dev/github/Mintplex-Labs/anything-llm/cves (third-party)
- https://docs.jan.ai/local-server
- https://www.lmstudio.ai/blog/free-for-work
- https://alternativeto.net/news/2025/7/lm-studio-lifts-commercial-license-barrier-expands-free-team-collaboration/ (third-party)
- https://docs.ollama.com/faq.md
- https://labs.cloudsecurityalliance.org/research-rb/csa-research-note-self-hosted-ai-infrastructure-exposure-202/
- https://openapps.pro/apps/gpt4all (third-party)
- https://www.bdemerson.com/article/owasp-llm-top-10 (third-party summary of the OWASP list)
