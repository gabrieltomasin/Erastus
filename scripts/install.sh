#!/bin/sh
# Erastus one-line installer.
#
#   curl -fsSL https://raw.githubusercontent.com/gabrieltomasin/erastus/main/scripts/install.sh | sh
#
# Non-interactive and pipe-safe (reads nothing from stdin). Overrides:
#   ERASTUS_DIR             install location            (default: ./erastus)
#   ERASTUS_REPO            repository URL              (default: the GitHub repo)
#   ERASTUS_SKIP_GPU_CHECK=1  proceed without a working NVIDIA GPU
set -eu

REPO_URL="${ERASTUS_REPO:-https://github.com/gabrieltomasin/erastus.git}"
INSTALL_DIR="${ERASTUS_DIR:-./erastus}"
CDI_SPEC=/var/run/cdi/nvidia.yaml

if [ -t 1 ]; then
  B='\033[1m'; R='\033[0m'
  BLUE="${B}\033[34m"; YELLOW="${B}\033[33m"; RED="${B}\033[31m"; GREEN="${B}\033[32m"
else
  BLUE=''; YELLOW=''; RED=''; GREEN=''; R=''
fi

log()   { printf "${BLUE}==>${R} %s\n" "$*"; }
ok()    { printf "${GREEN}==>${R} %s\n" "$*"; }
warn()  { printf "${YELLOW}warning:${R} %s\n" "$*"; }
die()   { printf "${RED}error:${R} %s\n" "$*" >&2; exit 1; }

# --- Preflight -------------------------------------------------------------

command -v git >/dev/null 2>&1 || die "git is required: https://git-scm.com/downloads"
command -v docker >/dev/null 2>&1 || die "Docker is required: https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || \
  die "Docker Compose v2 is required (the 'docker compose' plugin)."

if nvidia-smi >/dev/null 2>&1; then
  GPU=1
else
  GPU=0
  [ "${ERASTUS_SKIP_GPU_CHECK:-0}" = "1" ] || die "No working NVIDIA GPU found.
    The transcription worker needs one. Install the NVIDIA driver and
    nvidia-container-toolkit, or set ERASTUS_SKIP_GPU_CHECK=1 to install anyway."
fi

# --- Clone / update ----------------------------------------------------------

if [ -d "$INSTALL_DIR/.git" ]; then
  log "Updating existing repository in $INSTALL_DIR"
  git -C "$INSTALL_DIR" pull --ff-only
else
  log "Cloning repository into $INSTALL_DIR"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# --- Environment -------------------------------------------------------------

if [ ! -f .env ]; then
  cp .env.example .env
  ok "Created .env from .env.example"
else
  log "Keeping existing .env"
fi

# --- NVIDIA CDI spec ---------------------------------------------------------
# A missing (or stale, after a driver update) CDI spec makes the worker
# container fail to create.
if [ "$GPU" = 1 ] && [ ! -f "$CDI_SPEC" ]; then
  if command -v nvidia-ctk >/dev/null 2>&1; then
    log "Generating NVIDIA CDI spec"
    nvidia-ctk cdi generate --output="$CDI_SPEC" >/dev/null 2>&1 ||
      warn "could not write $CDI_SPEC (permissions?). Run:
    sudo nvidia-ctk cdi generate --output=$CDI_SPEC"
  else
    warn "nvidia-ctk not found. Install nvidia-container-toolkit, then run:
    sudo nvidia-ctk cdi generate --output=$CDI_SPEC"
  fi
fi

# --- Build & start -----------------------------------------------------------

log "Building and starting services (first build downloads several GB)"
docker compose up -d --build

log "Waiting for the database"
POSTGRES_ID=$(docker compose ps -q postgres)
i=0
while [ "$i" -lt 60 ]; do
  status=$(docker inspect -f '{{.State.Health.Status}}' "$POSTGRES_ID" 2>/dev/null || echo starting)
  [ "$status" = "healthy" ] && break
  i=$((i + 1))
  sleep 2
done
[ "$status" = "healthy" ] || die "Postgres did not become healthy. Check: docker compose logs postgres"

log "Running database migrations"
i=0
while [ "$i" -lt 30 ]; do
  docker compose exec -T backend alembic upgrade head && break
  i=$((i + 1))
  sleep 2
done
[ "$i" -lt 30 ] || die "Migrations failed. Check: docker compose logs backend"

# --- Done --------------------------------------------------------------------

ok "Erastus is running!"
printf '\n'
printf '  Frontend:  %s\n' "http://localhost:3000"
printf '  API:       %s\n' "http://localhost:8000/api/health"
printf '\n'
warn "one step left: add your LLM key to $INSTALL_DIR/.env"
printf '\n'
printf '    LLM_API_BASE_URL=https://api.deepseek.com   (or OpenRouter, etc.)\n'
printf '    LLM_API_KEY=sk-...\n'
printf '    LLM_MODEL=deepseek-chat\n'
printf '\n'
printf 'then apply it:\n\n'
printf '    cd %s && docker compose up -d   # recreates containers with the new env\n' "$INSTALL_DIR"
printf '\n'
printf 'Useful commands:\n\n'
printf '    docker compose logs -f        # follow all logs\n'
printf '    docker compose logs -f worker # watch transcription/summarization\n'
printf '    docker compose down           # stop everything\n'
