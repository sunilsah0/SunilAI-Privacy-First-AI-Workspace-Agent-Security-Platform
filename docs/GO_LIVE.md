# Going live on a server

A checklist for putting SunilAI on a small Linux server with HTTPS. Pick the kind of installation first:

| Kind | Preset | AI | Who signs up | Needs |
|---|---|---|---|---|
| Public demo | `.env.demo.example` | simulated | anyone, rate-limited | nightly wipe, privacy notice |
| Team (enterprise) | `.env.enterprise.example` | local model | people with the invite code | backups, enough CPU and RAM for the model |
| Personal | `.env.personal.example` | local model | first account only | usually your own computer, not a server |

## 1. The server

- A small VPS running a current Ubuntu LTS. Prefer a region that fits your data-protection needs (for Sweden, the EU).
- Log in with an SSH key. Turn off password logins. Create a normal user for day-to-day work.
- Turn on automatic security updates (`unattended-upgrades`).
- Firewall: allow SSH, 80 and 443 only (`ufw allow OpenSSH`, `ufw allow 80/tcp`, `ufw allow 443/tcp`, `ufw enable`). Docker edits the firewall itself when it publishes ports. In this setup only the HTTPS service publishes ports (80 and 443), so nothing else is exposed. Check with `docker ps`.
- Install Docker Engine by following Docker's official instructions for your system.

## 2. The domain

Create a DNS "A" record that points your name (for example `demo.example.com`) at the server's address. Wait until `ping demo.example.com` shows that address. Caddy needs this before it can get a certificate.

## 3. Install

Using a downloaded package (team installation):

```bash
unzip SunilAI-enterprise-v0.1.0.zip && cd SunilAI-enterprise-v0.1.0
bash install.sh --domain demo.example.com --email you@example.com
```

Using the repository (public demo):

```bash
git clone https://github.com/YOUR-NAME/YOUR-REPO.git sunilai && cd sunilai
bash install.sh --preset .env.demo.example --skip-models --domain demo.example.com --email you@example.com
```

The installer writes `.env` with fresh random secrets, builds everything and starts it. The first start downloads and builds images, which takes several minutes.

## 4. Check it

- Open `https://demo.example.com`. The browser should show a valid padlock.
- Sign in, then open the **Privacy** page. The database checks should say verified.
- Run the network check from the project folder: `python3 scripts/verify_docker_offline.py` (it should report no internet from the API container).
- `docker compose -f docker-compose.release.yml -f docker-compose.https.yml ps` should show everything running.

## 5. Keep it healthy

- **Demo only:** schedule the nightly wipe. Run `crontab -e` and add
  `0 3 * * * /home/YOUR-USER/sunilai/scripts/wipe_demo.sh >> /home/YOUR-USER/sunilai-wipe.log 2>&1`
- **Team installation:** back up on a schedule and test a restore (`docs/BACKUP_RESTORE.md`). Keep `.env` safe: it holds the secrets that protect the data.
- Use any free uptime checker to alert you if the site stops answering.
- **Update:** put the new package or code in place, keep `.env`, and run the same `docker compose ... up -d --build` command. Check the Privacy page afterwards.

## 6. People and law

- Edit `apps/web/public/privacy-notice.html`, replacing every [square bracket]. Link it where people sign up (the sign-in page already links to it).
- You are responsible for visitors' data. If you collect other people's personal data, check the rules that apply to you. This is not legal advice.
- Never describe the service as audited, certified or "100% private".

## 7. If something goes wrong

- Stop everything: `docker compose -f docker-compose.release.yml -f docker-compose.https.yml down`
- Suspect a leaked secret? Stop the service, replace the values in `.env` (new `SECRET_KEY` signs everyone out), and start again. A changed `DB_APP_PASSWORD` or `DB_OWNER_PASSWORD` also needs the database passwords changed inside PostgreSQL.
- Report security problems you find through the private reporting link in `SECURITY.md`.
