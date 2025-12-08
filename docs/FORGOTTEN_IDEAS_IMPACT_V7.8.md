# Étude d'Impact - Idées Oubliées NEXUS V7.8

**Date**: 2025-12-08
**Auditeur**: Claude Opus 4.5
**Contexte**: Audit ROADMAP vs Codebase

---

## Vue d'Ensemble

Deux idées documentées dans la ROADMAP n'ont pas été implémentées:

| Idée | Origine | Phase Cible | Status |
|------|---------|-------------|--------|
| **EPHEMERAL Sessions** | Gemini (2025-12-04) | Phase 7 | ❌ NOT IMPLEMENTED |
| **Hot-Swap Lead Agent** | Claude (2025-12-04) | Phase 8 | ⚠️ PARTIAL (detection only) |

---

## 1. EPHEMERAL Sessions (Gemini Proposal)

### Concept

Sessions one-shot sans persistence pour tâches triviales. Évite:
- Création de fichiers dans `~/.gemini/tmp/<hash>/`
- Surcharge du registre de sessions
- I/O inutiles pour tâches `TRIVIAL`/`SIMPLE`

### Référence ROADMAP

```markdown
# ROADMAP_HIVE_MIND.md lignes 57, 80-81, 762-775

class SessionMode(Enum):
    FRESH = "fresh"
    CONTINUE = "continue"
    BRANCH = "branch"
    EPHEMERAL = "ephemeral"  # ⬅️ MISSING in codebase

def get_session_mode(complexity: TaskComplexity, is_parallel: bool) -> SessionMode:
    if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
        return SessionMode.EPHEMERAL  # ⬅️ MISSING
```

### État Actuel du Code

```python
# core/swarm/session_manager.py:41-45
class SessionMode(str, Enum):
    FRESH = "fresh"       # New session, no prior context
    CONTINUE = "continue"  # Resume from existing session
    BRANCH = "branch"      # Fork from existing session
    # ❌ EPHEMERAL is MISSING
```

### Analyse d'Impact

| Dimension | Valeur |
|-----------|--------|
| **Fichiers à modifier** | 2: `session_manager.py`, `hybrid_swarm_engine.py` |
| **Lignes de code** | ~30-40 lignes |
| **Tests requis** | ~5-10 nouveaux tests |
| **Risque de régression** | 🟢 FAIBLE - Mode additif |
| **Dépendances** | Aucune nouvelle |
| **Effort estimé** | 2-3 heures |

### Bénéfices

1. **Performance**: ~20% moins d'I/O pour tâches triviales (pas de write session)
2. **Stockage**: Évite saturation de `~/.gemini/tmp/` sur longue durée
3. **Simplicité**: Tâches simples ne polluent pas le registre
4. **Métrique existante**: "Ephemeral Session Usage" déjà définie (objectif >50%)

### Implémentation Proposée

```python
# session_manager.py
class SessionMode(str, Enum):
    FRESH = "fresh"
    CONTINUE = "continue"
    BRANCH = "branch"
    EPHEMERAL = "ephemeral"  # NEW: No persistence

# hybrid_swarm_engine.py
def _determine_session_mode(self, complexity: TaskComplexity) -> SessionMode:
    """Determine optimal session mode based on task complexity."""
    if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
        return SessionMode.EPHEMERAL
    return SessionMode.FRESH

# Dans create_session() - skip persistence pour EPHEMERAL
if mode != SessionMode.EPHEMERAL:
    self._save_registry()
```

### Décision Recommandée

| Critère | Score |
|---------|-------|
| Effort | ████░░░░░░ 2/10 |
| Bénéfice | ██████░░░░ 6/10 |
| Risque | ██░░░░░░░░ 2/10 |
| **PRIORITÉ** | 🟡 **MOYENNE** |

**Recommandation**: Implémenter en V7.8.2 ou V7.9 comme quick-win.

---

## 2. Hot-Swap Lead Agent (Claude Proposal)

### Concept

Si le lead agent stagne pendant une collaboration LEAD_SUPPORT, le support prend automatiquement le rôle de lead avec le contexte accumulé.

### Référence ROADMAP

```markdown
# ROADMAP_HIVE_MIND.md lignes 367-403

#### Hot-Swap Lead Agent (Claude proposal 2025-12-04)

**Détection de stagnation mid-execution**:
- 3 messages similaires consécutifs du lead → trigger handover
- Support devient lead avec accumulated_context
- Ancien lead passe en support (ou idle)
```

### État Actuel du Code

