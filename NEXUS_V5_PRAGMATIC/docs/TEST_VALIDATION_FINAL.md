# NEXUS V5.1 - Test de Validation Finale

**Date**: 21 Novembre 2025
**Version**: V5.1.1
**Status**: Installation complétée - Prêt pour tests utilisateur

---

## Installation Confirmée

Installation réussie dans: `C:\Users\yann.abadie\AppData\Local\NEXUS`

Fichiers critiques vérifiés:
- ✅ `nexus.bat` - Lanceur Windows
- ✅ `nexus.ps1` - Lanceur PowerShell
- ✅ `nexus_interactive.py` - REPL interactif
- ✅ `core/orchestration.py` - Avec fix `forced_agent_switch`
- ✅ `nexus_interactive.py` - Avec détecteur de conversation

---

## Protocole de Test Utilisateur

### Étape 1: Ouvrir un nouveau terminal PowerShell

**IMPORTANT**: Ouvrir un NOUVEAU terminal pour recharger le PATH.

```powershell
# Dans un nouveau PowerShell:
nexus
```

**Résultat attendu**: Message de bienvenue NEXUS V5.1

---

### Étape 2: Test de Conversation (FIX #2)

**Objectif**: Vérifier que "hello" ne déclenche PAS l'orchestration

**Commande**:
```
nexus> hello
```

**Résultat attendu**:
```
[NEXUS] Hello! I'm NEXUS V5.1, an AI orchestrator.
I coordinate Gemini (strategy) and Claude (execution) to help you with tasks.
Type /help to see available commands, or describe a task to begin.
```

**Critères de succès**:
- ✅ Réponse immédiate (< 1 seconde)
- ✅ Pas de message "[Gemini - Stratège]"
- ✅ Pas de message "[Claude - Exécutant]"
- ✅ Pas de boucle d'orchestration
- ✅ Retour immédiat au prompt `nexus>`

**En cas d'échec**:
- Si orchestration se déclenche → Conversation detector non fonctionnel
- Vérifier ligne 364 de nexus_interactive.py

---

### Étape 3: Test des Questions (FIX #2)

**Objectif**: Vérifier que les questions conversationnelles sont gérées

**Commandes à tester**:
```
nexus> what are you
nexus> qui es-tu
nexus> what can you do
```

**Résultat attendu**:
- Réponse directe expliquant NEXUS
- PAS d'orchestration

**Critères de succès**:
- ✅ Chaque réponse instantanée
- ✅ Pas d'invocation Gemini/Claude

---

### Étape 4: Test de Tâche Technique (FIX #1)

**Objectif**: Vérifier que Claude APPARAÎT dans l'orchestration

**Commande**:
```
nexus> create a file test.txt with content "NEXUS V5.1 works"
```

**Résultat attendu**:
```
[NEXUS CORE] Démarrage de l'orchestration V5.0
[Gemini - Stratège] Analyse de la tâche...
[Gemini - Stratège] Délégation à Claude pour exécution...
[NEXUS CORE] Switch forcé actif → Claude
[Claude - Exécutant] Création du fichier test.txt...
[NEXUS - EXECUTOR] Exécution: file_write
[NEXUS - CFL] ✓ Action validée avec succès
[NEXUS CORE] Objectif atteint. Fin de session.
```

**Critères de succès**:
- ✅ `[Gemini - Stratège]` apparaît en premier
- ✅ `[Claude - Exécutant]` apparaît ensuite (CRITIQUE!)
- ✅ Fichier `test.txt` créé dans workspace
- ✅ Contenu du fichier = "NEXUS V5.1 works"
- ✅ Pas de boucle infinie
- ✅ Session se termine correctement

**En cas d'échec**:
- Si Claude n'apparaît jamais → Bug #1 non résolu
- Vérifier `forced_agent_switch` dans orchestration.py (ligne 43, 220, 331)

---

### Étape 5: Test de Stagnation (FIX #4)

**Objectif**: Vérifier que le système s'arrête au seuil configuré

**Commande** (entrée ambiguë):
```
nexus> fais quelque chose
```

**Résultat attendu**:
```
[Gemini - Stratège] Analyse...
[NEXUS CORE] ⚠ Stagnation détectée (3/5 échecs)
[NEXUS CORE] Stagnation détectée (3/5 échecs). Transfert au partenaire.
[NEXUS CORE] Switch forcé actif → Claude
[Claude - Exécutant] ...
[NEXUS CORE] STAGNATION CRITIQUE (5/5 échecs). Arrêt.
[NEXUS] Task stopped: Stagnation critique: 5 échecs consécutifs
This often happens when the task isn't clear or is too conversational.
Try describing a specific technical task (e.g., 'create a file test.txt').
```

