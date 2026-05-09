#!/bin/sh
set -e

python3 -m pytest
PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile \
  cloudsaver/core.py \
  cloudsaver/web_server.py \
  cloudsaver/history.py \
  cloudsaver/desktop.py
node --check web/app.js
python3 -m cloudsaver --help >/dev/null
python3 -m cloudsaver.web_server --help >/dev/null
python3 -m cloudsaver.desktop --help >/dev/null
python3 -m build --no-isolation
