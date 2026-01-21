@echo off
REM DCCKit Installer Launcher
cd /d "%~dp0"
python dcckit_installer.py
if errorlevel 1 (
    echo.
    echo Error: Failed to launch installer.
    echo Make sure Python is installed.
    pause
)
