$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path "."
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path $repoRoot "workspace\\demo_research_$timestamp"

python .\nexus_research.py "How does ProjectMemory index files?" `
  --mode mock `
  --output $outputDir `
  --path core\memory_pkg\memory\project_memory.py

Write-Host "Evidence pack written to: $outputDir"
