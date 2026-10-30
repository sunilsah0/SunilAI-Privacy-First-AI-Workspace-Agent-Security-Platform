# Build status

Last updated: end of Phase 11B.

## Completed work

Phases 1 to 11 of the roadmap (see [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)).

## Test results

- Backend: `pytest` should report **111 passed, 1 skipped** (the skipped test is the Windows firewall test, run only after `scripts/offline-on.ps1`). Run it to confirm for your checkout.
- Web: `npm run lint` and `npm run build` pass.
- CI: backend, web and container jobs run on every push.

## Manual checks (not in CI)

- `python scripts\verify_docker_offline.py` (Docker network)
- `scripts\check_network.py` with `scripts\offline-on.ps1` (Windows firewall)
- Backup and restore ([BACKUP_RESTORE.md](BACKUP_RESTORE.md))

## Unresolved issues

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md). The most important: no rate limiting, no TLS, no encryption at rest, no independent audit.

## Next tasks

See "Next, in a sensible order" in [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md).
