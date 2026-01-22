@echo off
REM NCM Pilot Automated Execution Script
REM Executes /ncm pilot --count=2 automatically

echo.
echo ==================================================
echo   NCM PHASE 1 PILOT - Automated Execution
echo ==================================================
echo.
echo Starting NEXUS and executing pilot...
echo.

cd /d "%~dp0"

REM Create command file
echo /ncm pilot --count=2 > ncm_commands.txt
echo exit >> ncm_commands.txt

REM Execute NEXUS with piped commands
echo [1/2] Starting NEXUS...
python nexus7.py < ncm_commands.txt

REM Cleanup
del ncm_commands.txt

echo.
echo ==================================================
echo   Pilot Execution Complete
echo ==================================================
echo.
echo Check logs at: workspace/logs/
echo Run tests: pytest tests/
echo.

pause
