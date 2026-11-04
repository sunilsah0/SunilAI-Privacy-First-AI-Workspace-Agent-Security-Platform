# SunilAI Personal edition

One person, one computer. Your documents and chats stay in your own database, and the AI model runs on your machine.

## Install (about 15 minutes, mostly downloading)

1. Install **Docker Desktop** (Windows or macOS) or Docker Engine (Linux) and start it.
2. Unzip this folder somewhere you will keep it.
3. Windows: open PowerShell in this folder and run
   `powershell -ExecutionPolicy Bypass -File .\install.ps1`
   Linux or macOS: run `bash install.sh`
4. Open http://localhost:8080 and create your account. The **first account becomes the owner; after that, sign-up closes.**

The installer creates a `.env` file with fresh random secrets. Keep it private and back it up. It never replaces an existing `.env`.

## Everyday use

- Start and stop: `docker compose -f docker-compose.release.yml up -d` and `... down`
- Your data lives in Docker volumes. See `docs/BACKUP_RESTORE.md`.
- Update: unzip the newer package into a new folder, copy your `.env` into it, and run the installer again.

## Read before trusting it

SunilAI is a learning project and has not been independently audited. Read `docs/KNOWN_LIMITATIONS.md`.
