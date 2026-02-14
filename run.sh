#!/bin/bash

# Resolve real script location (follow symlink)
SCRIPT_PATH="$(readlink -f "$0")"
REPO_DIR="$(dirname "$SCRIPT_PATH")"

VENV_DIR="$REPO_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in repo..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip >/dev/null
pip install cryptography >/dev/null

python "$REPO_DIR/btc_tracker.py" "$@"

deactivate
