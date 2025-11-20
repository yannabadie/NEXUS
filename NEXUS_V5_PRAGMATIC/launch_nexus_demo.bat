@echo off
REM NEXUS V5.0 - Démonstration Visible
REM Lance NEXUS dans PowerShell pour voir l'exécution en temps réel

echo.
echo ================================================================================
echo NEXUS V5.0 - LANCEMENT DEMONSTRATION
echo ================================================================================
echo.
echo Ce script va lancer NEXUS avec un objectif de test simple pour démontrer:
echo   1. L'utilisation de Gemini 3 Pro Preview (VERIFIE)
echo   2. La coordination Gemini + Claude
echo   3. Le protocole CFL (Cognitive Feedback Loop)
echo.
echo Le test sera visible dans ce terminal.
echo.
pause

echo.
echo Vérification Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python non trouvé
    pause
    exit /b 1
)

echo.
echo Vérification Gemini CLI...
gemini --version
if errorlevel 1 (
    echo AVERTISSEMENT: Gemini CLI non trouvé dans PATH
    echo Assurez-vous que Gemini CLI est installé et dans le PATH
    pause
)

echo.
echo Vérification Claude Code CLI...
claude --version 2>nul
if errorlevel 1 (
    echo AVERTISSEMENT: Claude CLI non trouvé dans PATH
    echo Assurez-vous que Claude Code est installé et dans le PATH
    pause
)

echo.
echo ================================================================================
echo LANCEMENT NEXUS
echo ================================================================================
echo.
echo Configuration UTF-8...
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo.
echo Objectif du test: Créer un fichier test.txt et vérifier son contenu
echo.
echo Appuyez sur une touche pour démarrer...
pause >nul

echo.
echo ================================================================================
echo.

REM Lancer NEXUS avec logging visible
python nexus.py "Create a file named demo_test.txt with the content 'NEXUS V5.0 - Gemini 3 Pro Preview VERIFIED'. Then read the file to confirm the content."

echo.
echo ================================================================================
echo EXECUTION TERMINEE
echo ================================================================================
echo.
echo Vérification du fichier créé:
if exist workspace\demo_test.txt (
    echo.
    echo Contenu du fichier demo_test.txt:
    echo --------------------------------------------------
    type workspace\demo_test.txt
    echo.
    echo --------------------------------------------------
    echo.
    echo SUCCESS: Le fichier a été créé!
) else (
    echo.
    echo AVERTISSEMENT: Le fichier demo_test.txt n'a pas été trouvé
    echo Consultez les logs dans workspace\logs\ pour plus de détails
)

echo.
echo Pour vérifier que Gemini 3 Pro Preview a été utilisé:
echo   1. Consultez workspace\_IO_BUFFER\action_out.json
echo   2. Cherchez la section "stats" / "models"
echo   3. Vous devriez voir "gemini-3-pro-preview"
echo.

pause
