#!/bin/bash
set -e
export PORT="${PORT:-10000}"
export PYTHONUNBUFFERED=1
echo "[start] PORT=$PORT"
echo "[start] python: $(which python3) $(python3 --version 2>&1)"
echo "[start] gunicorn: $(which gunicorn) $(gunicorn --version 2>&1 | head -1)"
echo "[start] files:"
ls -la .
echo "[start] alert/:"
ls alert/
exec gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --threads 2 --timeout 120 alert.server:app
