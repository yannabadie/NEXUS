@echo off
REM NEXUS V5.0 - Test Launcher
REM Wrapper pour lancer les tests facilement

REM Configure UTF-8 encoding for Windows
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8

echo.
echo ================================================================================
echo NEXUS V5.0 - COMPREHENSIVE TEST SUITE
echo ================================================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

echo Python version:
python --version
echo.

REM Parse arguments
set SUITE=%1
if "%SUITE%"=="" set SUITE=critical

echo Running test suite: %SUITE%
echo.
echo Available suites:
echo   - critical: Critical tests only (recommended first run)
echo   - advanced: Advanced functionality tests
echo   - stress: Stress tests
echo   - all: All tests (long execution time)
echo.

REM Create test workspaces directory
if not exist test_workspaces mkdir test_workspaces

REM Run tests
echo.
echo Starting tests...
echo ================================================================================
echo.

python test_suite.py --suite %SUITE% --workspace test_workspaces

echo.
echo ================================================================================
echo TEST EXECUTION COMPLETE
echo ================================================================================
echo.
echo Check test_workspaces/ for detailed logs and reports
echo.

pause
