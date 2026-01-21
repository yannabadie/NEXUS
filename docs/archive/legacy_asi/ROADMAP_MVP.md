# ROADMAP MVP NEXUS V7 - 3 MOIS

> Généré le 2025-11-30 | Objectif: MVP Démontrable avec évolution autonome fonctionnelle

## ÉTAT ACTUEL VÉRIFIÉ

| Composant | État | Fichier clé |
|-----------|------|-------------|
| TieredValidator | ✅ OK | `core/evolution/tiered_validator.py` |
| PathGuardian | ✅ OK | `core/security/path_guardian.py` |
| Swarm RED_BLUE | ✅ OK | `core/swarm/mode_executors.py:490-575` |
| AST Validation | ✅ OK | `core/interface/repl.py:1368-1401` |
| tiktoken (memory) | ✅ OK | `core/synapse/memory_v7.py:196-201` |
| Pydantic V2 | ✅ OK | `core/synapse/protocol_v7.py` |
| **Format mutation** | 🔴 JSON | Cause IndentationError fréquents |
| Timeout Swarm | ⚠️ Tours only | Pas de timeout en secondes |
| Token counting driver | ⚠️ TODO | `core/orchestration_v7.py:1040` |

---

## PHASE 1 : STABILISATION ÉVOLUTION (Mois 1) ⭐ PRIORITÉ

### Semaine 1-2 : Format Mutation SEARCH/REPLACE

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Créer parser SEARCH/REPLACE | `core/evolution/mutation_parser.py` | M (6h) | Tests unitaires 100% |
| Remplacer JSON dans repl.py | `core/interface/repl.py:650-720` | L (3j) | 0 IndentationError sur 20 mutations |
| Adapter prompt évolution | `repl.py:600-750` | S (2h) | Prompt mis à jour |

**Format cible :**
```
<<<<<<< SEARCH
def old_function():
    return 42
=======
def old_function():
    return optimized_result
>>>>>>> REPLACE
```

**Avantages :**
- Préserve l'indentation exacte (pas d'échappement `\\n`)
- Format familier aux LLM (utilisé par Claude Code, aider, etc.)
- Diff-like, facile à review

### Semaine 3 : Timeout Swarm

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Ajouter timeout TEMPS (seconds) | `core/swarm/negotiation_protocol.py:262` | S (2h) | Config `swarm_timeout_seconds: 60` |
| Signal timeout dans logs | `core/logging/logger_v7.py` | S (1h) | Log "[TIMEOUT] Negotiation exceeded 60s" |

### Semaine 4 : Tests & Token Counting

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Token counting driver response | `core/orchestration_v7.py:1040` | S (2h) | Supprimer TODO |
| Tests evolution coverage >50% | `tests/test_evolution/` | M (8h) | pytest --cov > 50% |

---

## PHASE 2 : ARCHITECTURE SAINE (Mois 2)

### Semaine 5-6 : Refactoring Orchestrateur

| Tâche | Fichier(s) | Effort | Critère succès | Dépendances |
|-------|------------|--------|----------------|-------------|
| Extraire FSM pure | `core/fsm/state_machine.py` (<300L) | M (6h) | États + transitions uniquement | - |
| Extraire contexte | `core/fsm/context.py` (<200L) | M (4h) | Blackboard, mémoire | state_machine.py |
| Extraire exécution | `core/fsm/executor.py` (<400L) | M (6h) | Invoke drivers, tools | context.py |
| Adapter orchestration_v7.py | `core/orchestration_v7.py` (<500L) | M (4h) | Composition des 3 modules | tous |

### Semaine 7 : Rollback Atomique

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Backup parent avant mutation | `core/evolution/rollback.py` | M (4h) | Snapshot dans `.nexus/snapshots/` |
| Restore si échec validation tier 3+ | `core/evolution/tiered_validator.py:200` | S (2h) | Auto-restore testé |

### Semaine 8 : Métriques Évolution

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Tracker métriques mutation | `core/telemetry/evolution_metrics.py` | M (4h) | JSON: succès/échec/raison |
| Dashboard CLI évolution | `core/interface/evolution_dashboard.py` | M (6h) | `rich` table temps réel |

---

## PHASE 3 : CONNECTIVITÉ HYBRIDE (Mois 3)

### Semaine 9-10 : Driver API Gemini

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Nouveau driver API | `core/drivers/gemini_api_driver.py` | L (2j) | google-generativeai SDK |
| Factory driver (CLI/API) | `core/drivers/driver_factory.py` | M (4h) | Config `use_gemini_api: bool` |
| Tests comparatifs CLI vs API | `tests/test_drivers/` | M (6h) | Latence, tokens, coût |

### Semaine 11-12 : Driver API Claude + Streaming

| Tâche | Fichier | Effort | Critère succès |
|-------|---------|--------|----------------|
| Nouveau driver API | `core/drivers/claude_api_driver.py` | L (2j) | anthropic SDK |
| Streaming responses | `core/drivers/*_api_driver.py` | M (4h) | Affichage progressif |
| Documentation mode hybride | `docs/DRIVERS.md` | S (2h) | CLI vs API trade-offs |

---

## PHASE 4 : OBSERVABILITÉ (Continu)

| Tâche | Fichier | Effort | Critère succès | Phase |
|-------|---------|--------|----------------|-------|
| Dashboard CLI `rich` | `core/interface/dashboard.py` | M (6h) | FSM state, Swarm mode, tokens | 1 |
| Logs structurés JSON | `core/logging/structured_logger.py` | M (4h) | Format OpenTelemetry-compatible | 2 |
| Export metrics file | `core/telemetry/exporter.py` | S (2h) | JSON exportable pour analyse | 3 |

---

## DIAGRAMME DÉPENDANCES

```
Phase 1 (Mois 1)
├── Format SEARCH/REPLACE ──────┐
├── Timeout Swarm               │
└── Token counting              │
                                ▼
Phase 2 (Mois 2)                │
├── Refactoring FSM ◄───────────┘
├── Rollback atomique
└── Métriques évolution
                                │
Phase 3 (Mois 3)                ▼
├── Driver API Gemini
├── Driver API Claude
└── Streaming
```

---

## CRITÈRES MVP FINAL

| Critère | Mesure | Seuil |
|---------|--------|-------|
| Évolution réussie | % children valides | >80% |
| Latence moyenne | ms/turn | <5000ms |
| Coverage tests | pytest --cov | >50% |
| Orchestrateur | lignes/fichier | <500 |
| Timeout Swarm | échecs boucle infinie | 0 |

---

## RISQUES & MITIGATIONS

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Format SEARCH/REPLACE mal parsé | Bloque évolution | Tests exhaustifs + fallback JSON |
| API coûte trop cher | Budget dépassé | Garder CLI par défaut |
| Refactoring casse FSM | Régression | Tests E2E avant/après |

---

## CHANGELOG

| Date | Version | Changement |
|------|---------|------------|
| 2025-11-30 | 1.0 | Création initiale |
