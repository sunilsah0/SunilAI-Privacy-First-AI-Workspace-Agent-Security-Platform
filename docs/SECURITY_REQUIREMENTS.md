# Security requirements

Each requirement says what must be true, what enforces it, and where it is verified.

| ID | Requirement | Enforced by | Verified by |
|---|---|---|---|
| SR-1 | A user cannot read another user's documents, chats, search data or settings | owner filters + RLS | `test_isolation.py`, `test_chat.py`, `test_rag.py`, `test_rls.py`, `test_privacy_rights.py` |
| SR-2 | A user cannot reach another organization's data | RLS on `org_id` tables, 404 for outsiders | `test_orgs.py` |
| SR-3 | No role can read another person's private content without an approved grant | role matrix, owner-only policies | `test_orgs.py`, `test_breakglass.py` |
| SR-4 | Break-glass needs a reason, a second owner, a time limit (60 min), is read-only and visible to the person | database policies and constraints | `test_breakglass.py` |
| SR-5 | The model cannot grant itself permissions | no permission-changing tool exists; policy engine is plain code | `test_agent.py` |
| SR-6 | Risky tools are off by default and need approval | tool registry | `test_agent.py` |
| SR-7 | Approved actions run the stored arguments, rechecked at approval time | `approve_pending` | `test_agent.py` |
| SR-8 | Audit logs are append-only for the app account | database grants | `test_agent.py`, `test_orgs.py`, `test_breakglass.py` |
| SR-9 | Offline mode refuses public network addresses inside the API | `network_guard.py` | `test_network.py` |
| SR-10 | The model server must be local or explicitly listed; no silent cloud fallback | `providers.py`, 503 on failure | `test_chat.py`, `test_network.py` |
| SR-11 | Production refuses to start without a strong secret key | `security.py` | `test_security_config.py` |
| SR-12 | The API container has no owner database credentials and is hardened | compose file | `test_release_config.py` |
| SR-13 | Account deletion removes personal data; shared organization records stay without the author | foreign keys | `test_privacy_rights.py` |
| SR-14 | Status page labels claims honestly | `privacy.py` | `test_privacy.py` |
| SR-15 | Secrets do not appear in test-run logs | no secret logging | `test_logging.py` |

## Role matrix

| Action | owner | security_admin | team_admin | member | auditor |
|---|---|---|---|---|---|
| Add members and change roles | any role | not owner | no | no | no |
| See the member list | yes | yes | yes | no | yes |
| Read and write shared documents | yes | no | yes | yes | no |
| Delete shared documents | any | no | any | own only | no |
| Read the organization audit log | yes | yes | no | no | yes |
| Request break-glass access | yes | yes | no | no | no |
| Approve break-glass access | yes (not their own request) | no | no | no | no |
| Read someone's private chats, documents or memory | no | no | no | no | no |

## Not required yet (planned)

Rate limiting, multi-factor authentication, single sign-on, TLS, encryption at rest, organization-level model and tool policies. See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).
