@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM MotionKit Distribution Packaging Script
REM Creates a clean zip ready to send to other animators

echo.
echo ========================================
echo  MotionKit - Build Distribution Package
echo ========================================
echo.

REM Get script directory
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

REM Create dist output folder
set "DIST_DIR=%ROOT%\dist"
set "STAGING=%DIST_DIR%\MotionKit"
REM Use PowerShell for locale-safe date formatting
for /f %%i in ('powershell -Command "Get-Date -Format yyyyMMdd"') do set "TIMESTAMP=%%i"
set "ZIP_NAME=MotionKit_%TIMESTAMP%.zip"

echo [INFO] Source:  %ROOT%
echo [INFO] Output:  %DIST_DIR%\%ZIP_NAME%
echo.

REM Clean previous build
if exist "%STAGING%" (
    echo [CLEAN] Removing previous staging folder...
    rmdir /S /Q "%STAGING%"
)
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
mkdir "%STAGING%"

echo [COPY] Copying project files...
echo.

REM === Core directories (always included) ===
for %%D in (core config localization max maya mobu presets resources standalone unreal_scripts) do (
    if exist "%ROOT%\%%D" (
        echo   + %%D\
        xcopy "%ROOT%\%%D" "%STAGING%\%%D\" /E /I /Q /Y >nul 2>&1
    )
)

echo.

REM === Root files (installers + startup) ===
echo [COPY] Copying installer and config files...
for %%F in (install.bat uninstall.bat run_installer.bat dcckit_installer.py motionkit_init.ms) do (
    if exist "%ROOT%\%%F" (
        echo   + %%F
        copy "%ROOT%\%%F" "%STAGING%\%%F" >nul 2>&1
    )
)

REM === Docs (only user-facing ones) ===
echo.
echo [COPY] Copying documentation...
for %%F in (README.md QUICKSTART.md INSTALLER.md) do (
    if exist "%ROOT%\%%F" (
        echo   + %%F
        copy "%ROOT%\%%F" "%STAGING%\%%F" >nul 2>&1
    )
)

echo.

REM === Clean up unwanted files from staging ===
echo [CLEAN] Removing dev/build artifacts...

REM Remove __pycache__ directories
for /D /R "%STAGING%" %%D in (__pycache__) do (
    if exist "%%D" (
        echo   - %%D
        rmdir /S /Q "%%D" 2>nul
    )
)

REM Remove .pyc files
for /R "%STAGING%" %%F in (*.pyc) do (
    if exist "%%F" (
        del "%%F" 2>nul
    )
)

REM Remove .gitkeep files
for /R "%STAGING%" %%F in (.gitkeep) do (
    if exist "%%F" (
        del "%%F" 2>nul
    )
)

echo.

REM === Summary of what was EXCLUDED ===
echo [INFO] Excluded from distribution:
echo   - .git\              (version control history)
echo   - tests\             (unit tests)
echo   - examples\          (dev examples)
echo   - docs\              (dev documentation)
echo   - dist\              (previous builds)
echo   - AGENTS.md          (dev notes)
echo   - DEVELOPMENT.md     (dev notes)
echo   - INSTALLER_FEATURES.md
echo   - AniMax_Tools_Analysis.md
echo   - make_release.bat   (this script)
echo   - __pycache__\       (Python cache)
echo   - *.pyc              (compiled Python)
echo.

REM === Create zip using PowerShell ===
echo [PACK] Creating %ZIP_NAME%...
set "ZIP_PATH=%DIST_DIR%\%ZIP_NAME%"

REM Remove old zip if exists
if exist "%ZIP_PATH%" del "%ZIP_PATH%"

powershell -Command "Compress-Archive -Path '%STAGING%' -DestinationPath '%ZIP_PATH%' -Force"

if not exist "%ZIP_PATH%" (
    echo.
    echo [ERROR] Failed to create zip file!
    echo [ERROR] Check that PowerShell is available.
    echo.
    goto :EndScript
)

REM Get file size
for %%A in ("%ZIP_PATH%") do (
    set /a "SIZE_KB=%%~zA / 1024"
)
echo.
echo ========================================
echo  Package Created Successfully!
echo ========================================
echo.
echo   File: %ZIP_PATH%
echo   Size: !SIZE_KB! KB
echo.
echo [NEXT] Send this zip to your animator.
echo        They extract it and run:
echo        - run_installer.bat  (GUI installer)
echo        - install.bat        (command-line installer)
echo.

REM Clean up staging folder
echo [CLEAN] Removing staging folder...
rmdir /S /Q "%STAGING%" 2>nul

:EndScript
echo Done!
echo.
pause
