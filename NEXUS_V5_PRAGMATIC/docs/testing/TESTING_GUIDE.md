# NEXUS V5.0 - COMPREHENSIVE TESTING GUIDE

**Date:** 20 Novembre 2025
**Version:** 5.0 Pragmatic Edition

---

## 🎯 OBJECTIF

Ce guide décrit comment exécuter les tests en environnement réel avec les CLIs Claude et Gemini, et comment analyser les résultats avec logging exhaustif.

---

## 📦 PRÉ-REQUIS

### 1. CLIs Installés

```powershell
# Vérifier Claude CLI
claude --version

# Vérifier Gemini CLI
gemini --version
```

**Les deux CLIs doivent être disponibles dans le PATH.**

### 2. Configuration

Créer ou vérifier `.env`:

```env
# Agent CLIs
CLAUDE_CLI_PATH=claude
GEMINI_CLI_PATH=gemini

# Workspace
WORKSPACE_PATH=./workspace

# Timeouts
AGENT_TIMEOUT=120

# Mode
OPERATION_MODE=Normal
```

### 3. Dépendances (optionnelles mais recommandées)

```powershell
pip install -r requirements.txt
```

---

## 🧪 EXÉCUTION DES TESTS

### Méthode 1: Script Batch (Windows)

```powershell
# Tests critiques seulement (recommandé pour premier run)
.\run_tests.bat critical

# Tests avancés
.\run_tests.bat advanced

# Stress tests
.\run_tests.bat stress

# Tous les tests
.\run_tests.bat all
```

### Méthode 2: Commande Python Directe

```powershell
# Tests critiques
python test_suite.py --suite critical --workspace test_workspaces

# Tests avancés
python test_suite.py --suite advanced --workspace test_workspaces

# Stress tests
python test_suite.py --suite stress --workspace test_workspaces

# Tous les tests
python test_suite.py --suite all --workspace test_workspaces
```

---

## 📊 SCÉNARIOS DE TEST

### Suite CRITICAL (4 tests - ~10-30 minutes)

**Tests essentiels pour valider le système:**

1. **CFL_BASIC_WRITE_READ**
   - Valide le cycle CFL complet
   - Write → Read → Validation
   - Expected: 3-10 tours

2. **DUAL_SCHEMA_ENFORCEMENT**
   - Force HeavyMessage après TOOL_USE
   - 3 commandes bash séquentielles
   - Expected: 6-15 tours

3. **TOOL_EXECUTOR_ALL_TOOLS**
   - Teste tous les 6 outils disponibles
   - bash, write, read, edit, list_dir, git
   - Expected: 12-30 tours

4. **STRATEGIC_PLAN_TRACKING**
   - Planification et suivi de progression
   - 3 fichiers + summary
   - Expected: 10-25 tours

**Critère de réussite:** 4/4 tests PASSED

---

### Suite ADVANCED (4 tests - ~30-60 minutes)

**Tests de fonctionnalités avancées:**

1. **ERROR_RECOVERY**
   - Gestion d'erreur et récupération
   - Commande invalide → analyse → recovery

2. **MULTI_STEP_ANALYSIS**
   - Analyse multi-étapes sur code réel
   - Scan directory → read files → audit

3. **AGENT_COLLABORATION**
   - Collaboration Gemini ↔ Claude
   - Stratégie → Exécution

4. **GIT_OPERATIONS**
   - Opérations Git complètes
   - status, add, status

**Critère de réussite:** 3/4 tests PASSED

---

### Suite STRESS (3 tests - ~60-120 minutes)

**Tests de robustesse:**

1. **STRESS_RAPID_TOOL_SWITCHING**
   - Changements rapides d'outils
   - CFL sur chaque switch

2. **STRESS_LARGE_FILE_OPERATIONS**
   - Fichiers volumineux (1000+ lignes)
   - Performance I/O

3. **STRESS_PLAN_COMPLEXITY**
   - Plans avec 20+ étapes
   - Plan health monitoring

**Critère de réussite:** 2/3 tests PASSED

---

## 📁 STRUCTURE DES LOGS

Chaque test génère un workspace dédié:

```
test_workspaces/
├── test_cfl_basic_write_read/
│   ├── logs/
│   │   ├── nexus_session_YYYYMMDD_HHMMSS.log    # Log principal
│   │   ├── events_YYYYMMDD_HHMMSS.jsonl         # Événements structurés
│   │   ├── cfl_YYYYMMDD_HHMMSS.jsonl            # CFL spécifique
│   │   ├── errors_YYYYMMDD_HHMMSS.log           # Erreurs seulement
│   │   ├── trace_YYYYMMDD_HHMMSS.log            # Trace ultra-verbose
│   │   └── summary_YYYYMMDD_HHMMSS.json         # Résumé session
│   ├── workspace/
│   │   └── ... fichiers créés par le test
│   └── .nexus/
│       ├── blackboard.json
│       └── ... state files
├── test_dual_schema_enforcement/
│   └── ...
└── TEST_REPORT_CRITICAL_YYYYMMDD_HHMMSS.md      # Rapport global
```

