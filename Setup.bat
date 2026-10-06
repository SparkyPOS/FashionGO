@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    echo Running setup with Python launcher...
    py "%~dp0Setup.py"
) else (
    echo Python launcher not found. Falling back to python...
    python "%~dp0Setup.py"
)

if errorlevel 1 (
    echo.
    echo Setup failed. The Python traceback is shown above.
    echo Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Setup complete. Press any key to exit...
pause >nul