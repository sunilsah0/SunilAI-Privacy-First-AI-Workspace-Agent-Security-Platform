# SunilAI-Privacy-First AI Workspace & Agent Security Platform

A privacy-first AI workspace with a permission layer that sits **outside** the AI model.

## Try it

- **Download:** go to the [Releases page](https://github.com/YOUR-NAME/YOUR-REPO/releases/latest) and pick **Personal** (one person, own computer) or **Enterprise** (a team, on a server).
- **Live demo:** https://demo.yourdomain.com (simulated AI, wiped every night, please enter no real information) *(add once it is running)*

## How to use it

1. Install Docker, unzip the package, run the installer (`install.ps1` on Windows, `bash install.sh` on Linux or macOS).
2. Open the address it prints and create your account.
3. **Chat** with a model that runs on your own machine. **Documents:** upload `.txt`, `.md` or `.pdf` files and search them. **Agent:** choose what the AI is allowed to do; risky actions wait for your approval. **Privacy:** see which checks were verified and which are only settings.
4. Your data stays in your own database. Download it or delete your account any time from **My data**.

SunilAI is a learning project and has not been independently audited. See docs/KNOWN_LIMITATIONS.md.

It runs a local model (Ollama), keeps your data in your own PostgreSQL database, and enforces who can see what **inside the database**, not only in the app code or in prompts.

> **Status: working prototype, built step by step as a learning project.**
> It has **not** been independently audited or certified. Read [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) before trusting it with real data.

## What it does

- **Personal workspace:** chat with a local model, upload `.txt`, `.md` and `.pdf` files, search them by meaning, keep conversation history.
- **Agent permissions:** the AI can only *propose* actions. A policy engine outside the model decides. Risky actions wait for your approval, and every decision goes to an audit log.
- **Organizations (enterprise mode):** five roles (owner, security admin, team admin, member, auditor), shared documents, an organization audit log, and tenant isolation enforced by PostgreSQL Row-Level Security.
- **Admins are not snoops:** no role can read another person's private chats or documents. Exceptional access ("break-glass") needs a written reason, a second owner, a time limit, is read-only, and the affected person can see it.
- **Your data:** export everything, delete your account, set automatic conversation cleanup.
- **Privacy status page:** every claim is labelled `verified`, `configured`, `unverified` or `failed`.

## Quick start: development (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d                      # development database on port 5433
alembic upgrade head
ollama pull llama3.2:3b
ollama pull nomic-embed-text
uvicorn services.api.app.main:app --reload

# in a second terminal
cd apps\web
npm ci
npm run dev                               # http://localhost:5173
```

Tip: set the environment variable `OLLAMA_NO_CLOUD=1` for your own Ollama so its optional cloud features stay off.

## Quick start: Docker release

```powershell
copy .env.example .env                    # then replace all three CHANGE_ME values with random hex strings
python -c "import secrets; print(secrets.token_hex(32))"   # run it three times
docker compose -f docker-compose.release.yml up -d --build
docker compose -f docker-compose.release.yml --profile setup run --rm model-puller   # downloads the models (uses the internet)
# open http://localhost:8080
python scripts\verify_docker_offline.py   # proves the API container has no route to the internet
```

## Run the checks

```powershell
pytest                                    # backend and security tests (needs the development database)
cd apps\web
npm run lint
npm run build
```

## What we claim, and what we do not

We claim only what a test or a script demonstrates. [docs/TEST_COVERAGE.md](docs/TEST_COVERAGE.md) maps each claim to its evidence.

We do **not** claim: that it is "100% private", "fully secure", audited, certified, encrypted at rest, or ready for regulated data.

## Documentation

| File                                                              | What it is                                         |
| ----------------------------------------------------------------- | -------------------------------------------------- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)                       | components, trust boundaries, request flow         |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)                       | what we defend against, and what we do not         |
| [docs/SECURITY_REQUIREMENTS.md](docs/SECURITY_REQUIREMENTS.md)     | numbered requirements and the role matrix          |
| [docs/PRIVACY_DESIGN.md](docs/PRIVACY_DESIGN.md)                   | where data lives and what leaves the device        |
| [docs/DATA_LIFECYCLE.md](docs/DATA_LIFECYCLE.md)                   | retention, export, deletion                        |
| [docs/BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md)                   | backup and restore steps                           |
| [docs/COMPETITOR_ANALYSIS.md](docs/COMPETITOR_ANALYSIS.md)         | similar tools, from their public documentation     |
| [docs/PRODUCT_DIFFERENTIATION.md](docs/PRODUCT_DIFFERENTIATION.md) | five testable differences, with limits             |
| [docs/TEST_COVERAGE.md](docs/TEST_COVERAGE.md)                     | the original 25 test requirements and their status |
| [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)             | everything that is missing or weak                 |
| [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md)         | what is done and what comes next                   |
| [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md)                       | current state and test results                     |


