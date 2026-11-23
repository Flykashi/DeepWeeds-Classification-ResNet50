@echo off
REM Starts the Weed Classification app (API + frontend) on http://127.0.0.1:8000/app/
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Virtual environment not found. Run the setup steps in README.md first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
start "" http://127.0.0.1:8000/app/
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
