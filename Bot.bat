@echo off
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo Bot failed. Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Bot exited cleanly. Press any key to exit...
pause >nul