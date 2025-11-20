@echo off
echo ========================================
echo    NEXUS 2.0 - SYSTEM BOOT
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Claude Worker (Daemon)...
start "NEXUS Worker" /B python 02_CORE\nexus_daemon.py

timeout /t 2 /nobreak > nul

echo [2/2] Starting Gemini Driver (Interactive)...
python 02_CORE\gemini_driver.py

echo.
echo [SHUTDOWN] System halted.
taskkill /F /IM python.exe >nul 2>&1