```python
# ✅ IMPLÉMENTÉ: StagnationDetector (core/fsm/stagnation_detector.py)
detector = StagnationDetector(similarity_threshold=0.8)
if detector.is_stagnant():
    # ❌ Actuellement: ERROR state ou force decision
    # ❌ PAS de handover lead→support
```

**Comportement actuel quand stagnation**:
1. `fsm_handlers.py:175-176`: `_handle_stagnation()` appelé
2. Message d'avertissement injecté
3. Transition vers ERROR ou force decision
4. **PAS de swap de rôle lead/support**

### Analyse d'Impact

| Dimension | Valeur |
|-----------|--------|
| **Fichiers à modifier** | 3-4: `mode_executors.py`, `fsm_handlers.py`, `session_manager.py` |
| **Lignes de code** | ~80-120 lignes |
| **Tests requis** | ~15-20 nouveaux tests |
| **Risque de régression** | 🟠 MOYEN - Modifie flow FSM critique |
| **Dépendances** | StagnationDetector (existe), LEAD_SUPPORT mode |
| **Effort estimé** | 4-6 heures |

### Bénéfices

1. **Résilience**: Récupération automatique de stagnation sans ERROR
2. **Autonomie**: Moins d'intervention utilisateur
3. **Efficacité**: Support peut débloquer situations où lead est coincé
4. **Métrique existante**: "Hot-Swap Events" déjà définie (objectif <5%)

### Challenges Techniques

1. **Context Transfer**: Comment transférer le contexte accumulé au nouveau lead?
2. **Session Management**: Les sessions Gemini/Claude sont-elles transférables?
3. **FSM Complexity**: Transition mid-execution = complexité accrue
4. **Edge Cases**: Et si le support aussi stagne après swap?

### Implémentation Proposée (Esquisse)

```python
# mode_executors.py - dans LeadSupportExecutor

def _check_and_handle_stagnation(self, lead_agent: str, support_agent: str) -> bool:
    """Check for stagnation and perform hot-swap if needed."""
    if not self.stagnation_detector.is_stagnant():
        return False

    # Log hot-swap event
    self.logger.log_event(EventType.HOT_SWAP_TRIGGERED, {
        "old_lead": lead_agent,
        "new_lead": support_agent,
        "reason": "stagnation_detected"
    })

    # Swap roles
    self.roles[lead_agent] = "support"
    self.roles[support_agent] = "lead"

    # Transfer context
    accumulated = self.conversation_history[-3:]  # Last 3 messages

    # Reset stagnation
    self.stagnation_detector.reset()

    return True
```

### Décision Recommandée

| Critère | Score |
|---------|-------|
| Effort | ██████░░░░ 6/10 |
| Bénéfice | ████░░░░░░ 4/10 |
| Risque | █████░░░░░ 5/10 |
| **PRIORITÉ** | 🟢 **BASSE** |

**Recommandation**: Reporter à V7.9+. La détection de stagnation actuelle (→ERROR) est suffisante. Le hot-swap est une optimisation, pas une nécessité.

---

## Synthèse & Plan d'Action

### Priorités Recommandées

```
V7.8.2 (Court terme):
└── EPHEMERAL Sessions (2-3h, quick-win)

V7.9 (Moyen terme):
├── BM25S RAG (Phase 10e)
├── Backend Abstraction (Phase 10f)
└── [OPTIONNEL] Hot-Swap Lead si demandé

V7.9+ (Long terme):
├── Dense Embeddings (Phase 10g)
├── Hybrid RAG (Phase 10h)
└── Hot-Swap Lead si stagnation fréquente
```

### Mise à Jour ROADMAP Requise

1. **Phase 7**: Marquer EPHEMERAL comme `[ ] À FAIRE`
2. **Phase 8**: Clarifier que Hot-Swap est OPTIONNEL/DIFFÉRÉ
3. **Timeline**: Ajouter EPHEMERAL à V7.8.2
4. **Métriques**: Activer tracking "Ephemeral Session Usage"

---

## Conclusion

| Idée | Action | Version Cible |
|------|--------|---------------|
| **EPHEMERAL Sessions** | ✅ IMPLÉMENTER | V7.8.2 |
| **Hot-Swap Lead Agent** | ⏸️ DIFFÉRER | V7.9+ (si besoin) |

L'EPHEMERAL est un quick-win avec ROI positif. Le Hot-Swap est une optimisation de niche qui peut attendre que des métriques justifient son implémentation.

---

**Document généré par**: Claude Opus 4.5
**Audit ID**: NEXUS-AUDIT-2025-12-08-FORGOTTEN
