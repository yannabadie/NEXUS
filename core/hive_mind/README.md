# Module : core/hive_mind

## Rôle dans l'Architecture NEXUS V8.3.x

**TRUE HIVE MIND** - Orchestrateur de collaboration intelligente pour tâches complexes.

Ce module transforme NEXUS d'un orchestrateur séquentiel en une **intelligence collaborative** où Gemini et Claude travaillent ensemble à travers un pipeline structuré de 7 phases. Il gère les tâches de complexité MODERATE, COMPLEX et EXPERT.

```
V7 Swarm (TRIVIAL/SIMPLE) vs V8 Hive Mind (MODERATE/COMPLEX/EXPERT)
```

### Nouveautés V8.3.x

| Version | Feature | Description |
|---------|---------|-------------|
| **V8.3.0** | SwarmBridge | HiveMind peut déléguer au Swarm (Dictator Mode) |
| **V8.3.1** | SwarmTool | Agents peuvent invoquer `swarm_delegate` à n'importe quelle phase |
| **V8.3.1-hotfix** | Depth Guard | Anti-recursion (MAX_SWARM_DEPTH=2) |

## Composants Clés

### Orchestration
| Fichier | Rôle |
|---------|------|
| `orchestrator.py` | **TrueHiveMind** - Coordinateur principal du pipeline 7 phases |
| `types.py` | Dataclasses et enums (HiveMindState, IndependentAnalysis, DebateArgument, etc.) |
| `swarm_bridge.py` | **SwarmBridge** (V8.3.0) - Pont HiveMind → Swarm pour délégation |

### Infrastructure
| Fichier | Rôle |
|---------|------|
| `agent_registry.py` | **AgentRegistry** - Anti-duplication avec recherche par similarité Jaccard |
| `cost_estimator.py` | **CostEstimator** - Contrôle budget tokens + intégration BudgetTracker (USD) |
| `context_manager.py` | **HiveMindContextManager** - Fenêtre glissante pour éviter explosion tokens |
| `strategy_blacklist.py` | **StrategyBlacklist** - Anti-retry circulaire avec suggestions alternatives |
| `user_interaction.py` | **UserInteractionHandler** - Breakpoints utilisateur avec UI Rich |
| `adaptive_debate.py` | **AdaptiveDebateConfig** - Paramètres débat adaptatifs (3-10 tours) |
| `success_adapter.py` | **SuccessAdapter** (V8.2.0) - Feedback loop vers SuccessMemory |

### Phases
| Sous-module | Description |
|-------------|-------------|
| `phases/` | 7 phases du pipeline (voir `phases/README.md`) |

## Architecture & Flux

### Pipeline 7 Phases

```
                    +------------------+
                    |  HIVE_GATING     |  <- Decides V7 Swarm vs V8 Hive Mind
                    +--------+---------+
                             |
              +--------------v--------------+
              |  PHASE 1: Independent       |
              |  Analysis (Gemini + Claude) |
              +--------------+--------------+
                             |
              +--------------v--------------+
              |  PHASE 2: Strategic Debate  |
              |  (Adaptive 3-10 turns)      |
              +--------------+--------------+
                             |
                   [BREAKPOINT: AFTER_DEBATE]
                             |
              +--------------v--------------+
              |  PHASE 3: Architecture      |
              |  Generation + Spawn         |
              +--------------+--------------+
                             |
                   [BREAKPOINT: BEFORE_SPAWN]
                             |
    +------------------------v------------------------+
    |                PHASE 4: Execution               |
    |                (Monitored Steps)                |
    +------------------------+------------------------+
                             |
                    +--------v--------+
                    | Success?        |
                    +--+----------+---+
                       |          |
                      YES         NO
                       |          |
                       |   +------v-------+
                       |   | PHASE 5:     |
                       |   | Diagnosis    |
                       |   +------+-------+
                       |          |
                       |  [BREAKPOINT: AFTER_DIAGNOSIS]
                       |          |
                       |   +------v-------+
                       |   | PHASE 6:     |
                       |   | Adaptive     |
                       |   | Retry        |
                       |   +------+-------+
                       |          |
              +--------v----------v--------+
              |  PHASE 7: Knowledge        |
              |  Consolidation             |
              +-------------+--------------+
                            |
                   [BREAKPOINT: KNOWLEDGE_CONSOLIDATION]
                            |
                    +-------v-------+
                    | HIVE_SUCCESS  |
                    | or HIVE_FAILED|
                    +---------------+
```

