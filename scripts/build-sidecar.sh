#!/usr/bin/env bash
set -euo pipefail

PLATFORM=$(python3 -c "import platform; p = platform.system().lower(); print({'darwin':'macos','windows':'windows'}.get(p, p))")
ARCH=$(python3 -c "import platform; print('aarch64' if platform.machine() in ('arm64','aarch64') else 'x86_64')")

python3 -m pip install pyinstaller -r requirements.txt -e ".[sidecar,image_extras]"

pyinstaller \
  --onefile \
  --name "cloudsaver-sidecar-${PLATFORM}-${ARCH}" \
  --hidden-import "uvicorn.logging" \
  --hidden-import "uvicorn.protocols.http.auto" \
  --hidden-import "uvicorn.protocols.websockets.auto" \
  --hidden-import "uvicorn.lifespan.on" \
  --collect-all googleapiclient \
  src-python/sidecar_main.py

mkdir -p src-tauri/binaries
cp "dist/cloudsaver-sidecar-${PLATFORM}-${ARCH}" "src-tauri/binaries/"
