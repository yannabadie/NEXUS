@echo off
REM ============================================
REM NEXUS KERNEL - BOOTSTRAP
REM ============================================
REM Script d'initialisation du Kernel NEXUS
REM Vérifie l'environnement et prépare le système
REM ============================================

echo.
echo ========================================
echo  NEXUS KERNEL - BOOTSTRAP v1.0.0
echo ========================================
echo.

REM --- 1. Vérification Python ---
echo [1/5] Verification Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Installez Python 3.8+ depuis https://www.python.org/
    pause
    exit /b 1
)
python --version
echo [OK] Python detecte
echo.

REM --- 2. Vérification Git (optionnel) ---
echo [2/5] Verification Git...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Git non detecte - Versionning desactive
) else (
    git --version
    echo [OK] Git detecte
)
echo.

REM --- 3. Vérification structure dossiers ---
echo [3/5] Verification structure NEXUS_KERNEL...
if not exist "MEMORY\" (
    echo [CREATE] Dossier MEMORY manquant - Creation...
    mkdir MEMORY
)
if not exist "SKILLS\" (
    echo [CREATE] Dossier SKILLS manquant - Creation...
    mkdir SKILLS
)
if not exist "TEMP\" (
    echo [CREATE] Dossier TEMP pour cache - Creation...
    mkdir TEMP
)
echo [OK] Structure dossiers validee
echo.

REM --- 4. Initialisation mémoire court terme ---
echo [4/5] Initialisation memoire court terme...
if not exist "MEMORY\short_term.json" (
    echo [CREATE] Fichier short_term.json manquant - Creation...
    echo { > MEMORY\short_term.json
    echo   "session_id": null, >> MEMORY\short_term.json
    echo   "start_time": null, >> MEMORY\short_term.json
    echo   "current_objective": null >> MEMORY\short_term.json
    echo } >> MEMORY\short_term.json
)
echo [OK] Memoire court terme prete
echo.

REM --- 5. Test skill_loader ---
echo [5/5] Test du Skill Loader...
python SKILLS\skill_loader.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Skill Loader teste avec erreurs (normal si aucune skill)
) else (
    echo [OK] Skill Loader fonctionnel
)
echo.

REM --- Résumé final ---
echo ========================================
echo  BOOTSTRAP COMPLETE
echo ========================================
echo.
echo Status: NEXUS KERNEL READY
echo.
echo Prochaines etapes:
echo   1. Consulter CORE_PROTOCOL.md pour les regles
echo   2. Developper des skills dans SKILLS/
echo   3. Utiliser skill_loader.py pour charger dynamiquement
echo.
echo Appuyez sur une touche pour quitter...
pause >nul
