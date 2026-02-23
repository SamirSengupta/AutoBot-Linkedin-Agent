@echo off
title AutoBot Mk1 Launcher

echo ==============================================
echo        Starting AutoBot Mk1 Services...
echo ==============================================

:: Start FastAPI Backend
echo [1/2] Starting FastAPI Backend...
start cmd /k "title AutoBot Backend & cd backend & call venv\Scripts\activate.bat & python server.py"

:: Give backend a second to initialize
timeout /t 2 /nobreak > nul

:: Start Vite React Frontend
echo [2/2] Starting React Frontend...
cd frontend
start cmd /k "title AutoBot Frontend & npm run dev"

echo ==============================================
echo        All Services Started!
echo ==============================================
echo Backend running at:  http://localhost:8000
echo Frontend running at: http://localhost:5173
echo.
echo Press any key to exit this launcher text...
pause > nul
