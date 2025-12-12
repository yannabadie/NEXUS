@echo off
echo ===================================================
echo 🚀 NEXUS V9.0 "Singularity" Cockpit Startup
echo ===================================================

echo.
echo [1/2] Starting Dashboard Server (Background)...
start "NEXUS Dashboard" /min cmd /k python core/ui/dashboard_server.py

echo [2/2] Starting NEXUS Core (Interactive)...
echo.
echo    - Dashboard: http://localhost:8000
echo    - Core:      Interactive REPL below
echo.

python nexus7.py

echo.
echo [SHUTDOWN] Stopping Dashboard...
taskkill /FI "WINDOWTITLE eq NEXUS Dashboard" /F >nul 2>&1
echo Done.
pause
