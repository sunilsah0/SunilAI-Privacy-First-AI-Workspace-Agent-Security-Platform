#!/usr/bin/env bash
# Deletes ALL accounts and data on a DEMO server. It refuses to run anywhere else.
# Schedule it nightly with cron, for example:
#   0 3 * * * /home/deploy/sunilai/scripts/wipe_demo.sh >> /home/deploy/sunilai-wipe.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."

if ! tr -d '\r' < .env | grep -q '^DEMO_MODE=1$'; then
  echo "Refusing to wipe: DEMO_MODE=1 is not set in .env. This script is only for demo servers."
  exit 1
fi

FILES=(-f docker-compose.release.yml)
if tr -d '\r' < .env | grep -q '^SITE_ADDRESS='; then
  FILES+=(-f docker-compose.https.yml)
fi
compose() { docker compose "${FILES[@]}" "$@"; }

echo "$(date -u +%FT%TZ) wiping demo data"
compose stop api
compose exec -T db psql -U verity -d verity -v ON_ERROR_STOP=1 -c "TRUNCATE users, organizations CASCADE;"
compose start api
echo "$(date -u +%FT%TZ) done"
