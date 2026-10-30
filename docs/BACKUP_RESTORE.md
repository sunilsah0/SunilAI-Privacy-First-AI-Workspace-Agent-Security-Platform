# Backup and restore (Docker release)

These steps are **manual**. They are not automated and have not been tested in CI.

## Back up

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
docker compose -f docker-compose.release.yml exec -T db sh -c "pg_dump -U verity -Fc verity -f /tmp/verity.dump"
docker compose -f docker-compose.release.yml cp db:/tmp/verity.dump backups/verity-backup.dump
docker compose -f docker-compose.release.yml exec -T db rm /tmp/verity.dump
```

The dump is written inside the container and copied out with `docker compose cp`. Do not use PowerShell's `>` to save a database dump, because it can corrupt binary files.

## Protect the backup

A backup contains everyone's private data. Encrypt it with a maintained tool such as 7-Zip (AES-256) or `age`, keep the key somewhere else, and do not store it next to the data it protects. Do not invent your own encryption.

## Restore into a fresh stack

```powershell
docker compose -f docker-compose.release.yml up -d db
docker compose -f docker-compose.release.yml run --rm migrate
docker compose -f docker-compose.release.yml cp backups/verity-backup.dump db:/tmp/restore.dump
docker compose -f docker-compose.release.yml exec -T db pg_restore -U verity -d verity --clean --if-exists --no-owner /tmp/restore.dump
docker compose -f docker-compose.release.yml exec -T db rm /tmp/restore.dump
docker compose -f docker-compose.release.yml up -d
```

Running `migrate` first creates the limited database account and the structure. The restore then replaces the data. Use the same `DB_APP_PASSWORD` in `.env` as when the backup was made.

## Check that the access rules survived

Open **Privacy status** in the web app. The checks "Database account cannot bypass row security", "Row-Level Security on all user-data tables" and "Audit log cannot be edited or deleted by the app" should all say `verified`. Then log in as two different people and confirm each sees only their own data.

## Limits

- Restore and the checks above are done by hand.
- Old backups keep data that people later deleted.
- Model files live in the `ollama` volume and are not part of this backup (they can be downloaded again).
