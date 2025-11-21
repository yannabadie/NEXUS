@echo off
REM Setup Windows Task Scheduler for NEXUS Review Checker
REM Run this script as Administrator

echo ========================================
echo NEXUS - Setup Task Scheduler
echo ========================================
echo.

REM Get Python path
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to PATH
    pause
    exit /b 1
)

REM Get script path
set SCRIPT_PATH=%~dp0check_pending_review.py
set PYTHON_PATH=python

echo Creating scheduled task...
echo Task Name: NEXUS_Review_Checker
echo Script: %SCRIPT_PATH%
echo Schedule: Every hour
echo.

REM Create task (runs every hour)
schtasks /create /tn "NEXUS_Review_Checker" /tr "%PYTHON_PATH% %SCRIPT_PATH%" /sc hourly /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Task created successfully
    echo ========================================
    echo.
    echo The task will check for pending reviews every hour.
    echo.
    echo To disable:
    echo   schtasks /end /tn "NEXUS_Review_Checker"
    echo.
    echo To delete:
    echo   schtasks /delete /tn "NEXUS_Review_Checker" /f
    echo.
) else (
    echo.
    echo ERROR: Failed to create task
    echo Make sure you run this script as Administrator
    echo.
)

pause
