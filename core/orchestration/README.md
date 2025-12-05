# Module: Orchestration Package

**Version**: 7.8 (ADAPTIVE EVOLUTION)
**Last Updated**: 2025-12-05
**Phase**: 14c - Orchestrator Refactoring

---

## Role Architectural

Package modulaire contenant les composants extraits de `orchestration_v7.py`.

**Principe**: Découpage du "God Object" OrchestratorV7 (2223 lignes) en modules spécialisés suivant le Single Responsibility Principle.

---

## Alignement ROADMAP V7.8

| Phase | Impact |
|-------|--------|
| **Phase 14c** | Refactoring incrémental de l'orchestrateur |
| **V8.0** | Base pour StateHandler pattern complet |

---

## Structure du Package

```
core/orchestration/
├── __init__.py          # Exports publics
├── README.md            # Cette documentation
├── context_builder.py   # Construction des contextes agents
├── detectors.py         # Détection de formats (mutations, etc.)
├── agent_invoker.py     # Invocation des agents (Claude, Gemini, Spawned)
├── swarm_bridge.py      # Intégration HybridSwarmEngine
└── fsm_handlers.py      # Handlers par état FSM
```

---

## Composants

### `context_builder.py`

**Classe**: `ContextBuilder`

| Méthode | Description |
|---------|-------------|
| `build_context()` | Contexte complet pour brainstorming |
| `build_context_with_tool_result()` | Contexte léger pour CFL validation |
| `build_swarm_context()` | Contexte enrichi pour swarm execution |
| `build_simple_context()` | Contexte minimal pour tâches simples |

**Usage**:
```python
builder = ContextBuilder(orchestrator)
context = builder.build_context()
```

---

### `detectors.py`

**Classes**: `MutationDetector`, `ResponseDetector`

| Méthode | Description |
|---------|-------------|
| `detect_mutation_complete()` | Détecte mutation JSON ou SEARCH/REPLACE |
| `detect_search_replace_format()` | Détecte format SEARCH/REPLACE |
| `detect_json_format()` | Détecte format JSON legacy |
| `is_finish_signal()` | Détecte signaux de fin de tâche |
| `has_error_pattern()` | Détecte patterns d'erreur |

**Usage**:
```python
from core.orchestration.detectors import get_mutation_detector

detector = get_mutation_detector()
if detector.detect_mutation_complete(content):
    # Process mutation
```

---

### `agent_invoker.py`

**Classe**: `AgentInvoker`

| Méthode | Description |
|---------|-------------|
| `get_claude_driver()` | Crée driver Claude avec model routing |
| `invoke_agent()` | Invoque agent actif avec budget check |
| `invoke_for_swarm()` | Invoque pour HybridSwarmEngine |
| `invoke_spawned_agent()` | Invoque agent spawné avec system prompt |
| `invoke_agent_direct()` | Invocation thread-safe directe |
| `record_invocation()` | Enregistre métriques DyLAN |
| `calculate_quality_score()` | Calcule score qualité |

**Usage**:
```python
invoker = AgentInvoker(orchestrator)
response = invoker.invoke_agent(TaskType.BRAINSTORM, context)
```

---

### `swarm_bridge.py`

**Classe**: `SwarmBridge`

| Méthode | Description |
|---------|-------------|
| `start_swarm_mode()` | Initialise mode swarm |
| `process_with_swarm()` | Exécute pipeline swarm complet |
| `get_swarm_stats()` | Récupère statistiques swarm |

**Usage**:
```python
bridge = SwarmBridge(orchestrator)
result = bridge.process_with_swarm(task_input, force_mode=CollaborationMode.PARALLEL)
```

---

### `fsm_handlers.py`

**Classe**: `FSMHandlers`

| Handler | État FSM |
|---------|----------|
| `handle_idle()` | IDLE - Routing par complexité |
| `handle_waiting_user()` | WAITING_USER - Attente nouvelle entrée |
| `handle_brainstorming()` | BRAINSTORMING - Débat agents |
| `handle_executing_tool()` | EXECUTING_TOOL - Exécution outil |
| `handle_validating_cfl()` | VALIDATING_CFL - Validation CFL |
| `handle_evolution_brainstorm()` | EVOLUTION_BRAINSTORM - Mode évolution |
| `handle_swarm_analyzing()` | SWARM_ANALYZING - Analyse swarm |
| `handle_swarm_negotiating()` | SWARM_NEGOTIATING - Négociation mode |
| `handle_swarm_executing()` | SWARM_EXECUTING - Exécution swarm |
| `handle_error()` | ERROR - État erreur |
| `handle_panic()` | PANIC - État panique |

**Usage**:
```python
handlers = FSMHandlers(orchestrator)

# Dans process_turn():
if state == OrchestratorState.IDLE:
    return handlers.handle_idle(user_input)
elif state == OrchestratorState.BRAINSTORMING:
    return handlers.handle_brainstorming()
# ...
```

---

## Migration Strategy

### Phase 14c (Current)

1. **Extraction**: Modules créés avec code extrait
2. **Composition**: OrchestratorV7 utilise modules via composition
3. **Compatibilité**: API publique inchangée

### Futur (V8.0)

1. **Dispatcher**: `process_turn()` devient simple dispatcher
2. **StateHandler**: Pattern State complet avec classes par état
3. **Tests**: Tests unitaires par module

---

## Intégration avec OrchestratorV7

```python
# core/orchestration_v7.py
class OrchestratorV7:
    def __init__(self, ...):
        # ... existing init ...

        # V7.8 Phase 14c: Extracted modules
        self.context_builder = ContextBuilder(self)
        self.mutation_detector = get_mutation_detector()
        self.agent_invoker = AgentInvoker(self)
        self.swarm_bridge = SwarmBridge(self)
        self.fsm_handlers = FSMHandlers(self)

    def process_turn(self, user_input: Optional[str] = None) -> Dict:
        # Dispatcher pattern
        if self.state == OrchestratorState.IDLE:
            return self.fsm_handlers.handle_idle(user_input)
        elif self.state == OrchestratorState.BRAINSTORMING:
            return self.fsm_handlers.handle_brainstorming()
        # ...
```

---

## Tests

```bash
# Vérifier que les imports fonctionnent
python -c "from core.orchestration import ContextBuilder, FSMHandlers; print('OK')"

# Lancer les tests d'intégration existants
python -m pytest tests/test_hive_mind_execution.py -v
```

---

## Métriques Phase 14c

| Métrique | Avant | Après |
|----------|-------|-------|
| Lignes `orchestration_v7.py` | 2223 | ~1500 (cible) |
| Modules | 1 | 6 |
| Responsabilités par module | ~10 | 1-2 |
| Testabilité | Faible | Moyenne |

---

## Dépendances

### Internes
- `core.fsm` - États et transitions
- `core.drivers` - Drivers Claude/Gemini
- `core.routing` - Model routing
- `core.synapse` - Protocole et mémoire
- `core.swarm` - HybridSwarmEngine
- `core.telemetry` - Métriques

### Externes
- `tiktoken` - Token counting
- `pydantic` - Validation

---

## Voir Aussi

- [core/README.md](../README.md) - Documentation core module
- [ROADMAP_HIVE_MIND.md](../../ROADMAP_HIVE_MIND.md) - Phase 14c details
- [core/fsm/README.md](../fsm/README.md) - FSM documentation
