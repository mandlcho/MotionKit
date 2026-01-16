@echo off
REM MotionKit Uninstallation Script
REM Removes MotionKit startup scripts from MotionBuilder installations

echo.
echo ========================================
echo  MotionKit Uninstallation
echo ========================================
echo.

REM Get the directory where this script is located
set "MOTIONKIT_ROOT=%~dp0"
set "MOTIONKIT_ROOT=%MOTIONKIT_ROOT:~0,-1%"

echo This will remove MotionKit integration from MotionBuilder.
echo The MotionKit files in %MOTIONKIT_ROOT% will NOT be deleted.
echo.
echo Do you want to continue?
set /p "confirm=Type YES to confirm: "

if /i not "%confirm%"=="YES" (
    echo Uninstallation cancelled.
    exit /b 0
)

echo.
echo Detecting MotionBuilder installations...
echo.

set "MOBU_FOUND=0"
set "MOBU_VERSIONS="

REM Check common installation paths for MotionBuilder 2020-2025
for %%v in (2025 2024 2023 2022 2021 2020) do (
    if exist "C:\Program Files\Autodesk\MotionBuilder %%v" (
        set "STARTUP_PATH=C:\Program Files\Autodesk\MotionBuilder %%v\bin\config\PythonStartup"
        if exist "!STARTUP_PATH!\motionkit_init.py" (
            echo [*] Found MotionKit installation in MotionBuilder %%v
            set "MOBU_FOUND=1"
            set "MOBU_VERSIONS=!MOBU_VERSIONS! %%v"
        )
    )
)

if "%MOBU_FOUND%"=="0" (
    echo.
    echo [!] No MotionKit installations found in MotionBuilder
    echo     MotionKit may not be installed, or was installed manually.
    echo.
    echo If you installed MotionKit manually:
    echo 1. Locate your MotionBuilder installation folder
    echo 2. Navigate to: bin\config\PythonStartup
    echo 3. Delete the motionkit_init.py file
    echo.
    pause
    exit /b 1
)

echo.
echo Found MotionKit in the following MotionBuilder versions:
for %%v in (%MOBU_VERSIONS%) do (
    echo   - MotionBuilder %%v
)
echo.

echo Choose an option:
echo.
echo [A] Uninstall from ALL versions
echo [S] Select specific version
echo [Q] Quit
echo.

set /p "choice=Enter your choice: "

if /i "%choice%"=="Q" (
    echo Uninstallation cancelled.
    exit /b 0
)

if /i "%choice%"=="A" (
    echo.
    echo Uninstalling from ALL MotionBuilder versions...
    for %%v in (%MOBU_VERSIONS%) do (
        call :UninstallFromVersion %%v
    )
    goto :Done
)

if /i "%choice%"=="S" (
    echo.
    set /a count=0
    for %%v in (%MOBU_VERSIONS%) do (
        set /a count+=1
        echo [!count!] MotionBuilder %%v
        set "VERSION_!count!=%%v"
    )
    echo.
    set /p "version_choice=Select version number: "

    if defined VERSION_!version_choice! (
        call set "SELECTED_VERSION=%%VERSION_!version_choice!%%"
        echo.
        echo Uninstalling from MotionBuilder !SELECTED_VERSION!...
        call :UninstallFromVersion !SELECTED_VERSION!
        goto :Done
    ) else (
        echo Invalid choice!
        pause
        exit /b 1
    )
)

echo Invalid choice!
pause
exit /b 1

:UninstallFromVersion
set "VERSION=%~1"
set "MOBU_PATH=C:\Program Files\Autodesk\MotionBuilder %VERSION%"
set "STARTUP_PATH=%MOBU_PATH%\bin\config\PythonStartup"
set "STARTUP_FILE=%STARTUP_PATH%\motionkit_init.py"

echo.
echo Processing MotionBuilder %VERSION%...

if exist "%STARTUP_FILE%" (
    echo Removing: %STARTUP_FILE%
    del "%STARTUP_FILE%"

    if not exist "%STARTUP_FILE%" (
        echo [OK] Successfully removed from MotionBuilder %VERSION%
    ) else (
        echo [ERROR] Failed to remove startup file from MotionBuilder %VERSION%
        echo        You may need to delete it manually with administrator privileges.
    )
) else (
    echo [SKIP] No MotionKit installation found in MotionBuilder %VERSION%
)

goto :eof

:Done
echo.
echo ========================================
echo  Uninstallation Complete!
echo ========================================
echo.
echo MotionKit has been removed from MotionBuilder.
echo.
echo The MotionKit files in this directory were NOT deleted.
echo If you want to completely remove MotionKit:
echo 1. Delete this folder: %MOTIONKIT_ROOT%
echo.
echo To reinstall MotionKit later, simply run install.bat again.
echo.
pause