### Entrees
- **Task description** (string) depuis FSMHandlers via `_route_to_hive_mind()`
- **TaskComplexity** (enum) depuis TaskAnalyzer
- **Config** avec parametres `hive_mind_*`
- **Drivers** Gemini et Claude

### Sorties
- **HiveMindResult** dataclass contenant:
  - `success`: bool
  - `output`: string formatee
  - `phases_completed`: liste des phases executees
  - `total_tokens`: cout total
  - `agents_spawned`: nouveaux agents crees
  - `knowledge_archived`: insights archives dans RAG

### Configuration (Variables ENV)

| Variable | Default | Description |
|----------|---------|-------------|
| `HIVE_MIND_ENABLED` | True | Active/desactive V8 Hive Mind |
| `HIVE_MIND_MODERATE` | True | Route MODERATE vers Hive Mind (False = V7 Swarm) |
| `HIVE_MIND_BUDGET` | 50000 | Limite tokens par tache |
| `HIVE_MIND_MAX_DEBATE` | 10 | Tours de debat maximum |
| `HIVE_MIND_MIN_DEBATE` | 3 | Tours de debat minimum |
| `HIVE_MIND_BREAKPOINTS` | True | Active breakpoints utilisateur |
| `HIVE_MIND_MAX_RETRIES` | 3 | Tentatives retry maximum |
| `HIVE_MIND_AGREEMENT_THRESHOLD` | 0.85 | Seuil consensus pour skip debat |

## Dependances

### Utilise
```python
# Drivers
from core.drivers.gemini_driver_v7 import GeminiDriverV7
from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid

# Telemetry (integration V8.0)
from core.telemetry.budget_tracker import BudgetTracker

# Memory (RAG archival)
from core.memory.project_memory import ProjectMemory

# FSM (stagnation detection)
from core.fsm.stagnation_detector import StagnationDetector

# External (optional)
from rich.console import Console  # UI breakpoints
```

### Utilise par
```python
# Orchestration
core.orchestration.fsm_handlers.FSMHandlers._route_to_hive_mind()

# Tests
tests.test_hive_mind_e2e
tests.test_v8_integrations
tests.verify_hive_mind_routing
```

## Diagramme: Integrations V7 -> V8

```mermaid
graph LR
    subgraph V7_Components
        FSM[fsm_handlers.py]
        BD[BudgetTracker]
        SD[StagnationDetector]
        PM[ProjectMemory]
    end

    subgraph V8_Hive_Mind
        THM[TrueHiveMind]
        CE[CostEstimator]
        SB[StrategyBlacklist]
        CM[ContextManager]
    end

    FSM -->|complexity >= MODERATE| THM
    BD -->|USD limits| CE
    SD -->|stagnation reports| SB
    CM -->|archive insights| PM

    style THM fill:#f9f,stroke:#333
    style FSM fill:#bbf,stroke:#333
```

## Exemple d'Utilisation

```python
from core.hive_mind import TrueHiveMind, HiveMindResult

# Initialisation
hive = TrueHiveMind(
    workspace_path=workspace_path,
    config=config,
    gemini_driver=gemini_driver,
    claude_driver=claude_driver,
    budget_tracker=budget_tracker,  # V8.0 integration
    project_memory=project_memory   # RAG archival
)

# Execution
result: HiveMindResult = await hive.process_task(
    task="Refactor authentication module with OAuth2 support",
    complexity=TaskComplexity.COMPLEX
)

# Statistiques
stats = hive.get_stats()
print(f"Tokens spent: {stats['cost_stats']['total_spent']}")
print(f"Phases completed: {result.phases_completed}")
```

