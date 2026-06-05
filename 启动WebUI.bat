@echo off
REM ============================================================
REM  Windows double-click launcher for the Fund Finance Stress Model WebUI.
REM
REM  Double-click this file in Explorer to:
REM    1. Auto-setup the Python environment if it's missing
REM    2. Start the Streamlit web server
REM    3. Auto-open your default browser to http://localhost:8501
REM
REM  Keep the command window open while you use the WebUI.
REM  Close it (or press Ctrl+C) to stop the server.
REM ============================================================

cd /d "%~dp0"
chcp 65001 >nul

cls
echo.
echo  ============================================================
echo.
echo    Fund Finance Stress Model
echo    A Power-Electronics Sub-Sector Risk Lens
echo.
echo  ============================================================
echo.

REM ---- Verify Python is available ----
where python >nul 2>nul
if errorlevel 1 (
    echo [X] python not found in PATH.
    echo.
    echo     Please install Python 3.10+ from python.org
    echo     and make sure "Add to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [ok] Python %PY_VER% detected

REM ---- Bootstrap venv if missing ----
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  -^> First-time setup ^(this takes ~90 seconds on Windows^)...
    echo     Installing numpy, pandas, matplotlib, streamlit, plotly...
    echo.
    python dev.py setup
    if errorlevel 1 (
        echo.
        echo [X] Setup failed. See messages above.
        pause
        exit /b 1
    )
)

REM ---- Launch ----
echo.
echo  -^> Starting WebUI...
echo  -^> Your browser will open in a few seconds.
echo.
echo     When you're done: come back to this window and press
echo     Ctrl+C, or simply close it. The server will stop.
echo.

REM Open browser after a 4-second delay
start "" /b cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8501/"

REM Run streamlit in foreground
.venv\Scripts\python.exe -m streamlit run app.py ^
    --server.headless true ^
    --server.port 8501 ^
    --browser.gatherUsageStats false

echo.
echo Server stopped.
pause
