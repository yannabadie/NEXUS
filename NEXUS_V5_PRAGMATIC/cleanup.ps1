# NEXUS V5.1 - Cleanup Script
# Removes temporary files and test outputs

param([switch]$Force)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "NEXUS V5.1 - Cleanup Script" -ForegroundColor Cyan
Write-Host ""

# Confirmation
if (-not $Force) {
    $confirm = Read-Host "This will delete temporary files, test workspaces, and logs. Continue? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "Cleanup cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Items to clean
$itemsToClean = @(
    # Test workspaces
    "test_workspaces",

    # Temporary files
    "temp_*.json",
    "temp_*.md",

    # Log files
    "test_execution.log",
    "test_final.log",
    "*.test.log",

    # Python cache
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",

    # Workspace (will be recreated)
    "workspace"
)

$cleaned = 0
$errors = 0

foreach ($item in $itemsToClean) {
    $fullPath = Join-Path $scriptDir $item

    if (Test-Path $fullPath) {
        try {
            Remove-Item -Path $fullPath -Recurse -Force -ErrorAction Stop
            Write-Host "[OK] Removed: $item" -ForegroundColor Green
            $cleaned++
        } catch {
            Write-Host "[ERROR] Failed to remove $item : $_" -ForegroundColor Red
            $errors++
        }
    }
}

Write-Host ""
Write-Host "Cleanup Summary:" -ForegroundColor Cyan
Write-Host "  Cleaned: $cleaned items" -ForegroundColor Green
Write-Host "  Errors:  $errors items" -ForegroundColor $(if ($errors -eq 0) { "Green" } else { "Red" })
Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
