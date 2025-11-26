# NEXUS V6.0 - Automated Evolution Script
# Executes first evolution cycle automatically

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  NEXUS V6.0 - First Evolution" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "This script will execute:" -ForegroundColor Yellow
Write-Host "  1. Baseline V6.0 measurement" -ForegroundColor White
Write-Host "  2. Create 3 children (V6.1-A, B, C)" -ForegroundColor White
Write-Host "  3. Check evolution status" -ForegroundColor White
Write-Host "  4. Review and select best child`n" -ForegroundColor White

Write-Host "⚠️  WARNING: This may take 20-40 minutes`n" -ForegroundColor Yellow

$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes" -and $confirm -ne "y") {
    Write-Host "`n❌ Cancelled by user" -ForegroundColor Red
    exit 1
}

# Create commands file
$commandsFile = "workspace/evolution_commands.txt"
$commands = @"
Effectue un test complet de tes capacités actuelles. Mesure ton ASI Proximity Score baseline avant toute évolution. Documente les résultats dans workspace/baseline_v6.0.md
/evolve 3
/evolve-status
/review
exit
"@

Write-Host "`n✓ Creating commands file..." -ForegroundColor Green
Set-Content -Path $commandsFile -Value $commands

Write-Host "✓ Launching NEXUS with automated commands...`n" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Launch NEXUS with piped commands
try {
    Get-Content $commandsFile | python nexus6.py

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  Evolution Cycle Complete!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Check LINEAGE.json for updates" -ForegroundColor White
    Write-Host "  2. Review workspace/EVOLUTION_REPORT_GEN6.md" -ForegroundColor White
    Write-Host "  3. Commit and push results`n" -ForegroundColor White

} catch {
    Write-Host "`n❌ Error during evolution:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nCheck EVOLUTION_START_GUIDE.md for troubleshooting`n" -ForegroundColor Yellow
    exit 1
} finally {
    # Cleanup
    if (Test-Path $commandsFile) {
        Remove-Item $commandsFile
    }
}
