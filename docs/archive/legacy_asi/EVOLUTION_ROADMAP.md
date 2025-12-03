# NEXUS V7 - Roadmap d'Évolution Autonome

**Date**: 2025-11-27
**Auteur**: Claude (Opus 4.5) lors de tests E2E
**Session**: Sprint 12 - Test complet du cycle d'évolution

---

## 🔴 Bugs Critiques Identifiés

### 1. Cycle d'évolution ne produit JAMAIS d'enfant viable
**Symptôme**: Le brainstorming démarre, Gemini+Claude échangent, mais aucun enfant n'est créé dans GENERATION_ACTIVE/

**Cause probable**:
- La phase brainstorming ne termine pas avec un JSON valide
- Ou le JSON est extrait mais la création d'enfant échoue silencieusement

**Action**: Ajouter logging détaillé dans `run_evolve()` pour tracer exactement où le processus s'arrête

### 2. Erreurs tools Gemini: "Path must be..."
**Symptôme**: `Error executing tool list_directory: Path must be...`

**Cause**: Gemini CLI refuse les chemins qui ne sont pas dans `--include-directories`

**Impact**: Gemini ne peut pas explorer le code parent, donc ne peut pas proposer de mutations intelligentes

**Action**: Vérifier que `--include-directories` inclut bien tous les chemins nécessaires

### 3. Erreur IDE Client
**Symptôme**: `[ERROR] [IDEClient] Failed to connect to IDE`

**Cause**: Gemini essaie de se connecter à un IDE (VS Code?) qui n'est pas disponible

**Impact**: Bruit dans les logs, possible ralentissement

**Action**: Peut-être désactiver les fonctions IDE de Gemini CLI si non utilisées

---

## 🟡 Problèmes UX Majeurs

### 1. Fragmentation des commandes évolution
**Problème**: 4 commandes séparées pour l'évolution
- `/evolve [count]` - Créer enfants
- `/evolve-status` - Voir stats
- `/review` - Évaluer enfants
- `/specialize` - Créer spinoff

**Impact**: Utilisateur doit savoir quoi appeler et quand

**Solution proposée**:
```
/evolve           → Lance évolution ET affiche statut à la fin
/evolve --status  → Stats seulement
/evolve --review  → Mode review
/evolve --spec    → Mode spécialisation
```

### 2. Exposition FSM inutile
**Problème**: L'utilisateur voit des messages comme:
- `[FSM] IDLE -> EVOLUTION_BRAINSTORM`
- `[FSM] Mode: EVOLUTION_BRAINSTORM (max 30 tours)`

**Impact**: Confusion - c'est du jargon technique interne

**Solution**: Masquer par défaut, afficher seulement en mode verbose

### 3. Messages d'erreur tronqués
**Problème**: `Error executing tool list_directory: Path must be...` (tronqué)

**Impact**: Impossible de debugger sans voir le message complet

**Solution**: Logger les erreurs complètes dans un fichier, afficher une version courte à l'écran

### 4. Pas de mode non-interactif
**Problème**: Impossible de tester NEXUS en batch (CI/CD, scripts)

**Impact**: Tests E2E manuels uniquement

**Solution**: Ajouter `--command "..."` ou `--batch` à nexus7.py

---

## 🟢 Améliorations Suggérées

### Court terme (Sprint 13)
1. [ ] Fixer le cycle d'évolution pour qu'il produise un enfant
2. [ ] Ajouter mode batch `nexus7.py --command "/evolve 1"`
3. [ ] Logger erreurs complètes dans workspace/logs/errors.log
4. [ ] Masquer messages FSM en mode non-verbose

### Moyen terme (Sprint 14-15)
1. [ ] Unifier commandes évolution sous `/evolve`
2. [ ] Ajouter `/evolve --dry-run` pour simuler sans créer
3. [ ] Progress bar pour brainstorming (au lieu de `Processing...`)
4. [ ] Meilleure gestion des timeouts

### Long terme
1. [ ] Interface web simple (dashboard évolution)
2. [ ] Notifications (email/slack) quand évolution terminée
3. [ ] Auto-healing: si évolution échoue 3 fois, propose diagnostic

---

## 📋 Checklist Test E2E

Pour valider que NEXUS fonctionne:

```bash
# 1. Bootstrap
python nexus7.py --verify
# Attendu: ✅ Bootstrap verification successful!

# 2. Status
nexus7> /status
# Attendu: État IDLE, agents disponibles

# 3. Evolution
nexus7> /evolve 1
# Attendu:
#   - Brainstorming démarre
#   - Gemini+Claude débattent
#   - JSON mutation généré
#   - Enfant créé dans GENERATION_ACTIVE/
#   - Validation tiers (SYNTAX, SMOKE, BENCHMARK, REDTEAM)
#   - Birth certificate créé

# 4. Vérification enfant
ls GENERATION_ACTIVE/
# Attendu: NEXUS_V7.1_CHILD_001_<mission>/
#   - KERNEL.py existe
#   - workspace/_IO_BUFFER existe
#   - BIRTH_CERTIFICATE.json existe
```

---

## 🔄 État Actuel (27/11/2025 20:00)

| Étape | Status | Notes |
|-------|--------|-------|
| Bootstrap | ✅ | KERNEL.py vérifié |
| Brainstorming | ⚠️ | Démarre mais ne termine pas |
| Création enfant | ❌ | Jamais atteint |
| Validation tiers | ❌ | Jamais atteint |
| Mode batch | ❌ | N'existe pas |

**Blocker principal**: Le brainstorming Gemini+Claude ne produit pas de JSON valide qui déclenche la création d'enfant.

---

## 📝 Notes pour sessions futures

1. **Toujours vérifier GENERATION_ACTIVE/** après `/evolve` - si vide, le cycle a échoué
2. **Les logs dans workspace/logs/events_YYYYMMDD.jsonl** contiennent l'historique des invocations
3. **Le blackboard workspace/.nexus/blackboard.json** contient l'état du débat
4. **Chercher `[EVOLUTION_BRAINSTORM] Valid mutation JSON detected`** dans les logs pour voir si le JSON a été trouvé
