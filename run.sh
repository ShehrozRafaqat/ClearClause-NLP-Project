#!/usr/bin/env bash
set -euo pipefail

VENV="/home/shehroz/Documents/genai-course/.venv"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$APP_DIR"
"$VENV/bin/streamlit" run app.py --server.address 127.0.0.1 --server.port 8502

