# 📥 NEXUS V5.1.3 - Guide d'Installation

**Installation complète pour Windows 11**

---

## Prérequis

### Système
- **OS**: Windows 11 (Windows 10 possible mais non testé)
- **Python**: 3.11 ou supérieur
- **PowerShell**: 5.1+ (inclus avec Windows)
- **Git**: Recommandé pour cloner le dépôt

### CLIs Requis

#### Claude Code CLI
```powershell
# Installation via npm (recommandé)
npm install -g @anthropic-ai/claude-code

# Vérifier installation
claude --version

# Authentification
claude auth login
```

**Documentation**: https://docs.anthropic.com/claude/docs/claude-code

#### Gemini CLI
```powershell
# Installation via pip
pip install google-generativeai

# Ou via instructions officielles Google
```

**Documentation**: https://ai.google.dev/gemini-api/docs/ai-studio-quickstart

**Note**: Vous devez avoir une clé API Gemini configurée.

---

## Installation Rapide (Recommandé)

### Étape 1: Cloner le Dépôt

```powershell
# Via HTTPS
git clone https://github.com/yannabadie/NEXUS.git
cd NEXUS/20_NEXUS/NEXUS_V5_PRAGMATIC

# Ou via SSH
git clone git@github.com:yannabadie/NEXUS.git
cd NEXUS/20_NEXUS/NEXUS_V5_PRAGMATIC
```

### Étape 2: Installer les Dépendances Python

```powershell
# Installation des dépendances
pip install -r requirements.txt
```

**Dépendances installées**:
- `rich>=13.0.0` - Interface console colorée
- `pydantic>=2.0.0` - Validation de schémas
- `python-dotenv>=1.0.0` - Gestion configuration .env
- `psutil>=5.9.0` - Monitoring ressources système
- `filelock>=3.12.0` - Robustesse I/O Windows
- `prompt_toolkit>=3.0.43` - REPL interactif (optionnel)

### Étape 3: Configuration

```powershell
# Copier le template de configuration
copy .env.template .env

# Éditer la configuration
notepad .env
```

**Configuration `.env` minimale**:
```env
# Chemins CLI (laisser vide si dans PATH)
CLAUDE_CLI_PATH=claude
GEMINI_CLI_PATH=gemini

# Session Claude (optionnel - pour reprendre une session existante)
CLAUDE_SESSION_ID=

# Modèles (Updated 2025-11-21)
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking
MODEL_EXECUTION=claude-sonnet-4-5-20250929

# Paramètres CFL
MAX_STALEMATE_COUNT=5
COMPRESSION_THRESHOLD_TOKENS=100000
```

### Étape 4: Installation Globale (Optionnel)

```powershell
# Exécuter le script d'installation
.\install.ps1

# Répondre 'y' pour confirmer l'installation
```

**Ce que fait `install.ps1`**:
1. Installe NEXUS dans `C:\Users\<vous>\AppData\Local\NEXUS`
2. Copie tous les fichiers nécessaires (core, prompts, scripts)
3. Ajoute le dossier au PATH utilisateur
4. Permet d'exécuter `nexus` depuis n'importe quel dossier

**Après installation**:
```powershell
# Redémarrer PowerShell

# Vérifier que nexus est dans le PATH
nexus --help

# Lancer NEXUS interactif
nexus
```

---

## Installation Manuelle (Avancée)

### Étape 1: Télécharger

```powershell
# Sans Git - télécharger ZIP
# Visitez: https://github.com/yannabadie/NEXUS
# Cliquez sur Code > Download ZIP
# Extraire dans C:\Code\NEXUS (ou autre dossier)

cd C:\Code\NEXUS\20_NEXUS\NEXUS_V5_PRAGMATIC
```

### Étape 2: Environnement Virtuel (Recommandé)

```powershell
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Si erreur "scripts désactivés":
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Réessayer
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 3: Configuration Avancée

```powershell
# Copier le template
copy .env.template .env

# Éditer avec paramètres avancés
notepad .env
```

**Configuration `.env` avancée**:
```env
# =====================================
# CLI PATHS
# =====================================
# Laisser vide si dans PATH, sinon chemin complet
CLAUDE_CLI_PATH=claude
GEMINI_CLI_PATH=gemini

# =====================================
# SESSIONS
# =====================================
# ID de session Claude à reprendre (optionnel)
# Format: session_20251121_143022
CLAUDE_SESSION_ID=

