# NEXUS V5.0 - Script d'installation
# Vérifie les prérequis, crée l'environnement et configure le système

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEXUS V5.0 - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier Python 3.11+
Write-Host "[1/7] Vérification de Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.1[1-9]" -or $pythonVersion -match "Python 3\.[2-9]") {
    Write-Host "  ✓ Python détecté: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python 3.11+ requis. Installé: $pythonVersion" -ForegroundColor Red
    exit 1
}

# 2. Vérifier Claude CLI
Write-Host "[2/7] Vérification de Claude CLI..." -ForegroundColor Yellow
$claudeCheck = claude --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Claude CLI détecté" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Claude CLI non trouvé. Installez-le depuis https://claude.ai" -ForegroundColor Yellow
}

# 3. Vérifier Gemini CLI (optionnel)
Write-Host "[3/7] Vérification de Gemini CLI..." -ForegroundColor Yellow
$geminiCheck = gemini --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Gemini CLI détecté" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Gemini CLI non trouvé (optionnel)" -ForegroundColor Yellow
}

# 4. Créer venv
Write-Host "[4/7] Création de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  ⚠ venv existe déjà" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "  ✓ venv créé" -ForegroundColor Green
}

# 5. Activer venv et installer dépendances
Write-Host "[5/7] Installation des dépendances..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt
Write-Host "  ✓ Dépendances installées" -ForegroundColor Green

# 6. Créer structure de dossiers
Write-Host "[6/7] Création de la structure workspace..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "workspace\.nexus" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace\_IO_BUFFER" | Out-Null
Write-Host "  ✓ Structure créée" -ForegroundColor Green

# 7. Configuration .env
Write-Host "[7/7] Configuration de .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ⚠ .env existe déjà - non écrasé" -ForegroundColor Yellow
} else {
    Copy-Item ".env.template" ".env"
    Write-Host "  ✓ .env créé depuis template" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ⚠ IMPORTANT: Éditez .env et configurez:" -ForegroundColor Yellow
    Write-Host "     - CLAUDE_SESSION_ID (si nécessaire)" -ForegroundColor Yellow
    Write-Host "     - API Keys (fallback si CLI échoue)" -ForegroundColor Yellow
}

# Finalisation
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation terminée!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "  1. Éditez .env avec votre configuration"
Write-Host "  2. Activez l'environnement: .\venv\Scripts\Activate.ps1"
Write-Host "  3. Lancez NEXUS: python nexus.py `"Votre objectif`""
Write-Host ""
Write-Host "Exemples:" -ForegroundColor Yellow
Write-Host "  python nexus.py `"Analyse le code dans src/ et identifie les bugs`""
Write-Host "  python nexus.py `"Crée un module de tests complet`" --mode Normal"
Write-Host ""
Write-Host "Panic mode (arrêt d'urgence):" -ForegroundColor Yellow
Write-Host "  python nexus.py --panic `"Raison de l'arrêt`""
Write-Host ""
