#!/bin/sh
set -eu

# Unified production entrypoint for Railway/Render/Docker/Procfile.
exec gunicorn --bind "0.0.0.0:${PORT:-8080}" app:app
