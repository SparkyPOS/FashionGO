@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    echo Running login script with Python launcher...
    py "%~dp0loginscript.py"
) else (
    echo Python launcher not found. Falling back to python...
    python "%~dp0loginscript.py"
)

if errorlevel 1 (
    echo.
    echo Login script failed. The Python traceback is shown above.
    echo Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo.
echo Login script exited cleanly. Press any key to exit...
pause >nul