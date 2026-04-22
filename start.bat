@echo off
cd /d "%~dp0"
echo ═══════════════════════════════════════════
echo       QUANTRA TRADING BOT — LAUNCHER
echo ═══════════════════════════════════════════
echo.
echo [1/2] Starting Quantra backend on port 8000...
start cmd /k "cd /d "%~dp0" && python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo [2/2] Opening Quantra UI...
start "" "%~dp0ui\index.html"
echo.
echo ═══════════════════════════════════════════
echo  Backend: http://localhost:8000
echo  Health:  http://localhost:8000/api/health
echo ═══════════════════════════════════════════
