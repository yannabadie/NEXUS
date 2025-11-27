# NEXUS V7.0 "Chrysalis" - Changelog

## Version 6.0.2 (2025-11-24)

### Améliorations du Contexte (par Gemini)

**Problème identifié :**
- Les agents perdaient le contexte du mode actuel et du plan stratégique
- L'historique limité à 5 messages causait des oublis de contexte

**Solutions implémentées :**

1. **Injection du MODE dans le contexte** (`core/orchestration_v7.py`)
   - Les agents voient maintenant explicitement le mode courant (Normal, Brainstorming, etc.)
   - Améliore la conscience situationnelle

2. **Injection du PLAN STRATÉGIQUE** (`core/orchestration_v7.py`)
   - Le plan complet (JSON) est inclus dans chaque contexte agent
   - Permet aux agents de voir les étapes en cours et leur assignation

3. **Injection des CAPABILITIES (TOOLS)** (`core/orchestration_v7.py`)
   - Liste complète des outils disponibles injectée dans le contexte
   - Les agents voient explicitement leurs capacités

4. **Historique étendu** (`core/orchestration_v7.py`)
   - Historique passé de 5 à 30 messages
   - Réduit drastiquement les pertes de contexte sur tâches longues

**Fichiers modifiés :**
- `core/orchestration_v7.py` - Fonction `_build_agent_context()` améliorée

### Test de Stabilité (par Gemini)

**Nouveau fichier :** `tests/verify_stability.py`

Test automatisé qui vérifie :
- ✓ Transitions FSM correctes (IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE)
- ✓ Injection des sections MODE, PLAN STRATÉGIQUE, CAPABILITIES dans le contexte
- ✓ Collaboration Gemini ↔ Claude avec délégation
- ✓ Exécution d'outil et validation (Closed Feedback Loop)

**Utilisation :**
```bash
cd NEXUS_V7_CHRYSALIS
python tests/verify_stability.py
```

**Output attendu :**
```
SUCCESS: Turn 1 completed.
```

### Corrections de Bugs (par Claude)

1. **Fix encodage Unicode** (`core/orchestration_v7.py`)
   - **Problème :** Caractère '→' (U+2192) causait UnicodeEncodeError sur Windows (cp1252)
   - **Solution :** Remplacé par '->' (ASCII compatible)
   - **Impact :** Le verbose mode fonctionne maintenant sur tous les terminaux Windows

2. **Fix test verify_stability.py**
   - **Problème :** Tentative de créer une session interactive (PromptSession) dans test automatisé
   - **Solution :** Test modifié pour instancier directement `OrchestratorV7` sans REPL
   - **Problème :** Signature incorrecte du constructeur (manquait `config`)
   - **Solution :** Ajout du paramètre `config` manquant
   - **Impact :** Test fonctionne maintenant en mode non-interactif

### Métriques

**Lignes modifiées :**
- orchestration_v7.py: +17 lignes (injection contexte)
- verify_stability.py: 125 lignes (nouveau fichier)

**Tests :**
- ✓ verify_stability.py : PASS
- ✓ NEXUS bootstrap : OK (--verify fonctionne)

### Documentation Ajoutée

**Nouveau fichier :** `CHANGELOG_V6.0.md` (ce fichier)
- Documente toutes les améliorations récentes
- Explique les problèmes résolus et les solutions

### Prochaines Étapes Recommandées

1. **Tester en conditions réelles** :
   - Lancer NEXUS avec un objectif complexe (15+ tours)
   - Vérifier que les agents ne perdent plus le contexte

2. **Métriques de contexte** :
   - Ajouter logging de la taille du contexte injecté
   - Surveiller si l'historique de 30 messages est suffisant

3. **Tests d'intégration** :
   - Créer des tests avec les VRAIS drivers (pas mocks)
   - Tester avec Gemini/Claude CLI réels

4. **Evolution V6.1** :
   - Utiliser `/evolve 3` pour créer des enfants
   - Mesurer l'impact des améliorations de contexte sur ASI Proximity Score

### Notes Techniques

**Pourquoi MockDriver dans le test ?**
- Les tests unitaires doivent être isolés et rapides
- Pas de dépendance aux CLIs externes (gemini, claude)
- Permet de tester la logique FSM pure sans side effects
- Les tests d'intégration avec vrais drivers viendront ensuite

**Compatibilité :**
- Python 3.13+
- Windows (encodage cp1252 géré)
- Linux/macOS (compatible)

### Références

- **Commit précédent :** 8eaa4f0 - "Workspace permissions, encoding fixes"
- **Branch :** N6P-bis
- **Auteurs :** Gemini (améliorations contexte), Claude (fixes bugs + doc)
