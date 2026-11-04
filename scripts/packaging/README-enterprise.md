# SunilAI Enterprise edition

For a team: organizations, five roles, shared documents, an organization audit log and an emergency-access (break-glass) process. New accounts need the **invite code**.

## Install on a Linux server (recommended)

1. A small server with Docker Engine, ports 80 and 443 open, and a domain name pointing at it.
2. Unzip this folder and run:
   `bash install.sh --domain chat.example.com --email you@example.com`
3. The installer prints an **invite code**. Share it only with people you trust. Open `https://chat.example.com` and register the first account.
4. Make that first account the owner of an organization (Organization tab), then add colleagues with their roles.

Trying it on your own computer instead? Run `bash install.sh` (or `install.ps1` on Windows) without a domain, then open http://localhost:8080.

## Operate it

- Follow `docs/GO_LIVE.md` for the server checklist, backups and updates.
- No role can read another person's private content. Exceptional access needs two owners and is visible to the person.
- Back up regularly (`docs/BACKUP_RESTORE.md`) and test a restore.

## Read before trusting it

SunilAI is a learning project and has not been independently audited. Read `docs/KNOWN_LIMITATIONS.md`.
