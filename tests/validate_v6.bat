@echo off
REM ========================================
REM NEXUS V6.0 VALIDATION PROTOCOL
REM Automated test suite for pre-evolution validation
REM Author: Yann Abadie
REM ========================================

setlocal enabledelayedexpansion

cd /d %~dp0..

echo.
echo ====================================
echo NEXUS V6.0 VALIDATION PROTOCOL
echo ====================================
echo Date: %date% %time%
echo.

REM Initialize counters
set PHASE1_PASS=0
set PHASE5_PASS=0
set TOTAL_ERRORS=0

REM ========================================
REM PHASE 1: INTEGRITY TESTS (CRITICAL)
REM ========================================
echo.
echo ====================================
echo PHASE 1: INTEGRITY TESTS
echo ====================================
echo.

python tests\validate_integrity.py
set PHASE1_RESULT=%ERRORLEVEL%

if %PHASE1_RESULT% EQU 0 (
    echo.
    echo [OK] Phase 1 passed
    set PHASE1_PASS=1
) else (
    echo.
    echo [ERROR] Phase 1 FAILED - CRITICAL
    echo Evolution BLOCKED until issues resolved
    set /a TOTAL_ERRORS+=1
)

REM ========================================
REM PHASE 5: EVOLUTION MODULE TESTS (CRITICAL)
REM ========================================
echo.
echo ====================================
echo PHASE 5: EVOLUTION MODULE TESTS
echo ====================================
echo.

python tests\validate_evolution.py
set PHASE5_RESULT=%ERRORLEVEL%

if %PHASE5_RESULT% EQU 0 (
    echo.
    echo [OK] Phase 5 passed
    set PHASE5_PASS=1
) else (
    echo.
    echo [ERROR] Phase 5 FAILED - CRITICAL
    echo Evolution engine not ready
    set /a TOTAL_ERRORS+=1
)

REM ========================================
REM SUMMARY
REM ========================================
echo.
echo ====================================
echo VALIDATION SUMMARY
echo ====================================
echo.

set AUTOMATED_PASSED=0
if %PHASE1_PASS% EQU 1 (
    if %PHASE5_PASS% EQU 1 (
        set AUTOMATED_PASSED=1
    )
)

echo Automated Tests:
echo   Phase 1 (Integrity):  %PHASE1_PASS%/1 passed
echo   Phase 5 (Evolution):  %PHASE5_PASS%/1 passed
echo.

if %AUTOMATED_PASSED% EQU 1 (
    echo [32m^=^=^=^= AUTOMATED TESTS: PASSED [0m
    echo.
    echo Manual tests remaining:
    echo   - Phase 2: REPL functionality
    echo   - Phase 3: Tool integration
    echo   - Phase 4: Performance tests
    echo   - Phase 6: Regression vs V5
    echo   - Phase 7: Security tests
    echo.
    echo See docs\V6.0_VALIDATION_PROTOCOL.md for manual test procedures
    echo.
    echo [33mWARNING: Complete ALL manual tests before /evolve[0m
) else (
    echo [31m^=^=^=^= AUTOMATED TESTS: FAILED [0m
    echo.
    echo [31mCRITICAL: Do NOT launch evolution[0m
    echo Fix all errors before proceeding
)

echo.
echo ====================================
echo Validation completed at %time%
echo ====================================
echo.

REM Exit with error if any tests failed
if %TOTAL_ERRORS% GTR 0 (
    exit /b 1
) else (
    exit /b 0
)
