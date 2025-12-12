# Hive Mind Module - NEXUS V9.2

## Rôle
Le module `core/hive_mind` est le cerveau stratégique de NEXUS. Contrairement au Swarm (tactique), le Hive Mind gère la planification à long terme, la négociation des rôles (via `Architect`), et la résilience des tâches complexes (via `SagaManager`).

## Fichiers Clés
| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `orchestrator.py` | ~270 | **TrueHiveMind**: Orchestrateur principal du pipeline stratégique (7 phases). |
| `architect.py` | ~110 | **Architect**: Négocie les rôles (Gemini/Claude/Spawn) et décide de la délégation. |
| `swarm_bridge.py` | ~200 | **Bridge**: Connecte le Hive Mind (Stratégie) au Swarm (Exécution). |
| `saga_manager.py` | ~230 | **Resilience**: Gère les checkpoints et la reprise après erreur (Saga Pattern). |
| `adaptive_debate.py` | ~160 | **Debate**: Gère la phase de débat contradictoire avant exécution. |

## API Publique
```python
from core.hive_mind import (
    TrueHiveMind,
    Architect,
    SagaManager,
    SwarmBridge
)

# Usage
hive = TrueHiveMind(workspace_path, config)
result = await hive.process_task("Build a complex app")
```

## Flux de Données

### Hive Mind Pipeline (7 Phases)
```mermaid
flowchart TD
    Start[Task] --> Analysis
    Analysis --> Debate
    Debate --> Architecture
    Architecture --> Execution
    Execution --> Diagnosis
    Diagnosis -- Error --> Retry
    Diagnosis -- Success --> Consolidation
    Retry --> Debate
```

### Architect Negotiation
```mermaid
flowchart LR
    Task --> Architect
    Architect --> Heuristics[Fast Path]
    Architect --> LLM[Slow Path]
    Heuristics -- Decision --> Result
    LLM -- Negotiation --> Result
    Result --> Role[Gemini/Claude/Spawn]
```

## Dépendances

**Importe :**
- `core/swarm` : Pour déléguer l'exécution tactique.
- `core/agents` : Pour spawner de nouveaux agents (`UnifiedRegistry`).
- `core/memory` : Pour la consolidation des connaissances.

**Importé par :**
- `core/orchestration_v7.py` : Intègre le Hive Mind dans la boucle principale FSM.
- `core/orchestration/fsm_handlers.py` : Gère les transitions vers/depuis le Hive Mind.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HIVE_MIND_ENABLED` | `True` | Active le pipeline stratégique complet. |
| `ARCHITECT_MODEL` | `gemini-pro` | Modèle utilisé pour la négociation des rôles. |

## Tests

- `tests/hive_mind/test_orchestrator.py`
- `tests/hive_mind/test_architect.py`
- `tests/e2e/test_hive_mind_pipeline.py`