---

## 🔍 ANALYSE DES RÉSULTATS

### 1. Rapport de Test Automatique

Après exécution, consulter:

```
test_workspaces/TEST_REPORT_CRITICAL_YYYYMMDD_HHMMSS.md
test_workspaces/TEST_REPORT_CRITICAL_YYYYMMDD_HHMMSS.json
```

**Contenu:**
- Executive Summary (pass/fail counts)
- Résultats détaillés par test
- Liens vers logs
- Métriques de performance

### 2. Analyse de Logs Individuelle

Pour analyser les logs d'un test spécifique:

```powershell
python log_analyzer.py test_workspaces/test_cfl_basic_write_read/logs
```

**Output:**
- `analysis_YYYYMMDD_HHMMSS.json` - Données structurées
- `analysis_YYYYMMDD_HHMMSS.md` - Rapport lisible

**Contient:**
- Overview (durée, événements)
- Analyse des tours (turn-by-turn)
- CFL compliance rate
- Utilisation des outils
- Erreurs détaillées
- Performance (temps de réponse)
- Validations

### 3. Inspection Manuelle des Logs

**Log principal (lecture humaine):**
```powershell
notepad test_workspaces/test_*/logs/nexus_session_*.log
```

**Événements structurés (pour scripts):**
```powershell
# Chaque ligne = 1 événement JSON
Get-Content test_workspaces/test_*/logs/events_*.jsonl | ConvertFrom-Json
```

**CFL spécifique:**
```powershell
Get-Content test_workspaces/test_*/logs/cfl_*.jsonl | ConvertFrom-Json
```

**Erreurs seulement:**
```powershell
notepad test_workspaces/test_*/logs/errors_*.log
```

**Trace ultra-détaillée:**
```powershell
notepad test_workspaces/test_*/logs/trace_*.log
```

---

## 📊 MÉTRIQUES CLÉS À ANALYSER

### 1. CFL Compliance

**Indicateur:** Taux de validation post-tool

```json
{
  "total_tool_executions": 12,
  "reviewed": 12,
  "compliance_rate": 100.0
}
```

**Objectif:** 100% compliance
**Acceptable:** >95%
**Problématique:** <90%

### 2. Tool Success Rate

**Indicateur:** % de succès par outil

```json
{
  "write": {"success_rate": 100.0},
  "read": {"success_rate": 100.0},
  "bash": {"success_rate": 85.7}
}
```

**Objectif:** >95% pour tous les outils
**Problématique:** <80%

### 3. Dual Schema Enforcement

**Indicateur:** Validations réussies

```json
{
  "validation_types": {
    "DUAL_SCHEMA": 20
  },
  "results": {
    "SUCCESS": 20,
    "FAILURE": 0
  }
}
```

**Objectif:** 0 failures
**Critique:** >1 failure

### 4. Performance

**Indicateur:** Temps de réponse moyen des agents

```json
{
  "avg_response_time": 5.23,
  "by_agent": {
    "Gemini": {"avg_duration": 4.8},
    "Claude": {"avg_duration": 5.6}
  }
}
```

**Bon:** <10s
**Acceptable:** 10-30s
**Lent:** >30s

### 5. Error Rate

**Indicateur:** Nombre total d'erreurs

```json
{
  "total_errors": 0,
  "error_types": {}
}
```

**Excellent:** 0 erreurs
**Bon:** 1-2 erreurs (non-critiques)
**Problématique:** >3 erreurs

---

## 🎯 CRITÈRES DE VALIDATION

### Tests Critiques (MUST PASS)

- [x] **CFL_BASIC_WRITE_READ:** 100% CFL compliance
- [x] **DUAL_SCHEMA_ENFORCEMENT:** 0 validation failures
- [x] **TOOL_EXECUTOR_ALL_TOOLS:** Tous les outils à >90% success
- [x] **STRATEGIC_PLAN_TRACKING:** Plan créé et suivi correctement

**Verdict:** Si 1 test critique échoue → BLOCKER

### Tests Avancés (SHOULD PASS)

- [ ] **ERROR_RECOVERY:** Récupération après erreur démontrée
- [ ] **MULTI_STEP_ANALYSIS:** Analyse complexe complétée
- [ ] **AGENT_COLLABORATION:** Agents collaborent efficacement
- [ ] **GIT_OPERATIONS:** Git fonctionne correctement

**Verdict:** Si >2 tests échouent → WARNING

### Stress Tests (NICE TO PASS)

- [ ] **STRESS_RAPID_TOOL_SWITCHING:** Gère changements rapides
- [ ] **STRESS_LARGE_FILE_OPERATIONS:** Gère fichiers volumineux
- [ ] **STRESS_PLAN_COMPLEXITY:** Gère plans complexes

**Verdict:** Si 1 test passe → ACCEPTABLE

---

## 🚨 GESTION DES ÉCHECS

### Si un test critique échoue:

1. **Consulter le rapport de test:**
   ```
   test_workspaces/TEST_REPORT_CRITICAL_*.md
   ```