**Critères de succès**:
- ✅ Arrêt à 5 stagnations (MAX_STALEMATE_COUNT)
- ✅ Switch vers Claude après 3 stagnations
- ✅ Message utilisateur friendly
- ✅ Retour au prompt `nexus>` (pas de crash)

---

### Étape 6: Test de Workspace (FIX #3)

**Objectif**: Vérifier que le workspace correct est utilisé

**Résultat attendu au démarrage**:
```
[NEXUS] Mode: Installed (workspace: C:\Users\yann.abadie\AppData\Local\NEXUS\workspace)
```

**Critères de succès**:
- ✅ Workspace détecté automatiquement
- ✅ Fichiers `.nexus/blackboard.json` créés dans ce workspace
- ✅ Pas d'erreur "No such file or directory"

---

## Tests de Commandes Slash

### Test `/help`
```
nexus> /help
```
**Attendu**: Liste des commandes disponibles

### Test `/status`
```
nexus> /status
```
**Attendu**: État du système (agent actif, compteur stagnation)

### Test `/history`
```
nexus> /history
```
**Attendu**: Historique des interactions de la session

### Test `/clear`
```
nexus> /clear
```
**Attendu**: Écran vidé

### Test `/exit`
```
nexus> /exit
```
**Attendu**: Session sauvegardée et sortie propre

---

## Checklist de Validation Complète

### Bugs Critiques Résolus
- [ ] **BUG #1**: Claude apparaît dans l'orchestration (Étape 4)
- [ ] **BUG #2**: "hello" ne déclenche pas d'orchestration (Étape 2)
- [ ] **BUG #3**: Workspace correct utilisé (Étape 6)
- [ ] **BUG #4**: Arrêt à MAX_STALEMATE_COUNT=5 (Étape 5)
- [ ] **BUG #5**: Messages d'erreur friendly (Étape 5)

### Fonctionnalités V5.1
- [ ] REPL interactif fonctionne
- [ ] Slash commands fonctionnent
- [ ] Session persistence (fichiers .nexus créés)
- [ ] UTF-8 support (caractères français affichés)
- [ ] Ctrl+C gestion propre (pas de crash)

### Orchestration V5.0
- [ ] CFL (Cognitive Feedback Loop) fonctionne
- [ ] Dual Schema validation (Light/Heavy)
- [ ] Tool execution centralisée
- [ ] Plan stratégique tracking
- [ ] Stalemate detection

---

## En Cas de Problème

### Problème: "nexus" commande introuvable
**Solution**:
1. Fermer et rouvrir le terminal PowerShell
2. Vérifier PATH: `$env:Path -split ';' | Select-String "NEXUS"`
3. Si absent, réexécuter install.ps1

### Problème: Orchestration ne démarre pas
**Solution**:
1. Vérifier .env: `cat "C:\Users\yann.abadie\AppData\Local\NEXUS\.env"`
2. Vérifier API keys (ANTHROPIC_API_KEY, GEMINI_API_KEY)
3. Voir logs dans workspace/logs/

### Problème: Claude n'apparaît jamais
**Solution**:
1. Vérifier version installée: `grep forced_agent_switch "C:\Users\yann.abadie\AppData\Local\NEXUS\core\orchestration.py"`
2. Si absent → Réinstaller avec install.ps1
3. Si présent → Vérifier logs pour comprendre pourquoi switch ne se déclenche pas

### Problème: Boucle infinie sur "hello"
**Solution**:
1. Vérifier: `grep is_simple_conversation "C:\Users\yann.abadie\AppData\Local\NEXUS\nexus_interactive.py"`
2. Si absent → Réinstaller
3. Si présent → Vérifier liste des greetings (ligne 259-266)

---

## Logs et Diagnostics

Tous les logs sont dans:
```
C:\Users\yann.abadie\AppData\Local\NEXUS\workspace\logs\
```

Fichiers importants:
- `nexus_session_YYYYMMDD_HHMMSS.log` - Log principal
- `events_YYYYMMDD_HHMMSS.jsonl` - Événements structurés
- `errors_YYYYMMDD_HHMMSS.log` - Erreurs uniquement
- `cfl_YYYYMMDD_HHMMSS.jsonl` - Feedback loop

---

## Résultat Attendu Final

Après tous les tests:

```
✅ Conversations gérées instantanément (sans orchestration)
✅ Tâches techniques déclenchent Gemini + Claude
✅ Claude invoqué après 3 stagnations
✅ Arrêt propre après 5 stagnations
✅ Workspace correct utilisé
✅ Messages d'erreur friendly
✅ Toutes les slash commands fonctionnent
```

**Si tous les critères sont remplis**: NEXUS V5.1 est 100% fonctionnel.

**Si échecs**: Documenter dans un nouveau rapport et investiguer.

---

**Prochaine Étape**: Utilisateur exécute ce protocole et rapporte les résultats.
