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

echo This will remove MotionKit integration from MotionBuilder and 3ds Max.
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

echo.
echo Detecting 3ds Max installations...
echo.

set "MAX_FOUND=0"
set "MAX_VERSIONS="

REM Check common installation paths for 3ds Max 2020-2026
for %%v in (2026 2025 2024 2023 2022 2021 2020) do (
    if exist "C:\Program Files\Autodesk\3ds Max %%v" (
        set "STARTUP_PATH=C:\Program Files\Autodesk\3ds Max %%v\scripts\Startup"
        if exist "!STARTUP_PATH!\motionkit_init.ms" (
            echo [*] Found MotionKit installation in 3ds Max %%v
            set "MAX_FOUND=1"
            set "MAX_VERSIONS=!MAX_VERSIONS! %%v"
        )
    )
)

echo.
if "%MOBU_FOUND%"=="0" (
    if "%MAX_FOUND%"=="0" (
        echo [!] No MotionKit installations found
        echo     MotionKit may not be installed, or was installed manually.
        echo.
        pause
        exit /b 1
    )
)

echo.
if "%MOBU_FOUND%"=="1" (
    echo Found MotionKit in the following MotionBuilder versions:
    for %%v in (%MOBU_VERSIONS%) do (
        echo   - MotionBuilder %%v
    )
    echo.
)

if "%MAX_FOUND%"=="1" (
    echo Found MotionKit in the following 3ds Max versions:
    for %%v in (%MAX_VERSIONS%) do (
        echo   - 3ds Max %%v
    )
    echo.
)

echo Choose an option:
echo.
echo [A] Uninstall from ALL versions
echo [Q] Quit
echo.

set /p "choice=Enter your choice: "

if /i "%choice%"=="Q" (
    echo Uninstallation cancelled.
    exit /b 0
)

if /i "%choice%"=="A" (
    echo.

    if "%MOBU_FOUND%"=="1" (
        echo Uninstalling from ALL MotionBuilder versions...
        for %%v in (%MOBU_VERSIONS%) do (
            call :UninstallFromMobu %%v
        )
    )

    if "%MAX_FOUND%"=="1" (
        echo.
        echo Uninstalling from ALL 3ds Max versions...
        for %%v in (%MAX_VERSIONS%) do (
            call :UninstallFromMax %%v
        )
    )

    goto :Done
)

echo Invalid choice!
pause
exit /b 1

:UninstallFromMobu
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

:UninstallFromMax
set "VERSION=%~1"
set "MAX_PATH=C:\Program Files\Autodesk\3ds Max %VERSION%"
set "STARTUP_PATH=%MAX_PATH%\scripts\Startup"
set "STARTUP_FILE=%STARTUP_PATH%\motionkit_init.ms"

echo.
echo Processing 3ds Max %VERSION%...

if exist "%STARTUP_FILE%" (
    echo Removing: %STARTUP_FILE%
    del "%STARTUP_FILE%"

    if not exist "%STARTUP_FILE%" (
        echo [OK] Successfully removed from 3ds Max %VERSION%
    ) else (
        echo [ERROR] Failed to remove startup file from 3ds Max %VERSION%
        echo        You may need to delete it manually with administrator privileges.
    )
) else (
    echo [SKIP] No MotionKit installation found in 3ds Max %VERSION%
)

goto :eof

:Done
echo.
echo ========================================
echo  Uninstallation Complete!
echo ========================================
echo.
echo MotionKit has been removed from installed applications.
echo.
echo The MotionKit files in this directory were NOT deleted.
echo If you want to completely remove MotionKit:
echo 1. Delete this folder: %MOTIONKIT_ROOT%
echo.
echo To reinstall MotionKit later, simply run install.bat again.
echo.
pause
