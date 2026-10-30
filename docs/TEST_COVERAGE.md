# Test coverage against the original 25 requirements

Status: **done** (automated test), **partial**, **manual** (a documented procedure, not automated), **not built**, **n/a**.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | User A cannot retrieve User B's document | done | `test_isolation.py` |
| 2 | User A cannot search User B's index | done | `test_rag.py::test_search_never_returns_another_users_chunks` |
| 3 | User A cannot read User B's conversations | done | `test_chat.py` |
| 4 | User A cannot read User B's personal memory | not built | there is no separate memory feature (documents and conversations are covered) |
| 5 | Another organization's agent definitions and permissions | partial | tool permissions are per user (`test_agent.py::test_permissions_are_per_user`); organization-level agent definitions are not built |
| 6 | Another user's cached response | n/a | the app does not cache model responses |
| 7 | Removing access revokes future requests | done | `test_orgs.py` (suspension), `test_privacy_rights.py` (account deletion) |
| 8 | Unauthorized export fails | done | `test_privacy_rights.py` (export needs login and returns only your data) |
| 9 | Agent cannot use a tool without permission | done | `test_agent.py` |
| 10 | Malicious document cannot grant permissions | done | `test_agent.py` |
| 11 | Unauthorized external transmission is blocked | done | `test_agent.py`, `test_network.py` |
| 12 | Tool cannot leave its resource boundary | done | `test_agent.py::test_agent_cannot_touch_another_users_document` |
| 13 | Sensitive actions need approval | done | `test_agent.py` |
| 14 | Background jobs cannot bypass authorization | done | `test_privacy_rights.py` (retention job). It is the only background job. |
| 15 | Offline inference works without internet | manual | try it with the network off. Not automated. |
| 16 | Cloud fallback disabled | done | `test_chat.py`, `test_network.py`, `test_release_config.py` |
| 17 | Unauthorized outbound connections blocked by an enforcement mechanism | partial | in-app guard is automated (`test_network.py`); Windows firewall (`test_os_enforcement.py`) and Docker (`scripts/verify_docker_offline.py`) are manual |
| 18 | Prompts not sent to telemetry | partial | the code contains no telemetry; not verified with network capture |
| 19 | Secrets not in ordinary logs | partial | `test_logging.py` checks logs during tests only |
| 20 | Temporary data and deletion behavior | partial | deletion is tested (`test_rag.py`, `test_privacy_rights.py`); the app writes no temporary files by design, not tested |
| 21 | Tenant-scoped queries cannot return another tenant's data | done | `test_orgs.py` |
| 22 | Row-Level Security works with the real app account | done | `test_rls.py` |
| 23 | Connection pooling cannot leak identity | done | `test_rls.py::test_pooled_connection_does_not_leak_identity` |
| 24 | Migrations preserve security policies | partial | CI creates a fresh database with the migrations and tests the policies; there is no upgrade/downgrade cycle test |
| 25 | Backups and restores keep access boundaries | manual | [BACKUP_RESTORE.md](BACKUP_RESTORE.md) |
