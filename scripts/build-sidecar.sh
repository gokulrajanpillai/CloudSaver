#!/usr/bin/env bash
set -euo pipefail

# Accept Rust target triple as first arg (e.g. aarch64-apple-darwin).
# Auto-detect when omitted (for local builds).
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  OS=$(python3 -c "
import platform
s = platform.system()
print('apple-darwin' if s == 'Darwin' else 'pc-windows-msvc' if s == 'Windows' else 'unknown-linux-gnu')
")
  ARCH=$(python3 -c "import platform; print('aarch64' if platform.machine() in ('arm64', 'aarch64') else 'x86_64')")
  TARGET="${ARCH}-${OS}"
fi

BINARY_NAME="cloudsaver-sidecar-${TARGET}"

python3 -m pip install pyinstaller -r requirements.txt -e ".[sidecar,image_extras]"

pyinstaller \
  --onefile \
  --name "$BINARY_NAME" \
  --hidden-import "uvicorn.logging" \
  --hidden-import "uvicorn.protocols.http.auto" \
  --hidden-import "uvicorn.protocols.websockets.auto" \
  --hidden-import "uvicorn.lifespan.on" \
  --collect-all googleapiclient \
  src-python/sidecar_main.py

mkdir -p src-tauri/binaries

# PyInstaller appends .exe on Windows automatically
if [[ "$TARGET" == *"windows"* ]]; then
  cp "dist/${BINARY_NAME}.exe" "src-tauri/binaries/${BINARY_NAME}.exe"
else
  cp "dist/${BINARY_NAME}" "src-tauri/binaries/${BINARY_NAME}"
fi
