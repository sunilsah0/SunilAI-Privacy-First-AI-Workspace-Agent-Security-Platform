# Privacy design

## Where each kind of data lives

| Data | Stored in | Who can read it | Leaves the device? |
|---|---|---|---|
| Account (email, password hash) | `users` table | the API; other users can look up an email address during login and sign-up | no |
| Personal documents (extracted text) | `documents` table | the owner only (break-glass excepted) | no |
| Search data (chunks and embeddings) | `chunks` table | the owner only | no |
| Conversations and messages | `conversations`, `messages` | the owner only | no |
| Tool permissions, pending approvals, personal activity log | own tables | the owner only | no |
| Settings (retention) | `user_settings` | the owner only | no |
| Shared organization documents | `org_documents` | owner, team admin, member roles | no |
| Organization audit log | `org_audit_events` | owner, security admin, auditor | no |
| Break-glass requests and access log | `break_glass_*` | requester, org owners and auditors; the affected person sees approved access and reads | no |
| Uploaded files | not kept as files | only their extracted text is stored | no |

## What the app sends over the network

- **Normal use:** nothing leaves the computer. The model runs in Ollama on the same machine (or on the private Docker network).
- **Downloads:** model files are downloaded by Ollama (development) or by the one-off `model-puller` step (release). These are the only planned internet uses.
- **Optional probe:** the privacy page can make one connection attempt to `1.1.1.1:443` when you ask it to. No data is sent.
- **Telemetry:** the app contains no analytics or telemetry code. Ollama and Docker are separate programs with their own behavior, and Ollama's cloud features can be switched off with `OLLAMA_NO_CLOUD=1` (the release compose file does this).

## What admins can and cannot see

- Admin roles manage people and see audit logs. They cannot read private content.
- Break-glass access shows the affected person who read what and when.

## Data protection we have **not** built

Encryption at rest inside the app and key management (use full-disk encryption such as BitLocker), TLS (the release serves plain HTTP on `127.0.0.1` only), and anonymization of audit logs beyond blanking a deleted person's identity.

See [DATA_LIFECYCLE.md](DATA_LIFECYCLE.md) for retention, export and deletion.
