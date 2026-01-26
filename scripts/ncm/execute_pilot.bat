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

set "ROOT=%~dp0..\.."
set "CMD_FILE=%~dp0ncm_commands.txt"
pushd "%ROOT%"

REM Create command file
echo /ncm pilot --count=2 > "%CMD_FILE%"
echo exit >> "%CMD_FILE%"

REM Execute NEXUS with piped commands
echo [1/2] Starting NEXUS...
python nexus7.py < "%CMD_FILE%"

REM Cleanup
del "%CMD_FILE%"
popd

echo.
echo ==================================================
echo   Pilot Execution Complete
echo ==================================================
echo.
echo Check logs at: workspace/logs/
echo Run tests: pytest tests/
echo.

pause