# =====================================
# MODELS (Updated 2025-11-21)
# =====================================
# Stratégie (Gemini 3 Pro with Thinking)
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking

# Exécution (Claude Sonnet 4.5)
MODEL_EXECUTION=claude-sonnet-4-5-20250929

# =====================================
# COGNITIVE FEEDBACK LOOP (CFL)
# =====================================
# Nombre maximum de stagnations avant escalade
# Seuil 3: Avertissement
# Seuil 5: Changement d'agent
# Seuil MAX: Arrêt d'urgence
MAX_STALEMATE_COUNT=5

# Seuil de compression mémoire (tokens)
# Au-delà, NEXUS compresse l'historique
COMPRESSION_THRESHOLD_TOKENS=100000

# =====================================
# LOGGING (Optionnel)
# =====================================
# Niveau de verbosité: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Activer logging détaillé (orchestration_logged.py)
ENABLE_DETAILED_LOGGING=false
```

### Étape 4: Vérification Installation

```powershell
# Test rapide - Mode CLI
python nexus.py --help

# Test Mode Interactif
python nexus_interactive.py

# Dans le REPL:
nexus> hello
# Devrait afficher un message de bienvenue

nexus> /status
# Devrait afficher "No active orchestration"

nexus> /exit
```

---

## Modes d'Exécution

### Mode 1: REPL Interactif (Recommandé)

```powershell
# Si installé globalement
nexus

# Ou directement
python nexus_interactive.py

# Depuis environnement virtuel
.\venv\Scripts\python.exe nexus_interactive.py
```

**Avantages**:
- Interface conversationnelle intuitive
- Historique de commandes sauvegardé
- Auto-complétion des commandes
- Sessions persistantes
- Détection conversation vs tâche technique

### Mode 2: CLI (Tâche Unique)

```powershell
# Exécution simple
python nexus.py "Analyse le code dans src/"

# Avec mode spécifique
python nexus.py "Améliore le projet" --mode InProjectImprovement

# Depuis environnement virtuel
.\venv\Scripts\python.exe nexus.py "Ma tâche"
```

**Avantages**:
- Exécution scriptée
- Intégration CI/CD facile
- Pas de REPL overhead

### Mode 3: Batch (Automation)

```powershell
# Créer un script batch
echo python nexus.py "Exécute tests et commit si succès" > run_tests.bat

# Exécuter
.\run_tests.bat
```

---

## Tests d'Installation

### Test 1: Conversation Simple

```powershell
nexus

nexus> hello
# Attendu: Message de bienvenue sans orchestration
# [NEXUS] Hello! I'm NEXUS V5.1, an AI orchestrator...

nexus> /exit
```

**✅ Succès si**: Message de bienvenue affiché instantanément

### Test 2: Tâche Technique

```powershell
nexus

nexus> créé un fichier test.txt avec "Hello NEXUS"
# Attendu: Orchestration démarre
# [NEXUS] Processing: créé un fichier test.txt...
# [NEXUS CORE] Démarrage de l'orchestration...

# Attendre la fin (peut prendre 30-60s)

nexus> /exit
```

**✅ Succès si**:
- Orchestration démarre
- Fichier `workspace/test.txt` créé
- Contenu correct: "Hello NEXUS"

### Test 3: Commandes Slash

```powershell
nexus

nexus> /help
# Attendu: Liste complète des commandes

nexus> /status
# Attendu: "No active orchestration"

nexus> /sessions
# Attendu: Liste des sessions (possiblement vide)

nexus> /exit
```

**✅ Succès si**: Toutes les commandes répondent sans erreur

### Test 4: Tests Automatisés

```powershell
# Lancer la suite de tests E2E
.\run_e2e_tests.bat

# Ou directement
python tests/test_automated_e2e.py
```

**✅ Succès attendu**:
```
Total Tests:  7
Passed:       7 (100.0%)
Failed:       0
Duration:     ~60s

✓ ALL TESTS PASSED - NEXUS V5.1.3 IS READY!
```

---

## Troubleshooting

### Problème: `claude: command not found`

**Solution**:
```powershell
# Installer Claude CLI
npm install -g @anthropic-ai/claude-code

# Vérifier installation
claude --version

# Si toujours pas trouvé, ajouter npm global bin au PATH
# Trouver le chemin:
npm bin -g
# Exemple: C:\Users\<vous>\AppData\Roaming\npm

