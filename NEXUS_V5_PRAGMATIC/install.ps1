# NEXUS V5.0 - Installation Script
param([string]$InstallPath)
Clear-Host
Write-Host "NEXUS V5.0 Installation" -ForegroundColor Cyan
if (-not $InstallPath) { $InstallPath = Join-Path $env:LOCALAPPDATA "NEXUS" }
Write-Host "Installing to: $InstallPath"
if (Test-Path $InstallPath) {
    $r = Read-Host "Overwrite? (y/N)"
    if ($r -ne 'y') { exit 0 }
    Remove-Item -Recurse -Force $InstallPath
}
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
$src = $PSScriptRoot
Copy-Item "$src\nexus.bat" $InstallPath -Force
Copy-Item "$src\nexus.ps1" $InstallPath -Force
Copy-Item "$src\nexus.py" $InstallPath -Force
Copy-Item "$src\core" $InstallPath -Recurse -Force
Copy-Item "$src\prompts" $InstallPath -Recurse -Force
$p = [Environment]::GetEnvironmentVariable("Path", "User")
if ($p -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$p;$InstallPath", "User")
}
Write-Host "Done! Restart terminal then run: nexus --help" -ForegroundColor Green
