# PROTOCOLE DE TEST NEXUS V5.0 - ULTRA RIGOUREUX

## 🎯 OBJECTIF
Pousser NEXUS V5.0 dans ses retranchements et valider chaque feature critique.

---

## TEST 1 : CFL Cycle Complet ⭐ CRITIQUE
**Objectif** : Valider le cycle Tool → Execution → Validation

**Commande** :
```powershell
python nexus.py "Crée un fichier test.txt avec le contenu 'Hello NEXUS' et valide sa création"
```

**Attendu** :
- Tour 1 : Claude propose TOOL_USE (write)
- Nexus exécute via Tool Executor
- last_tool_result.json créé avec status SUCCESS
- Tour 2 : Claude fournit post_action_review avec validation_status SUCCESS
- Fichier workspace/test.txt créé

**Validation** :
- [ ] last_tool_result.json existe
- [ ] test.txt créé avec contenu correct
- [ ] post_action_review présent dans logs
- [ ] Aucun crash

---

## TEST 2 : Dual Schema Enforcement
**Objectif** : Vérifier que HeavyMessage est forcé après TOOL_USE

**Commande** :
```powershell
python nexus.py "Lis test.txt puis écris un nouveau fichier test2.txt"
```

**Attendu** :
- Après chaque TOOL_USE, validation CFL obligatoire
- Si l'agent oublie post_action_review → erreur détectée

**Validation** :
- [ ] Dual Schema appliqué correctement
- [ ] Détection oubli CFL si applicable

---

## TEST 3 : Stagnation Detection
**Objectif** : Déclencher escalade automatique

**Commande** :
```powershell
python nexus.py "Exécute une commande bash qui n'existe pas: 'commandeinvalide123' et corrige l'erreur"
```

**Attendu** :
- Échec du tool bash
- post_action_review avec FAILURE
- Agent reste actif pour correction
- Si répété 3x → avertissement
- Si répété 5x → basculement agent

**Validation** :
- [ ] Stalemate counter incrémenté
- [ ] Escalade si > seuil

---

## TEST 4 : Plan Health
**Objectif** : Plan stratégique maintenu et santé surveillée

**Commande** :
```powershell
python nexus.py "Crée 3 fichiers: alpha.txt, beta.txt, gamma.txt avec des contenus différents"
```

**Attendu** :
- Gemini initialise plan avec 3+ étapes
- Plan mis à jour au fur et à mesure (PENDING → IN_PROGRESS → COMPLETED)
- Plan health calculé périodiquement

**Validation** :
- [ ] strategic_plan dans blackboard.json
- [ ] plan_health avec drift_score
- [ ] Progression visible

---

## TEST 5 : Panic System
**Objectif** : Arrêt d'urgence propre

**Test A - Via CLI** :
```powershell
python nexus.py --panic "Test arrêt urgence"
```
**Attendu** : Fichier STOP_NOW créé, message confirmé

**Test B - Durante exécution** :
```powershell
# Terminal 1
python nexus.py "Tâche longue..."

# Terminal 2 (pendant exécution)
echo "STOP TEST" > workspace\_IO_BUFFER\STOP_NOW
```
**Attendu** : Arrêt < 3s avec sauvegarde état

**Validation** :
- [ ] STOP_NOW détecté
- [ ] Sauvegarde effectuée
- [ ] Arrêt propre

---

## TEST 6 : State Rollback
**Objectif** : Récupération auto corruption

**Procédure** :
1. Lancer NEXUS normalement
2. Corrompre manuellement workspace/.nexus/blackboard.json
3. Redémarrer NEXUS

**Attendu** : Restauration depuis .bak1 avec message

**Validation** :
- [ ] Message "Corruption détectée"
- [ ] Restauration depuis backup
- [ ] Pas de crash

---

## TEST 7 : Tool Executor (5 tools)
**Objectif** : Tous les tools fonctionnent

**Commandes** :
```powershell
# Test bash
python nexus.py "Exécute 'dir' et montre le résultat"

# Test read
python nexus.py "Lis test.txt"

# Test write
python nexus.py "Crée fichier data.json avec contenu {\"test\": true}"

# Test edit
python nexus.py "Remplace 'Hello' par 'Bonjour' dans test.txt"

# Test git
python nexus.py "Exécute git status"

# Test list_dir
python nexus.py "Liste tous les fichiers .txt dans workspace"
```

**Validation** :
- [ ] Tous les tools s'exécutent sans erreur
- [ ] last_tool_result.json contient stdout, stderr, returncode
- [ ] Résultats cohérents

---

## TEST 8 : Stress Test Longue Session
**Objectif** : Stabilité sur 20+ tours

**Commande** :
```powershell
python nexus.py "Analyse tous les fichiers Python dans core/, identifie les fonctions sans docstrings, et génère un rapport complet rapport_audit.md"
```

**Attendu** :
- 20+ tours de Gemini/Claude
- Plan stratégique maintenu
- Compression si > seuil
- Aucun crash
- Rapport final créé

**Validation** :
- [ ] Session complète sans crash
- [ ] Plan health reste LOW/MEDIUM
- [ ] Rapport créé
- [ ] Mémoire gérée (compression si nécessaire)

---

## TEST 9 : Resource Monitor
**Objectif** : Pause si surcharge

**Procédure** :
1. Lancer processus gourmand en arrière-plan (stress CPU)
2. Lancer NEXUS

**Attendu** : Message pause si CPU > 90%

**Validation** :
- [ ] Détection surcharge
- [ ] Pause temporaire

---

## TEST 10 : Prompts Système
**Objectif** : Agents suivent instructions CFL

**Validation manuelle logs** :
- [ ] Gemini initialise plan stratégique
- [ ] Claude utilise expected_outcome systématiquement
- [ ] post_action_review fourni après chaque tool
- [ ] Instructions claires entre agents

---

## 📊 CRITÈRES DE RÉUSSITE

### CRITIQUE (0 échec toléré)
- [ ] CFL complet fonctionne (Test 1)
- [ ] Tool Executor capture résultats (Test 7)
- [ ] Dual Schema forcé (Test 2)
- [ ] Panic System arrêt < 3s (Test 5)

### IMPORTANT (1-2 échecs tolérés)
- [ ] Stagnation détectée et gérée (Test 3)
- [ ] Plan Health calculé (Test 4)
- [ ] State Rollback fonctionne (Test 6)
- [ ] Longue session stable (Test 8)

### NICE-TO-HAVE
- [ ] Resource Monitor (Test 9)
- [ ] Prompts suivis (Test 10)

---

## 🎯 OBJECTIF FINAL
**9/10 tests réussis = NEXUS V5.0 VALIDÉ**

---

## 📝 NOTES D'EXÉCUTION
Remplir après chaque test :
- Timestamp
- Résultat (PASS/FAIL)
- Logs pertinents
- Issues identifiées
