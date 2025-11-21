<#
.SYNOPSIS
    NEXUS V5.1 - Orchestrateur Cognitif Symbiotique Interactive

.DESCRIPTION
    Claude Code-like interactive experience for NEXUS orchestration.
    Launch without arguments for interactive mode (REPL).
    Provide objective for one-shot execution.

.PARAMETER Objective
    Task to accomplish (optional - omit for interactive mode)

.PARAMETER Mode
    Operation mode: Normal, InProjectImprovement, CoreEvolution (default: Normal)

.PARAMETER Panic
    Trigger emergency stop with message

.PARAMETER Help
    Show help

.PARAMETER Verbose
    Show pre-flight checks and detailed output

.EXAMPLE
    nexus
    Launch interactive mode (REPL)

.EXAMPLE
    nexus "Create a test file"
    Execute one-shot task

.EXAMPLE
    nexus "Analyze code" --mode InProjectImprovement
    One-shot with specific mode

.EXAMPLE
    nexus --panic "Emergency stop"
    Trigger emergency stop

.NOTES
    Version: 5.1
    License: YANEXUS V5.1 Proprietary License
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
    [switch]$Help,

    [Parameter(Mandatory = $false)]
    [switch]$Verbose
)

# UTF-8 configuration for Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Determine script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$nexusScript = Join-Path $scriptDir "nexus.py"
$nexusInteractive = Join-Path $scriptDir "nexus_interactive.py"

# Show help
if ($Help) {
    Write-Host "NEXUS V5.1 - Interactive Orchestrator (Claude Code-like)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  nexus                         Launch interactive mode (REPL)"
    Write-Host "  nexus <objective>             Execute one-shot task"
    Write-Host "  nexus <objective> [options]   One-shot with options"
    Write-Host "  nexus --panic <message>       Emergency stop"
    Write-Host "  nexus --help                  Show this help"
    Write-Host ""
    Write-Host "MODES:" -ForegroundColor Yellow
    Write-Host "  Interactive Mode (REPL):"
    Write-Host "    - Multi-turn conversations"
    Write-Host "    - Slash commands (/help, /status, /history, etc.)"
    Write-Host "    - Session persistence"
    Write-Host "    - Command history (up/down arrows)"
    Write-Host "    - Tab completion"
    Write-Host ""
    Write-Host "  One-Shot Mode:"
    Write-Host "    - Execute single task and exit"
    Write-Host "    - Same as Claude Code CLI mode"
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  --mode <mode>        Normal | InProjectImprovement | CoreEvolution (default: Normal)"
    Write-Host "  --panic <message>    Emergency stop"
    Write-Host "  --verbose            Show pre-flight checks"
    Write-Host "  --help               Show this help"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  nexus"
    Write-Host "    → Enter interactive mode"
    Write-Host ""
    Write-Host "  nexus `"Create a test file with hello world`""
    Write-Host "    → One-shot execution"
    Write-Host ""
    Write-Host "  nexus `"Analyze codebase`" --mode InProjectImprovement"
    Write-Host "    → One-shot with InProjectImprovement mode"
    Write-Host ""
    Write-Host "  nexus --panic `"Emergency stop`""
    Write-Host "    → Trigger emergency stop"
    Write-Host ""
    exit 0
}

# Panic mode
if ($Panic) {
    & python -u "$nexusScript" "dummy" --panic "$Panic"
    exit $LASTEXITCODE
}

# Determine mode: Interactive vs One-Shot
if (-not $Objective) {
    # No objective = Interactive Mode (REPL)
    if ($Verbose) {
        Write-Host "[NEXUS] Launching interactive mode (REPL)" -ForegroundColor Cyan
    }

    # Check nexus_interactive.py exists
    if (-not (Test-Path $nexusInteractive)) {
        Write-Host "ERROR: nexus_interactive.py not found at $nexusInteractive" -ForegroundColor Red
        exit 1
    }

    # Launch interactive mode
    try {
        & python -u "$nexusInteractive"
        exit $LASTEXITCODE
    } catch {
        Write-Host "ERROR: Failed to launch interactive mode: $_" -ForegroundColor Red
        exit 1
    }
}

# Pre-flight checks (silent unless --verbose)
if ($Verbose) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  NEXUS V5.0 - Pre-flight Checks" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

if ($Verbose) {
    $pythonVersion = & python --version 2>&1
    Write-Host "[1/5] Python: OK ($pythonVersion)" -ForegroundColor Green
}

# Check nexus.py
if (-not (Test-Path $nexusScript)) {
    Write-Host "ERROR: nexus.py not found at $nexusScript" -ForegroundColor Red
    exit 1
}

if ($Verbose) {
    Write-Host "[2/5] nexus.py: OK" -ForegroundColor Green
}

# Check Gemini CLI
$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
if (-not $geminiCmd) {
    Write-Host "ERROR: Gemini CLI not found. Install from: https://github.com/google-gemini/generative-ai-python" -ForegroundColor Red
    exit 1
}

if ($Verbose) {
    $geminiVersion = & gemini --version 2>&1 | Select-Object -First 1
    Write-Host "[3/5] Gemini CLI: OK ($geminiVersion)" -ForegroundColor Green
}

# Check Claude Code CLI
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host "ERROR: Claude Code CLI not found. Install from: https://docs.claude.ai/claude-code" -ForegroundColor Red
    exit 1
}

if ($Verbose) {
    $claudeVersion = & claude --version 2>&1 | Select-Object -First 1
    Write-Host "[4/5] Claude Code CLI: OK ($claudeVersion)" -ForegroundColor Green
}

# Check .env (warning only)
$envFile = Join-Path $scriptDir ".env"
if ($Verbose) {
    if (-not (Test-Path $envFile)) {
        Write-Host "[5/5] .env: WARNING (using defaults)" -ForegroundColor Yellow
    } else {
        Write-Host "[5/5] .env: OK" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Launch NEXUS (clean output like Claude Code)
try {
    & python -u "$nexusScript" $Objective --mode $Mode
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0 -and $Verbose) {
        Write-Host ""
        Write-Host "NEXUS exited with code $exitCode" -ForegroundColor Yellow
    }

    exit $exitCode

} catch {
    Write-Host "ERROR: Execution failed: $_" -ForegroundColor Red
    exit 1
}
