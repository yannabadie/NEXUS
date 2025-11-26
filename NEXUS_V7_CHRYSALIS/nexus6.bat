@echo off
REM NEXUS V6.0 - Batch Launcher
REM
REM This launcher allows you to run NEXUS from anywhere using "nexus6"
REM
REM Installation: Run install_v6.ps1 to install globally
REM Manual usage: nexus6.bat (from this directory)

REM Get the directory where this batch file is located
set "NEXUS_DIR=%~dp0"

REM Change to NEXUS directory
cd /d "%NEXUS_DIR%"

REM Launch NEXUS V6 with all arguments
python "%NEXUS_DIR%nexus6.py" %*
