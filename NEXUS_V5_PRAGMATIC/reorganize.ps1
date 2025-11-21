# NEXUS V5.1 - Reorganization Script
# Organizes project structure

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "NEXUS V5.1 - Reorganizing Project Structure" -ForegroundColor Cyan
Write-Host ""

# Create directories if they don't exist
$dirsToCreate = @(
    "docs\status",
    "docs\roadmaps",
    "tests"
)

foreach ($dir in $dirsToCreate) {
    $fullPath = Join-Path $scriptDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "[CREATE] $dir" -ForegroundColor Green
    }
}

# Move STATUS files
$statusFiles = Get-ChildItem -Path $scriptDir -Filter "STATUS_*.md" -File -ErrorAction SilentlyContinue
if ($statusFiles) {
    foreach ($file in $statusFiles) {
        $dest = Join-Path (Join-Path $scriptDir "docs\status") $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host "[MOVE] $($file.Name) → docs/status/" -ForegroundColor Yellow
    }
}

# Move ROADMAP files
$roadmapFiles = Get-ChildItem -Path $scriptDir -Filter "ROADMAP_*.md" -File -ErrorAction SilentlyContinue
if ($roadmapFiles) {
    foreach ($file in $roadmapFiles) {
        $dest = Join-Path (Join-Path $scriptDir "docs\roadmaps") $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host "[MOVE] $($file.Name) → docs/roadmaps/" -ForegroundColor Yellow
    }
}

# Move test files
$testFiles = Get-ChildItem -Path $scriptDir -Filter "test_*.py" -File -ErrorAction SilentlyContinue
if ($testFiles) {
    foreach ($file in $testFiles) {
        $dest = Join-Path (Join-Path $scriptDir "tests") $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host "[MOVE] $($file.Name) → tests/" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Reorganization complete!" -ForegroundColor Cyan
