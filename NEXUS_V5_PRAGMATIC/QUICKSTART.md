# 🚀 NEXUS V5.1.3 - Quick Start Guide

**Commencez avec NEXUS en 5 minutes**

---

## ⚡ Installation Express (3 minutes)

```powershell
# 1. Cloner le dépôt
git clone https://github.com/yannabadie/NEXUS.git
cd NEXUS/20_NEXUS/NEXUS_V5_PRAGMATIC

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer
copy .env.template .env
# Éditer .env si nécessaire (optionnel pour commencer)

# 4. Installer globalement (optionnel)
.\install.ps1
```

**C'est tout! NEXUS est prêt à l'emploi.**

---

## 🎯 Premier Lancement (2 minutes)

### Option A: Mode Interactif (Recommandé)

```powershell
# Lancer NEXUS
python nexus_interactive.py

# Ou si installé globalement:
nexus
```

**Dans le REPL**:
```
nexus> hello
[NEXUS] Hello! I'm NEXUS V5.1, an AI orchestrator...

nexus> créé un fichier hello.txt avec "Hello World"
[NEXUS] Processing: créé un fichier hello.txt...
[NEXUS CORE] Démarrage de l'orchestration...
# ... Gemini planifie → Claude exécute ...
[NEXUS] Task completed

nexus> /status
  NEXUS Status
Mode:            Normal
Active Agent:    Claude
Objective:       créé un fichier hello.txt...

nexus> /exit
[NEXUS] Session saved. Goodbye!
```

### Option B: Mode CLI (Tâche Unique)

```powershell
# Exécuter une tâche directement
python nexus.py "créé un fichier test.txt avec 'NEXUS V5.1.3'"

# Attendre la fin de l'exécution
# Le fichier workspace/test.txt est créé
```

---

## 📚 Commandes Essentielles

### Commandes REPL

| Commande | Description |
|----------|-------------|
| `/help` | Afficher l'aide complète |
| `/status` | État de l'orchestration |
| `/history` | Historique de la session |
| `/plan` | Plan stratégique actuel |
| `/sessions` | Sessions sauvegardées |
| `/exit` | Quitter NEXUS |

### Exemples de Tâches

**Création de fichiers**:
```
nexus> créé un fichier config.json avec {"version": "5.1.3"}
nexus> écris un script Python hello.py qui affiche "Hello NEXUS"
```

**Analyse de code**:
```
nexus> analyse le code dans src/ et liste les bugs potentiels
nexus> lis le fichier README.md et résume-le
```

**Tests et builds**:
```
nexus> exécute pytest dans tests/
nexus> lance les tests, corrige les erreurs, puis commit
```

**Git operations**:
```
nexus> affiche le git status
nexus> commit tous les changements avec le message "Update docs"
```

---

## 🔧 Configuration de Base

### Fichier .env Minimal

```env
# CLIs (laisser vide si dans PATH)
CLAUDE_CLI_PATH=claude
GEMINI_CLI_PATH=gemini

# Modèles
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking
MODEL_EXECUTION=claude-sonnet-4-5-20250929

# Paramètres
MAX_STALEMATE_COUNT=5
COMPRESSION_THRESHOLD_TOKENS=100000
```

**Note**: La configuration par défaut fonctionne immédiatement si les CLIs sont dans le PATH.

---

## 🧪 Vérifier l'Installation

### Test Automatisé

```powershell
# Lancer la suite de tests
.\run_e2e_tests.bat

# Résultat attendu:
# Total Tests:  7
# Passed:       7 (100.0%)
# ✓ ALL TESTS PASSED
```

### Test Manuel

```powershell
nexus

# Test 1: Conversation (devrait répondre instantanément)
nexus> hello

# Test 2: Tâche simple (devrait déclencher l'orchestration)
nexus> créé un fichier test.txt

# Test 3: Commandes slash
nexus> /status
nexus> /help

nexus> /exit
```

---

## 💡 Cas d'Usage Courants

### Développement

```powershell
# Créer un module de tests
python nexus.py "Crée un module de tests unitaires pour src/auth.py"

# Corriger un bug
python nexus.py "Corrige le bug dans validate_token qui accepte les tokens expirés"

# Refactoring
python nexus.py "Refactorise src/utils.py pour améliorer la lisibilité"
```

### Analyse et Documentation

```powershell
# Analyse de code
python nexus.py "Analyse le code et génère un rapport de qualité"

# Documentation
python nexus.py "Génère la documentation API pour tous les fichiers dans src/"
```

### CI/CD et Automation

```powershell
# Pipeline complet
python nexus.py "Exécute tous les tests, corrige les échecs, puis commit les changements"

# Build et déploiement
python nexus.py "Lance le build, vérifie les erreurs, corrige-les"
```

---

## 🚨 Problèmes Courants

### "claude: command not found"

```powershell
# Installer Claude CLI
npm install -g @anthropic-ai/claude-code
claude auth login
```

### "ModuleNotFoundError"