## Tests Associes

| Fichier | Coverage |
|---------|----------|
| `tests/test_hive_mind_e2e.py` | End-to-end pipeline |
| `tests/test_v8_integrations.py` | Integrations V7->V8 |
| `tests/verify_hive_mind_routing.py` | Routing complexite |

## Notes Techniques

### Thread Safety
- `AgentRegistry`: Thread-safe avec `threading.Lock`
- `StrategyBlacklist`: Thread-safe avec persistence JSON
- `ContextManager`: Non thread-safe (single-task design)

### Performance
- Cost estimation: O(1) per operation
- Registry similarity search: O(n) avec n = agents actifs
- Context eviction: O(n log n) avec n = items en contexte

### Limites Connues
- Breakpoints synchrones (bloquent le pipeline)
- Pas de parallelisation intra-phase
- Context limit de 50k tokens par défaut

---

## V8.3 SwarmBridge - Dictator Mode

### Concept

SwarmBridge permet au HiveMind de **déléguer des sous-tâches au Swarm Engine** tout en gardant le contrôle stratégique:

```
HiveMind (Stratège) → SwarmBridge → Swarm Engine (Tacticien)
```

### Guardrails: Modes Autorisés par Phase

| Phase | Modes Autorisés |
|-------|-----------------|
| ANALYSIS | SPECIALIST |
| DEBATE | PING_PONG, RED_BLUE |
| ARCHITECTURE | LEAD_SUPPORT |
| EXECUTION | PARALLEL, SEQUENTIAL, SPECIALIST |
| DIAGNOSIS | RED_BLUE |
| CONSOLIDATION | SPECIALIST |

### Exemple d'Utilisation

```python
from core.hive_mind.swarm_bridge import SwarmBridge, HivePhase
from core.swarm.collaboration_modes import CollaborationMode

bridge = SwarmBridge(swarm_engine, context_manager)

result = await bridge.delegate(
    task="Run security review",
    mode=CollaborationMode.RED_BLUE,
    phase=HivePhase.DIAGNOSIS
)

if result.success:
    bridge.inject_results_into_context(result)
```

### Self-Healing (V8.3.1)

SwarmBridge supporte les checkpoints pour restauration sur fallback:

```
Mode A (échec) → Checkpoint restauré → Mode B (fallback) → Success
```

---

## V8.3.1 SwarmTool - Swarm comme Outil

### swarm_delegate Tool

Les agents peuvent invoquer le Swarm via l'outil `swarm_delegate`:

```xml
<tool_use name="swarm_delegate">
{
  "task": "Débattre de l'approche d'auth",
  "mode": "red_blue",
  "phase": "debate"
}
</tool_use>
```

### Depth Guard (Anti-Recursion)

```
MAX_SWARM_DEPTH = 2
```

Prévient la "Inception Trap": Swarm → swarm_delegate → Swarm → ... (infini)

### Diagramme SwarmTool

```mermaid
graph TB
    subgraph "HiveMind Phase"
        A[Agent Claude/Gemini]
    end

    subgraph "Tool Execution"
        TM[ToolManager]
        SD[swarm_delegate]
    end

    subgraph "SwarmBridge"
        SB[SwarmBridge.delegate]
        VAL[validate_mode_for_phase]
        FB[execute_with_fallback]
    end

    subgraph "Swarm Engine"
        HSE[HybridSwarmEngine]
    end

    A -->|"invoke tool"| TM
    TM -->|"swarm_delegate"| SD
    SD -->|"check depth"| SD
    SD -->|"delegate"| SB
    SB -->|"validate"| VAL
    SB -->|"execute"| FB
    FB -->|"call"| HSE
    HSE -->|"result"| FB
    FB -->|"inject"| SB
    SB -->|"ToolResult"| SD
    SD -->|"return"| TM
    TM -->|"response"| A
```
