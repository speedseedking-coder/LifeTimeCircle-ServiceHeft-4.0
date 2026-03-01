#!/usr/bin/env bash
set -euo pipefail

HOST_ADDR="${HOST_ADDR:-127.0.0.1}"
PORT="${PORT:-8000}"
RELOAD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST_ADDR="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --no-reload)
      RELOAD=0
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  REPO_ROOT="$git_root"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

SERVER_DIR="$REPO_ROOT/server"
if [[ ! -d "$SERVER_DIR" ]]; then
  echo "Server directory not found: $SERVER_DIR" >&2
  exit 1
fi

if [[ -z "${LTC_SECRET_KEY:-}" || "${#LTC_SECRET_KEY}" -lt 16 ]]; then
  export LTC_SECRET_KEY="dev_test_secret_key_32_chars_minimum__OK"
fi

if [[ -z "${LTC_ENV:-}" ]]; then
  export LTC_ENV="dev"
fi

echo "Repo: $REPO_ROOT"
echo "Server: $SERVER_DIR"
echo "LTC_ENV=$LTC_ENV"
echo "LTC_SECRET_KEY len=${#LTC_SECRET_KEY}"
echo "Starting API: http://$HOST_ADDR:$PORT"

cd "$SERVER_DIR"

args=(app.main:app --host "$HOST_ADDR" --port "$PORT")
if [[ "$RELOAD" -eq 1 ]]; then
  args+=(--reload)
fi

exec poetry run uvicorn "${args[@]}"
