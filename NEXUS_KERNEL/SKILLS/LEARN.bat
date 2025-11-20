@echo off
REM NEXUS Learning Engine - Raccourci d'execution
REM Usage: LEARN.bat [--stats]

setlocal

set SCRIPT_DIR=%~dp0
set HISTORY_FILE=%SCRIPT_DIR%..\MEMORY\ARCHIVES\CHAT_HISTORY_MASTER.md
set PLAYBOOK_FILE=%SCRIPT_DIR%..\MEMORY\PLAYBOOK.md

if "%1"=="--stats" (
    echo.
    echo ========================================
    echo   NEXUS Learning Engine - Statistiques
    echo ========================================
    echo.
    python "%SCRIPT_DIR%nexus_learning.py" --stats --playbook "%PLAYBOOK_FILE%"
    goto :end
)

if "%1"=="--help" (
    echo.
    echo NEXUS Learning Engine - Script d'execution
    echo.
    echo Usage:
    echo   LEARN.bat           - Analyser logs et mettre a jour PLAYBOOK
    echo   LEARN.bat --stats   - Afficher statistiques PLAYBOOK
    echo   LEARN.bat --help    - Afficher cette aide
    echo.
    goto :end
)

echo.
echo ========================================
echo   NEXUS Learning Engine
echo ========================================
echo.
echo Analyse en cours...
echo.

python "%SCRIPT_DIR%nexus_learning.py" --learn "%HISTORY_FILE%" --playbook "%PLAYBOOK_FILE%"

echo.
echo ========================================
echo   PLAYBOOK mis a jour!
echo ========================================
echo.
echo Consultez: %PLAYBOOK_FILE%
echo.

:end
endlocal
