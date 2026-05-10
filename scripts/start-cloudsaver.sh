#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

PYTHON_BIN=${PYTHON:-python3}
HOST=${CLOUDSAVER_HOST:-127.0.0.1}
PORT=${CLOUDSAVER_PORT:-8765}

cd "$REPO_ROOT"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "CloudSaver could not find Python: $PYTHON_BIN" >&2
  echo "Set PYTHON=/path/to/python or install Python 3.10+." >&2
  exit 1
fi

if [ -x ".venv/bin/python" ] && [ "${PYTHON:-}" = "" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

echo "Starting CloudSaver at http://$HOST:$PORT"
exec "$PYTHON_BIN" -m cloudsaver.web_server --host "$HOST" --port "$PORT"
