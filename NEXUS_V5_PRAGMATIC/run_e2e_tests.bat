@echo off
REM NEXUS V5.1.3 - Automated E2E Tests Runner
REM Tests with real Gemini CLI + Claude Code CLI

echo ============================================================
echo NEXUS V5.1.3 - AUTOMATED END-TO-END TESTS
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    exit /b 1
)

REM Run tests
python tests\test_automated_e2e.py

REM Capture exit code
set TEST_RESULT=%ERRORLEVEL%

echo.
if %TEST_RESULT%==0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [FAILURE] Some tests failed - see output above
)

exit /b %TEST_RESULT%
