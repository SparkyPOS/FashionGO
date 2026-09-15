@echo off
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py Setup.py
) else (
    python Setup.py
)

if errorlevel 1 (
    echo.
    echo Setup failed. Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Setup complete. Press any key to exit...
pause >nul