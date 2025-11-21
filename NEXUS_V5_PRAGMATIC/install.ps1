# NEXUS V5.1 - Installation Script
param([string]$InstallPath)

Clear-Host
Write-Host "NEXUS V5.1 Installation" -ForegroundColor Cyan
Write-Host ""

if (-not $InstallPath) { $InstallPath = Join-Path $env:LOCALAPPDATA "NEXUS" }
Write-Host "Installing to: $InstallPath"

if (Test-Path $InstallPath) {
    $r = Read-Host "Overwrite existing installation? (y/N)"
    if ($r -ne 'y') {
        Write-Host "Installation cancelled" -ForegroundColor Yellow
        exit 0
    }
    Remove-Item -Recurse -Force $InstallPath -ErrorAction SilentlyContinue
}

Write-Host "Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null

$src = $PSScriptRoot

Write-Host "Copying core files..." -ForegroundColor Cyan
# Main executables
Copy-Item "$src\nexus.bat" $InstallPath -Force
Copy-Item "$src\nexus.ps1" $InstallPath -Force
Copy-Item "$src\nexus.py" $InstallPath -Force
Copy-Item "$src\nexus_interactive.py" $InstallPath -Force

# Core modules
Copy-Item "$src\core" $InstallPath -Recurse -Force -Exclude "__pycache__","*.pyc"
Copy-Item "$src\prompts" $InstallPath -Recurse -Force

# Configuration
if (Test-Path "$src\.env") {
    Copy-Item "$src\.env" $InstallPath -Force
}
Copy-Item "$src\.env.template" $InstallPath -Force -ErrorAction SilentlyContinue
Copy-Item "$src\requirements.txt" $InstallPath -Force

Write-Host "Updating PATH..." -ForegroundColor Cyan
$p = [Environment]::GetEnvironmentVariable("Path", "User")
if ($p -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$p;$InstallPath", "User")
    Write-Host "[OK] Added to PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] Already in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your PowerShell terminal"
Write-Host "  2. Run: nexus --help"
Write-Host "  3. Run: nexus (for interactive mode)"
Write-Host ""
