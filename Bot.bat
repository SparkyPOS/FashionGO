@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    echo Running bot with Python launcher...
    py "%~dp0main.py"
) else (
    echo Python launcher not found. Falling back to python...
    python "%~dp0main.py"
)

if errorlevel 1 (
    echo.
    echo Bot failed. The Python traceback is shown above.
    echo Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Bot exited cleanly. Press any key to exit...
pause >nul