@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
REM Manual installation helper for MotionKit - VERBOSE MODE
REM Run this as Administrator

echo.
echo ========================================
echo  MotionKit Manual Installation [VERBOSE]
echo ========================================
echo.
echo [INFO] This script copies motionkit_init.py to MotionBuilder's startup folder
echo [INFO] Time: %TIME%
echo [INFO] Date: %DATE%
echo.

REM Check if running as admin
echo [CHECK] Verifying administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges!
    echo [ERROR] Current user does not have admin rights
    echo.
    echo [ACTION] Please right-click this file and select "Run as administrator"
    echo.
    echo Terminal will remain open for review...
    pause
    exit /b 1
) else (
    echo [OK] Running with Administrator privileges
    echo.
)

set "SOURCE=%~dp0motionkit_init.py"
set "DEST=C:\Program Files\Autodesk\MotionBuilder 2024\bin\config\PythonStartup\motionkit_init.py"

echo [INFO] Source file: %SOURCE%
echo [INFO] Destination: %DEST%
echo.

echo [CHECK] Verifying source file exists...
if not exist "%SOURCE%" (
    echo [ERROR] Source file not found!
    echo [ERROR] Expected location: %SOURCE%
    echo [ERROR] Cannot proceed without source file
    echo.
    echo [ACTION] Ensure motionkit_init.py exists in the MotionKit directory
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Source file found
    for %%A in ("%SOURCE%") do (
        echo [INFO] File size: %%~zA bytes
        echo [INFO] Last modified: %%~tA
    )
    echo.
)

echo [CHECK] Verifying MotionBuilder installation...
if not exist "C:\Program Files\Autodesk\MotionBuilder 2024" (
    echo [ERROR] MotionBuilder 2024 not found!
    echo [ERROR] Expected location: C:\Program Files\Autodesk\MotionBuilder 2024
    echo.
    echo [INFO] If you're using a different version, you need to edit this script:
    echo [INFO] 1. Right-click install_manual.bat and select "Edit"
    echo [INFO] 2. Find the line with "MotionBuilder 2024"
    echo [INFO] 3. Change "2024" to your version (e.g., 2023, 2025)
    echo [INFO] 4. Save and run again as Administrator
    echo.
    pause
    exit /b 1
) else (
    echo [OK] MotionBuilder 2024 installation found
    echo.
)

echo [CHECK] Verifying destination directory...
set "DEST_DIR=C:\Program Files\Autodesk\MotionBuilder 2024\bin\config\PythonStartup"
if not exist "%DEST_DIR%" (
    echo [WARN] PythonStartup directory does not exist
    echo [ACTION] Creating directory: %DEST_DIR%
    mkdir "%DEST_DIR%"

    if exist "%DEST_DIR%" (
        echo [OK] Directory created successfully
    ) else (
        echo [ERROR] Failed to create directory
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] Destination directory exists
)
echo.

echo [ACTION] Copying file...
echo [INFO] From: %SOURCE%
echo [INFO] To:   %DEST%
echo.

copy /Y "%SOURCE%" "%DEST%" >nul 2>&1

echo [VERIFY] Checking if file was copied...
if exist "%DEST%" (
    echo [OK] File copied successfully!
    echo.

    for %%A in ("%DEST%") do (
        echo [INFO] Destination file size: %%~zA bytes
        echo [INFO] Destination file location: %%~fA
    )

    echo.
    echo [VERIFY] Reading first 5 lines of installed file:
    echo ----------------------------------------
    type "%DEST%" | more +0 | findstr /N "^" | findstr "^[1-5]:"
    echo ----------------------------------------
    echo.

    echo ========================================
    echo  Installation Successful!
    echo ========================================
    echo.
    echo [STATUS] MotionKit has been installed to MotionBuilder 2024
    echo.
    echo [NEXT STEPS]
    echo 1. Start/Restart MotionBuilder 2024
    echo 2. Open Python Console: View ^> Python Console
    echo 3. Look for messages starting with [MotionKit]
    echo 4. Check menu bar for "MotionKit" menu
    echo.
    echo [EXPECTED CONSOLE OUTPUT]
    echo [MotionKit] Added C:\Users\elementa\projects\MotionKit to Python path
    echo [MotionKit] Initializing MotionKit menu system...
    echo [MotionKit] Initialization completed successfully!
    echo [MotionKit] Menu should appear in: MotionKit ^> [categories]
    echo.
    echo [TROUBLESHOOTING]
    echo - If no console messages appear, check the file was installed correctly
    echo - If error messages appear, report them for debugging
    echo - All MotionKit messages are prefixed with [MotionKit]
    echo.
) else (
    echo [ERROR] File copy failed!
    echo [ERROR] Destination: %DEST%
    echo.
    echo [POSSIBLE CAUSES]
    echo - Insufficient permissions (even with Administrator rights)
    echo - Antivirus blocking the operation
    echo - File system issue
    echo.
    echo [MANUAL WORKAROUND]
    echo 1. Open File Explorer as Administrator
    echo 2. Navigate to: %DEST_DIR%
    echo 3. Copy motionkit_init.py from MotionKit directory
    echo 4. Paste it into the PythonStartup folder
    echo.
)

echo Terminal will remain open for review...
echo Press any key to close...
pause >nul
