@echo off
echo ========================================
echo  MCP SSE Server Launcher
echo  Windows-Stable HTTP Implementation
echo ========================================
echo.

REM Navigate to 20_NEXUS directory
cd /d "%~dp0\..\..\..\"

echo Starting MCP SSE Server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Run the SSE server with the venv Python
.venv\Scripts\python.exe 03_AGENTS\mcp_skeleton\server_sse.py

pause