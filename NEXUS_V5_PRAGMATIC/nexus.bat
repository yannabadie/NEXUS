@echo off
REM NEXUS V5.0 - Global CLI Wrapper (Batch)
REM Appelle le script PowerShell dans le même répertoire

REM Déterminer le répertoire du script
set "SCRIPT_DIR=%~dp0"

REM Appeler le script PowerShell avec tous les arguments
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%nexus.ps1" %*
