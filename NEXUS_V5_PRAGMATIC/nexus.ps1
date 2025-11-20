<#
.SYNOPSIS
    NEXUS V5.0 - Orchestrateur Cognitif Symbiotique (PowerShell Wrapper)

.DESCRIPTION
    Wrapper PowerShell pour lancer NEXUS V5.0 avec une interface CLI conviviale.

.PARAMETER Objective
    Objectif à accomplir par NEXUS (obligatoire si pas --panic)

.PARAMETER Mode
    Mode opératoire: Normal, InProjectImprovement, CoreEvolution (défaut: Normal)

.PARAMETER Panic
    Déclencher un arrêt d'urgence avec ce message

.PARAMETER Help
    Afficher l'aide

.EXAMPLE
    nexus "Create a test file with hello world"

.EXAMPLE
    nexus "Analyze the codebase" --mode InProjectImprovement

.EXAMPLE
    nexus --panic "Emergency stop - infinite loop detected"

.NOTES
    Version: 5.0
    Date: 2025-11-20
    License: YANEXUS V5.0 Proprietary License
#>

param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Objective,

    [Parameter(Mandatory = $false)]
    [ValidateSet("Normal", "InProjectImprovement", "CoreEvolution")]
    [string]$Mode = "Normal",

    [Parameter(Mandatory = $false)]
    [string]$Panic,

    [Parameter(Mandatory = $false)]
    [switch]$Help
)

# Configuration UTF-8 pour Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Couleurs pour output
function Write-NexusHeader {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  NEXUS V5.0 - Orchestrateur Cognitif  " -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-NexusInfo {
    param([string]$Message)
    Write-Host "[NEXUS INFO] $Message" -ForegroundColor Green
}

function Write-NexusWarning {
    param([string]$Message)
    Write-Host "[NEXUS WARN] $Message" -ForegroundColor Yellow
}

function Write-NexusError {
    param([string]$Message)
    Write-Host "[NEXUS ERROR] $Message" -ForegroundColor Red
}

# Afficher aide
if ($Help) {
    Write-NexusHeader
    Write-Host "USAGE:"
    Write-Host "  nexus <objective> [--mode <mode>]" -ForegroundColor White
    Write-Host "  nexus --panic <message>" -ForegroundColor White
    Write-Host ""
    Write-Host "ARGUMENTS:" -ForegroundColor Yellow
    Write-Host "  <objective>          Objectif à accomplir (obligatoire)" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  --mode <mode>        Mode opératoire (défaut: Normal)" -ForegroundColor White
    Write-Host "                       Valeurs: Normal, InProjectImprovement, CoreEvolution" -ForegroundColor Gray
    Write-Host "  --panic <message>    Arrêt d'urgence avec message" -ForegroundColor White
    Write-Host "  --help               Afficher cette aide" -ForegroundColor White
    Write-Host ""
    Write-Host "MODES:" -ForegroundColor Yellow
    Write-Host "  Normal               Mode standard de résolution de tâches" -ForegroundColor White
    Write-Host "  InProjectImprovement Auto-amélioration (analyse logs, propose capabilities)" -ForegroundColor White
    Write-Host "  CoreEvolution        Evolution du code NEXUS lui-même (sandbox)" -ForegroundColor White
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  nexus `"Create a test file with hello world`"" -ForegroundColor Gray
    Write-Host "  nexus `"Analyze the codebase structure`" --mode InProjectImprovement" -ForegroundColor Gray
    Write-Host "  nexus --panic `"Emergency stop - infinite loop detected`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "FILES:" -ForegroundColor Yellow
    Write-Host "  workspace/           Dossier de travail NEXUS" -ForegroundColor White
    Write-Host "  workspace/.nexus/    État et mémoire persistante" -ForegroundColor White
    Write-Host "  workspace/_IO_BUFFER/  Communication agents" -ForegroundColor White
    Write-Host "  workspace/logs/      Logs d'exécution" -ForegroundColor White
    Write-Host ""
    Write-Host "PANIC SYSTEM:" -ForegroundColor Yellow
    Write-Host "  En cas d'urgence, créez manuellement:" -ForegroundColor White
    Write-Host "  workspace/STOP_NOW   Fichier déclencheur panic" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Validation panic
if ($Panic) {
    Write-NexusHeader
    Write-NexusWarning "PANIC MODE ACTIVATED"
    Write-Host ""
    Write-Host "Message: $Panic" -ForegroundColor Red
    Write-Host ""

    # Vérifier Python
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-NexusError "Python not found in PATH"
        exit 1
    }

    # Lancer nexus.py avec --panic
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    & python "$scriptDir\nexus.py" "PANIC_PLACEHOLDER" --panic $Panic

    exit $LASTEXITCODE
}

# Validation objective
if (-not $Objective) {
    Write-NexusError "Objective required (use --help for usage)"
    exit 1
}

# Header
Write-NexusHeader

# Vérifications pré-vol
Write-NexusInfo "Pre-flight checks..."
Write-Host ""

# 1. Vérifier Python
Write-Host "[1/5] Checking Python..." -NoNewline
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-NexusError "Python not found in PATH"
    Write-Host "       Install Python 3.10+ and add to PATH"
    exit 1
}
$pythonVersion = & python --version 2>&1
Write-Host " OK ($pythonVersion)" -ForegroundColor Green

# 2. Vérifier nexus.py
Write-Host "[2/5] Checking nexus.py..." -NoNewline
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$nexusScript = Join-Path $scriptDir "nexus.py"
if (-not (Test-Path $nexusScript)) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-NexusError "nexus.py not found at: $nexusScript"
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# 3. Vérifier Gemini CLI
Write-Host "[3/5] Checking Gemini CLI..." -NoNewline
$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
if (-not $geminiCmd) {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-NexusWarning "Gemini CLI not found in PATH"
    Write-Host "       Install: npm install -g @google/generative-ai-cli"
} else {
    $geminiVersion = & gemini --version 2>&1
    Write-Host " OK ($geminiVersion)" -ForegroundColor Green
}

# 4. Vérifier Claude Code CLI
Write-Host "[4/5] Checking Claude Code CLI..." -NoNewline
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-NexusWarning "Claude Code CLI not found in PATH"
    Write-Host "       Install from: https://claude.ai/claude-code"
} else {
    $claudeVersion = & claude --version 2>&1
    Write-Host " OK ($claudeVersion)" -ForegroundColor Green
}

# 5. Vérifier .env
Write-Host "[5/5] Checking .env configuration..." -NoNewline
$envFile = Join-Path $scriptDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-NexusWarning ".env file not found"
    Write-Host "       NEXUS will use default configuration"
} else {
    Write-Host " OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  LAUNCHING NEXUS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Objective: $Objective" -ForegroundColor White
Write-Host "Mode:      $Mode" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to interrupt..." -ForegroundColor Gray
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Lancer NEXUS
try {
    & python -u "$nexusScript" $Objective --mode $Mode
    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan

    if ($exitCode -eq 0) {
        Write-NexusInfo "NEXUS completed successfully"
    } else {
        Write-NexusError "NEXUS exited with code $exitCode"
    }

    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""

    exit $exitCode

} catch {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-NexusError "Execution failed: $_"
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    exit 1
}
