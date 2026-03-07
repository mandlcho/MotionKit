@echo off
REM MotionKit Installer Launcher
REM Tries Python GUI installer first, falls back to batch installer
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python dcckit_installer.py
    if not errorlevel 1 exit /b 0
)

REM Python not found — run the batch installer silently
echo Python not detected, using automatic installer...
echo.
call install.bat
