@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Setting up for the first time...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -q --upgrade pip
python -m pip install -q -U -r requirements.txt
start "" http://localhost:8000
python app.py
pause
