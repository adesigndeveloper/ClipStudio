#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -d .venv ] || { echo "Setting up for the first time..."; python3 -m venv .venv; }
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -U -r requirements.txt
( sleep 2; (command -v open >/dev/null && open http://localhost:8000) || (command -v xdg-open >/dev/null && xdg-open http://localhost:8000) ) &
python app.py