```powershell
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Orchestration ne démarre pas

**Vérifications**:
1. CLIs installés: `claude --version` et `gemini --version`
2. Authentification OK: `claude auth status`
3. Configuration .env correcte
4. Dossier workspace/ existe

---

## 📖 Aller Plus Loin

### Documentation Complète

- **Installation**: [`INSTALLATION.md`](./INSTALLATION.md)
- **README**: [`README.md`](./README.md)
- **Architecture**: [`docs/ARCHITECTURE_COMPLETE.md`](./docs/ARCHITECTURE_COMPLETE.md)
- **Changelog**: [`CHANGELOG.md`](./CHANGELOG.md)
- **Tests**: [`tests/README.md`](./tests/README.md)

### Modes Avancés

**InProjectImprovement**:
```powershell
python nexus.py "Améliore le projet" --mode InProjectImprovement
```

**CoreEvolution** (⚠️ Avancé):
```powershell
python nexus.py "Analyse et améliore NEXUS lui-même" --mode CoreEvolution
```

### Personnalisation

**Modifier les prompts système**:
- `prompts/system_gemini_base.md` - Stratégie (Gemini)
- `prompts/system_claude_base.md` - Exécution (Claude)

**Ajouter des outils**:
- Créer un nouveau fichier dans `core/tools/`
- S'inspirer de `bash_tool.py`, `read_tool.py`, etc.

---

## 🎓 Apprendre NEXUS

### Tutoriel Interactif (5 minutes)

```powershell
nexus

# Étape 1: Saluer NEXUS
nexus> hello

# Étape 2: Vérifier le statut
nexus> /status

# Étape 3: Créer un fichier simple
nexus> créé un fichier tutorial.txt avec "Je découvre NEXUS!"

# Étape 4: Vérifier l'historique
nexus> /history

# Étape 5: Voir le plan stratégique
nexus> /plan

# Étape 6: Tâche plus complexe
nexus> créé un script Python qui affiche la date actuelle

# Étape 7: Quitter
nexus> /exit
```

### Concepts Clés

1. **CFL (Cognitive Feedback Loop)**
   - Tout outil suit: Demande → Exécution → Validation
   - Élimine les hallucinations sur les résultats

2. **Dual Agents**
   - **Gemini**: Planification stratégique
   - **Claude**: Exécution précise
   - Basculement automatique sur stagnation

3. **Tool Executor**
   - Exécution centralisée (source de vérité)
   - Résultats sauvegardés dans `last_tool_result.json`
   - 6 outils: bash, read, write, edit, git, list_dir

4. **Conversation Detection**
   - Filtre automatique greetings vs tâches
   - Réponses instantanées pour "hello", "aide", etc.
   - Orchestration uniquement pour tâches techniques

---

## 🏆 Exemples Complets

### Exemple 1: Créer un Module Python

```powershell
nexus

nexus> créé un module calculator.py avec les fonctions add, subtract, multiply, divide

# NEXUS va:
# 1. Gemini planifie la structure
# 2. Claude écrit le code
# 3. Fichier créé dans workspace/calculator.py

nexus> lis le fichier calculator.py

# NEXUS affiche le contenu

nexus> créé des tests unitaires pour calculator.py

# NEXUS génère test_calculator.py

nexus> exécute les tests avec pytest

# NEXUS lance pytest et affiche les résultats

nexus> /exit
```

### Exemple 2: Analyser et Corriger du Code

```powershell
python nexus.py "Lis le fichier src/auth.py, identifie les bugs de sécurité, et corrige-les"

# NEXUS va:
# 1. Lire auth.py
# 2. Analyser le code (Gemini)
# 3. Identifier les vulnérabilités
# 4. Corriger le code (Claude)
# 5. Sauvegarder les modifications
```

### Exemple 3: Workflow Git Complet

```powershell
nexus

nexus> affiche le git status

nexus> créé un commit avec tous les changements et le message "feat: Add new features"

nexus> affiche le git log

nexus> pousse les changements vers origin main

nexus> /exit
```

---

## ✅ Checklist Post-Installation

- [ ] CLIs installés (claude, gemini)
- [ ] Dépendances Python installées
- [ ] Fichier .env configuré
- [ ] Test "hello" fonctionne
- [ ] Test création fichier fonctionne
- [ ] Tests automatisés passent (optionnel)
- [ ] Installation globale (optionnel)

---

## 🆘 Besoin d'Aide?

### Support

- **Issues GitHub**: https://github.com/yannabadie/NEXUS/issues
- **Documentation**: `./docs/`
- **Tests**: `.\run_e2e_tests.bat`

### Commandes de Diagnostic

```powershell
# Vérifier CLIs
claude --version
gemini --version

# Vérifier Python packages
pip list | findstr "rich pydantic dotenv"

# Tester NEXUS
python nexus_interactive.py
nexus> /help
nexus> /status
nexus> /exit
```

---

**Quick Start Guide mis à jour le 21 Novembre 2025**
**Version: NEXUS V5.1.3 (Production Edition)**

**🎉 Bienvenue dans NEXUS! Bon coding!**
