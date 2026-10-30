# Threat model

Scope: the VerityAI API, database, web app and Docker release. Reference list: the OWASP Top 10 for LLM Applications (2025 edition), especially LLM01 prompt injection, LLM02 sensitive information disclosure, LLM06 excessive agency and LLM08 vector and embedding weaknesses.

## What we protect

Documents, conversations, embeddings, tool permissions, activity logs, organization data, credentials and tokens.

## Who we worry about

- A curious or malicious **user** who wants another user's or another company's data.
- A malicious **document or web text** that tries to steer the AI.
- A **tricked or buggy model**.
- An **organization admin** who should manage people but not read their private content.
- A **network attacker** or a program trying to send data out.
- A **developer mistake** (for example a forgotten owner check).

## Threats, defenses and evidence

| ID | Threat | Defense | Evidence | Remaining risk |
|---|---|---|---|---|
| T1 | Guessing another user's document or chat ID | Owner filter in every query, same 404 for "not yours" and "does not exist", random UUIDs | `test_isolation.py`, `test_chat.py` | none known for tested cases |
| T2 | A forgotten owner check leaks rows | Row-Level Security as a second layer, enforced for the app account | `test_rls.py` | tables added later must get RLS (a guard test checks this) |
| T3 | Crossing from one company to another | RLS on every table with `org_id`; outsiders get 404 | `test_orgs.py` | the database trusts the identity the API sets |
| T4 | Admin reads private content | Role matrix; admin roles have no content access; only break-glass can read | `test_orgs.py`, `test_breakglass.py` | break-glass exposes all of a person's documents |
| T5 | Prompt injection through documents (LLM01) | Retrieved text labelled as data; permissions live outside the model | `test_agent.py::test_malicious_document_cannot_trigger_delete` | the model can still say misleading things in chat |
| T6 | Excessive agency (LLM06) | Tool registry, risky tools off by default, human approval, stored arguments, rules re-checked at approval | `test_agent.py` | single-step tools only |
| T7 | Retrieval leaks another user's text (LLM02, LLM08) | Authorization before retrieval, owner filter plus RLS on embeddings | `test_rag.py::test_ai_prompt_contains_only_own_document_text` | embedding attacks beyond access control are not studied |
| T8 | Data sent to the internet | In-app guard; Windows firewall script; Docker internal network | `test_network.py`; manual scripts | guard covers only this process; firewall and Docker checks are manual |
| T9 | Silent fallback to a cloud model | Model host must be local or listed; failure returns 503; Ollama cloud features disabled | `test_chat.py`, `test_network.py`, `test_release_config.py` | Ollama is a separate program |
| T10 | Token theft or forgery | 30-minute tokens, a required strong secret in production, token kept in page memory | `test_security_config.py` | no server-side logout; no refresh or revocation list |
| T11 | Password guessing | Argon2 password hashing, same error for wrong email and wrong password | `test_auth.py` | **no rate limiting or lockout** |
| T12 | SQL injection | Bound parameters only | code review | not scanned automatically |
| T13 | Malicious or huge uploads | Type allowlist, 5 MB limit, chunk limit, nothing saved on failure | `test_rag.py` | PDF parsing runs inside the API process |
| T14 | Audit tampering | The app account can only insert and read audit tables | `test_agent.py`, `test_orgs.py`, `test_breakglass.py` | someone with the owner account can still change them |
| T15 | Break-glass abuse | Reason, second owner, 60-minute cap in the database, read-only, person can see access | `test_breakglass.py` | needs two admins; reasons are not verified |
| T16 | Vulnerable dependencies or images | Dependabot, `pip-audit`, `npm audit` (informational) | CI | images not pinned by digest; no triage process yet |
| T17 | Exposed model server | No host port in the release; localhost in development | `test_release_config.py` | Ollama has no built-in authentication |
| T18 | Script injection in the web app | React escapes text; Content-Security-Policy in the gateway | none automated | CSP still allows inline styles |
| T19 | Resource exhaustion | Size limits only | none | **no rate limits** |

## Out of scope

A compromised computer or database host, a malicious database administrator, hardware and side-channel attacks, and model-training data issues.

## Assumptions

The host is trusted. The database is reachable only from the API. Secrets are generated randomly and kept out of Git.