2. **Analyser les logs du test:**
   ```powershell
   python log_analyzer.py test_workspaces/test_NOM_DU_TEST/logs
   ```

3. **Identifier l'erreur:**
   - Consulter `errors_*.log`
   - Chercher "ERROR" dans `nexus_session_*.log`
   - Vérifier events JSONL pour la séquence

4. **Reproduire manuellement:**
   ```powershell
   python nexus.py "objectif du test"
   ```

5. **Fixer et re-tester:**
   - Corriger le code
   - Relancer le test spécifique

### Si tous les tests critiques passent:

✅ **NEXUS V5.0 EST VALIDÉ EN PRODUCTION**

Procéder aux tests avancés et stress pour évaluation complète.

---

## 📝 CHECKLIST PRÉ-PRODUCTION

Avant de déployer en production, vérifier:

- [ ] **4/4 tests critiques PASSED**
- [ ] **CFL compliance >95%**
- [ ] **Tool success rate >90% pour tous les outils**
- [ ] **0 erreurs critiques**
- [ ] **Dual Schema: 0 validation failures**
- [ ] **Performance: avg response <15s**
- [ ] **Logs générés correctement**
- [ ] **Rapports d'analyse fonctionnels**
- [ ] **Configuration .env validée**
- [ ] **CLIs Claude/Gemini fonctionnels**

---

## 🎓 INTERPRÉTATION DES RÉSULTATS

### Scénario 1: Tous les tests critiques passent

```
✅ CFL_BASIC_WRITE_READ: SUCCESS
✅ DUAL_SCHEMA_ENFORCEMENT: SUCCESS
✅ TOOL_EXECUTOR_ALL_TOOLS: SUCCESS
✅ STRATEGIC_PLAN_TRACKING: SUCCESS
```

**Verdict:** 🟢 PRODUCTION READY

**Actions:**
- Procéder aux tests avancés
- Documenter les résultats
- Déployer en production

---

### Scénario 2: 1 test critique échoue

```
✅ CFL_BASIC_WRITE_READ: SUCCESS
❌ DUAL_SCHEMA_ENFORCEMENT: FAILED
✅ TOOL_EXECUTOR_ALL_TOOLS: SUCCESS
✅ STRATEGIC_PLAN_TRACKING: SUCCESS
```

**Verdict:** 🔴 BLOCKER

**Actions:**
1. Analyser logs du test échoué
2. Identifier root cause
3. Corriger le problème
4. Re-tester
5. Ne PAS déployer avant correction

---

### Scénario 3: Plusieurs tests critiques échouent

```
❌ CFL_BASIC_WRITE_READ: FAILED
❌ DUAL_SCHEMA_ENFORCEMENT: FAILED
✅ TOOL_EXECUTOR_ALL_TOOLS: SUCCESS
❌ STRATEGIC_PLAN_TRACKING: FAILED
```

**Verdict:** 🔴 CRITICAL ISSUES

**Actions:**
1. Vérifier configuration .env
2. Vérifier CLIs fonctionnent standalone
3. Vérifier workspace permissions
4. Review code récent
5. Revenir à version stable si nécessaire

---

## 🔧 TROUBLESHOOTING

### Tests ne démarrent pas

**Symptôme:** `ModuleNotFoundError` ou import errors

**Solution:**
```powershell
# Vérifier Python path
python -c "import sys; print(sys.path)"

# Réinstaller dépendances
pip install -r requirements.txt
```

---

### Agent timeout

**Symptôme:** Tests échouent avec timeout

**Solution:**
Augmenter timeout dans `.env`:
```env
AGENT_TIMEOUT=300  # 5 minutes
```

---

### CLIs non trouvés

**Symptôme:** `FileNotFoundError: claude` ou `gemini`

**Solution:**
Spécifier chemins absolus dans `.env`:
```env
CLAUDE_CLI_PATH=C:\path\to\claude.exe
GEMINI_CLI_PATH=C:\path\to\gemini.exe
```

---

### Logs non générés

**Symptôme:** Pas de fichiers dans `logs/`

**Solution:**
Vérifier permissions:
```powershell
icacls test_workspaces /grant Users:F /T
```

---

## 📞 SUPPORT

### Fichiers à fournir en cas de problème:

1. Rapport de test: `TEST_REPORT_*.md`
2. Analyse de log: `analysis_*.json`
3. Logs d'erreur: `errors_*.log`
4. Configuration: `.env` (sans secrets!)
5. Version Python: `python --version`
6. Version CLIs: `claude --version` et `gemini --version`

---

## ✅ CONCLUSION

Ce système de test complet permet de:

✅ **Valider le système en conditions réelles**
✅ **Logger exhaustivement tous les événements**
✅ **Analyser finement les performances**
✅ **Identifier rapidement les problèmes**
✅ **Garantir la fiabilité en production**

**Commande recommandée pour premier test:**

```powershell
.\run_tests.bat critical
```

Puis analyser les résultats avant de procéder aux tests avancés.

---

**Generated:** 20 Novembre 2025
**System:** NEXUS V5.0 Pragmatic Edition
**Status:** 🧪 READY FOR TESTING
