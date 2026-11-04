#!/usr/bin/env bash
# SunilAI installer for Linux and macOS. Run it from this folder:   bash install.sh
# Options:
#   --skip-models          do not download the AI models now
#   --domain NAME          serve over HTTPS on this domain (needs --email)
#   --email ADDRESS        email for certificate notices
#   --preset FILE          settings template to start from (default .env.template)
set -euo pipefail
cd "$(dirname "$0")"

SKIP_MODELS=0
DOMAIN=""
EMAIL=""
PRESET=".env.template"
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-models) SKIP_MODELS=1 ;;
    --domain) DOMAIN="${2:-}"; shift ;;
    --email) EMAIL="${2:-}"; shift ;;
    --preset) PRESET="${2:-}"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

command -v docker >/dev/null 2>&1 || { echo "Docker is not installed. Install Docker first, then run this again."; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker is installed but not reachable. Start it, or check that your user may run docker."; exit 1; }
if [ -n "$DOMAIN" ] && [ -z "$EMAIL" ]; then echo "--domain also needs --email"; exit 1; fi

# Random secrets come from the operating system's random source.
secret() { head -c "$1" /dev/urandom | od -An -tx1 | tr -d ' \n'; }

INVITE=""
if [ -f .env ]; then
  echo ".env already exists, so I am keeping your existing settings and secrets."
else
  [ -f "$PRESET" ] || { echo "$PRESET is missing from this folder."; exit 1; }
  : > .env
  chmod 600 .env
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in
      INVITE_CODE=CHANGE_ME) INVITE="$(secret 12)"; echo "INVITE_CODE=$INVITE" >> .env ;;
      *=CHANGE_ME) echo "${line%%=*}=$(secret 32)" >> .env ;;
      *) echo "$line" >> .env ;;
    esac
  done < "$PRESET"
  if [ -n "$DOMAIN" ]; then
    { echo "SITE_ADDRESS=$DOMAIN"; echo "ACME_EMAIL=$EMAIL"; } >> .env
  fi
  echo "Created .env with fresh random secrets. Keep it private and back it up."
fi

FILES=(-f docker-compose.release.yml)
if tr -d '\r' < .env | grep -q '^SITE_ADDRESS='; then
  FILES+=(-f docker-compose.https.yml)
fi

docker compose "${FILES[@]}" up -d --build

if [ "$SKIP_MODELS" -eq 0 ] && ! tr -d '\r' < .env | grep -q '^MODEL_PROVIDER=fake$'; then
  echo "Downloading the AI models (this is the only step that uses the internet at run time)..."
  docker compose "${FILES[@]}" --profile setup run --rm model-puller
fi

SITE="$(tr -d '\r' < .env | sed -n 's/^SITE_ADDRESS=//p')"
if [ -n "$SITE" ]; then
  case "$SITE" in http*) URL="$SITE" ;; *) URL="https://$SITE" ;; esac
else
  URL="http://localhost:8080"
fi
echo
echo "SunilAI is starting. Open: $URL"
if [ -n "$INVITE" ]; then
  echo "Invite code for new accounts (share it only with people you trust): $INVITE"
fi
