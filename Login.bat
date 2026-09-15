@echo off
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py loginscript.py
) else (
    python loginscript.py
)

if errorlevel 1 (
    echo.
    echo Login script failed. Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Login script exited. Press any key to exit...
pause >nul