# Ajouter au PATH utilisateur via PowerShell:
$env:Path += ";C:\Users\<vous>\AppData\Roaming\npm"
```

### Problème: `ModuleNotFoundError: No module named 'rich'`

**Solution**:
```powershell
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt

# Ou installer manuellement
pip install rich pydantic python-dotenv psutil filelock prompt_toolkit
```

### Problème: Scripts PowerShell désactivés

**Erreur**: `cannot be loaded because running scripts is disabled`

**Solution**:
```powershell
# Autoriser l'exécution de scripts (CurrentUser)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Vérifier
Get-ExecutionPolicy

# Réessayer le script
.\install.ps1
```

### Problème: "État corrompu" au premier lancement

**Solution**:
```powershell
# Créer manuellement le dossier .nexus
mkdir workspace\.nexus

# Relancer NEXUS
python nexus_interactive.py
```

**Note**: Ce bug est normalement corrigé en V5.1.3 (auto-initialisation).

### Problème: Tests timeout

**Symptômes**: Tests E2E timeout après 30s

**Solution**:
```powershell
# Augmenter le timeout dans test_automated_e2e.py
# Ligne 50: timeout: int = 180 (au lieu de 30)

# Ou désactiver timeout pour debug:
# Ligne 50: timeout: int = None
```

**Note**: Les tests vérifient que l'orchestration **démarre**, pas qu'elle se termine complètement.

### Problème: Gemini CLI non disponible

**Solution temporaire**: Utiliser mode CLI uniquement (sans REPL) ou désactiver Gemini dans le code.

**Solution permanente**: Installer et configurer Gemini CLI correctement.

---

## Désinstallation

### Désinstallation Globale

```powershell
# Supprimer le dossier d'installation
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\NEXUS"

# Retirer du PATH manuellement:
# 1. Windows + R → sysdm.cpl
# 2. Onglet "Avancé" → Variables d'environnement
# 3. Dans "Variables utilisateur", éditer "Path"
# 4. Supprimer la ligne contenant "NEXUS"
```

### Désinstallation Locale

```powershell
# Désactiver l'environnement virtuel (si activé)
deactivate

# Supprimer le dossier du projet
cd ..
Remove-Item -Recurse -Force NEXUS_V5_PRAGMATIC
```

---

## Installation pour Développement

### Setup Développeur

```powershell
# Cloner avec toutes les branches
git clone https://github.com/yannabadie/NEXUS.git
cd NEXUS/20_NEXUS/NEXUS_V5_PRAGMATIC

# Créer environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installer dépendances + dev tools
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Configurer .env pour dev
copy .env.template .env
notepad .env  # Éditer

# Lancer les tests
python tests/test_protocol_complete.py
python tests/test_automated_e2e.py

# Mode développement
python nexus_interactive.py
```

### Structure Recommandée

```
C:\Code\
├── NEXUS\                          # Clone Git
│   └── 20_NEXUS\
│       └── NEXUS_V5_PRAGMATIC\    # Développement ici
│           ├── venv\              # Environnement virtuel
│           ├── .env               # Config locale (non commitée)
│           └── ...
│
└── .nexus\                         # Données de test (optionnel)
    └── test_workspaces\
```

---

## Mise à Jour

### Mise à Jour depuis Git

```powershell
# Sauvegarder .env
copy .env .env.backup

# Pull dernières modifications
git pull origin N5P

# Restaurer .env
copy .env.backup .env

# Réinstaller dépendances (si requirements.txt modifié)
pip install --upgrade -r requirements.txt

# Réinstaller globalement (si désiré)
.\install.ps1
```

### Mise à Jour Installation Globale

```powershell
# Depuis le dossier du projet
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V5_PRAGMATIC

# Réexécuter l'installation
.\install.ps1

# Répondre 'y' pour écraser
```

---

## Support

### Ressources

- **GitHub**: https://github.com/yannabadie/NEXUS
- **Documentation**: `./docs/`
- **Tests**: `./tests/README.md`
- **Issues**: https://github.com/yannabadie/NEXUS/issues

### Obtenir de l'Aide

```powershell
# Aide REPL
nexus
nexus> /help

# Aide CLI
python nexus.py --help

# Tests de diagnostic
.\run_e2e_tests.bat
```

---

**Guide d'installation mis à jour le 21 Novembre 2025**
**Version: NEXUS V5.1.3 (Production Edition)**
