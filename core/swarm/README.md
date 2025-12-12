# Swarm Module - NEXUS V9.0

## Rôle

Le module Swarm (Sprint 9) permet la **sélection dynamique du mode de collaboration** où les agents négocient la manière optimale de travailler ensemble pour chaque tâche.

### Évolution V8.x / V9.0

| Version | Feature |
|---------|---------|
| V7.8 | Suppression code GoT mort, Phase 15 Agent-as-Tool |
| **V8.3.0** | SwarmBridge - HiveMind peut déléguer au Swarm |
| **V8.3.1** | SwarmTool - Invocation via `swarm_delegate` tool |
| **V8.3.1-hotfix** | Depth Guard anti-recursion (MAX_DEPTH=2) |
| **V8.3.3** | MergeStrategy - Intelligent result aggregation |
| **V8.4.0** | UnifiedAgentRegistry integration |
| **V8.4.4** | Thread-safety fix (ThreadPoolExecutor + Lock) |
| **V8.8** | **GROK-002**: Exponential Decay + Domain Boost (SuccessMemory) |
| **V8.8** | **GROK-004**: AdaptiveFallbackSelector (context-aware fallbacks) |

## Architecture

```
                         USER INPUT
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID SWARM ENGINE                          │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │   TaskAnalyzer   │──▶│   ModeSelector   │──▶│ Negotiation │  │
│  │  • Complexity    │   │   • DyLAN scores │   │  Protocol   │  │
│  │  • Domains       │   │   • Mode scoring │   │  • Hybrid   │  │
│  └──────────────────┘   └──────────────────┘   └─────────────┘  │
│                                                      │          │
│                                                      ▼          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MODE EXECUTORS                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐  │   │
│  │  │ PARALLEL │ │SEQUENTIAL│ │LEAD_SUPPORT│ │PING_PONG │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘ └──────────┘  │   │
│  │  ┌────────────┐ ┌──────────┐                             │   │
│  │  │ SPECIALIST │ │ RED_BLUE │                             │   │
│  │  └────────────┘ └──────────┘                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Composants Principaux

| Fichier | Rôle | Classes/Fonctions clés |
|---------|------|------------------------|
| `hybrid_swarm_engine.py` | Moteur principal | `HybridSwarmEngine`, `SwarmResult` |
| `task_analyzer.py` | Analyse tâches | `TaskAnalyzer`, `TaskComplexity`, `TaskDomain` |
| `mode_selector.py` | Sélection mode | `ModeSelector`, `ModeProposal` |
| `collaboration_modes.py` | Définitions modes | `CollaborationMode`, `ModeCharacteristics` |
| `negotiation_protocol.py` | Négociation agents | `NegotiationProtocol`, `NegotiationResult` |
| `mode_executors.py` | Exécution + self-healing | `ParallelExecutor`, `execute_with_fallback()` |
| `merge_strategies.py` | **V8.3.3** Fusion résultats | `MergeStrategy`, `IntelligentMerger` |
| `agent_metrics.py` | DyLAN + scoring | `AgentProfile`, `AgentPool` |
| `session_manager.py` | Isolation session | `SwarmSessionManager`, `TaskSession` |
| `adaptive_fallback.py` | **V8.8** Fallback contextuel | `AdaptiveFallbackSelector`, `FallbackContext` |

## Modes de Collaboration (6)

| Mode | Description | Cas d'usage | Affinité Complexité |
|------|-------------|-------------|---------------------|
| **PARALLEL** | Travail simultané, fusion résultats | Sous-tâches indépendantes | 0.5 |
| **SEQUENTIAL** | Exécution ordonnée | Dépendances claires | 0.6 |
| **LEAD_SUPPORT** | Lead (80%) + Support (20%) | Expertise dominante | 0.7 |
| **PING_PONG** | Alternance rapide | Brainstorming, créativité | 0.6 |
| **SPECIALIST** | Un seul expert | Expertise exclusive | 0.8 |
| **RED_BLUE** | Adversarial propose/attaque/défend | Sécurité, décisions critiques | 1.0 |

### Chaîne de Fallback (Phase 8: Self-Healing)

**Chaîne Statique** (legacy):
```
PARALLEL    → SEQUENTIAL
RED_BLUE    → LEAD_SUPPORT
LEAD_SUPPORT → SPECIALIST
PING_PONG   → SEQUENTIAL
SEQUENTIAL  → SPECIALIST
SPECIALIST  → None (terminal)
```

### AdaptiveFallbackSelector (V8.8 - GROK-004)

**Nouveau**: Sélection de fallback contextuel remplaçant les chaînes statiques.

```python
from core.swarm.adaptive_fallback import (
    AdaptiveFallbackSelector,
    FallbackContext,
    get_adaptive_fallback_selector
)

selector = get_adaptive_fallback_selector()
decision = selector.get_adaptive_fallback(
    current_mode=CollaborationMode.PARALLEL,
    context=FallbackContext(
        domains=["coding"],
        complexity="moderate",
        stagnation_level="high"  # none, low, moderate, high, critical
    )
)

print(f"Fallback: {decision.fallback_mode}")   # SPECIALIST (shortcut)
print(f"Reason: {decision.reason}")            # "High stagnation - skipping to specialist"
print(f"Confidence: {decision.confidence}")    # 0.85
```

**Facteurs de décision** (ordre de priorité):
1. **Stagnation Level** - High/critical → shortcut vers SPECIALIST
2. **Domain Affinity** - `coding` préfère `lead_support`, `research` préfère `sequential`
3. **Historical Performance** - SuccessMemory pour les patterns réussis
4. **Static Chain** - Fallback par défaut si aucun contexte

**Domain Fallback Preferences**:
| Mode | coding | research | security | default |
|------|--------|----------|----------|---------|
| PARALLEL | lead_support | sequential | red_blue | sequential |
| RED_BLUE | lead_support | specialist | specialist | lead_support |
| LEAD_SUPPORT | specialist | specialist | specialist | specialist |
| PING_PONG | lead_support | sequential | sequential | sequential |

**Stagnation Shortcuts**:
| Mode | Shortcut | Skip |
|------|----------|------|
| PARALLEL | specialist | SEQUENTIAL |
| RED_BLUE | specialist | LEAD_SUPPORT |
| PING_PONG | specialist | SEQUENTIAL |

## Phase Status (V8.3.x)

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 7** | Session Isolation (SwarmSessionManager) | ✅ |
| **Phase 8** | Self-Healing Swarm (Fallback) | ✅ |
| **Phase 10a** | Success Memory | ✅ |
| **Phase 10b** | Memory-Augmented Mode Selection | ✅ |
| **Phase 10d** | Session-Aware Agent Selection | ✅ |
| **Phase 5b** | N-Agent Agnosticism (Spawned Agents) | ✅ |
| **Phase 14e** | Force Chain-of-Thought (EXPERT) | ✅ |
| **Phase 14c** | GoT code removal (-206 lignes) | ✅ |
| **Phase 15** | Agent-as-Tool integration | ✅ |
| **V8.3.0** | SwarmBridge (Dictator Mode) | ✅ **[NEW]** |
| **V8.3.1** | SwarmTool (swarm_delegate) | ✅ **[NEW]** |
| **V8.3.1-hotfix** | Depth Guard (anti-recursion) | ✅ **[NEW]** |

---

## Complexité des Tâches

| Niveau | Valeur | Description | Négociation | CoT Forcé |
|--------|--------|-------------|-------------|-----------|
| `TRIVIAL` | 1 | Tâches mono-étape | Skip | Non |
| `SIMPLE` | 2 | Opérations basiques | Minimal | Non |
| `MODERATE` | 3 | Tâches standard | Full | Non |
| `COMPLEX` | 4 | Planification multi-étapes | Extended | Non |
| `EXPERT` | 5 | Décisions critiques | RED_BLUE | **Oui** |

### Force Chain-of-Thought (Phase 14e)

Pour EXPERT, injection automatique de l'instruction CoT:

```xml
<instruction>BEFORE answering or using tools, you MUST wrap your step-by-step reasoning in <thinking>...</thinking> tags.</instruction>
```

---

## Scoring Session-Aware (Phase 10d)

```python
Score = (DyLAN_importance × 0.7) + (Session_success_rate × 0.3)

# Bonus session
HIGH_SESSION_BONUS = 0.08   # Success rate ≥ 0.8
MEDIUM_SESSION_BONUS = 0.05 # Success rate ≥ 0.6
LOW_SESSION_BONUS = 0.02    # Success rate ≥ 0.4
```

---

## Interactions et Flux de Données

```mermaid
graph TB
    subgraph "Swarm Module"
        HSE[HybridSwarmEngine]
        TA[TaskAnalyzer]
        MS[ModeSelector]
        NP[NegotiationProtocol]
        ME[ModeExecutors]
        SM[SessionManager]
    end

    subgraph "Consumers"
        OV7[OrchestratorV7]
        SB[SwarmBridge]
    end

    subgraph "Dépendances"
        AM[AutoMemory]
        AP[AgentPool]
        ATR[AgentToolRegistry]
    end

    OV7 -->|via| SB
    SB -->|process_task| HSE

    HSE -->|analyze| TA
    HSE -->|select| MS
    HSE -->|negotiate| NP
    HSE -->|execute| ME

    MS -->|recommendations| AM
    ME -->|sessions| SM
    ME -->|agent tools| ATR
```

---

## Usage

### Traitement Basique

```python
from core.swarm import HybridSwarmEngine

engine = HybridSwarmEngine(
    agent_pool=agent_pool,
    model_router=router,
    config=config,
    invoke_agent=orchestrator._invoke_for_swarm,
    workspace_path=workspace_path
)

result = engine.process_task("Review the auth module security")

print(f"Mode: {result.mode}")        # RED_BLUE
print(f"Status: {result.status}")    # SUCCESS
```

### Force Mode Spécifique

```python
result = engine.process_task(
    "Write unit tests",
    forced_mode=CollaborationMode.SPECIALIST
)
```

### Skip Négociation

```python
result = engine.process_task(
    "Quick fix",
    skip_negotiation=True
)
```

---

## Configuration

```bash
# Core
SWARM_ENABLED=True                  # Activer swarm engine
SWARM_AUTO_ROUTE=True               # Auto-route MODERATE+ tasks
SWARM_NEGOTIATION=True              # Activer phase négociation
SWARM_NEGOTIATION_TURNS=4           # Max rounds négociation
SWARM_DEFAULT_MODE=ping_pong        # Mode fallback
SWARM_MAX_ROUNDS=6                  # Max rounds exécution

# Session (Phase 7)
SWARM_SESSION_RETENTION_HOURS=24    # Durée rétention sessions

# Self-Healing (Phase 8)
SWARM_MAX_FALLBACKS=2               # Max tentatives fallback
```

---

## Fichiers Clés

| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `mode_executors.py` | ~1302 | Exécution modes + self-healing fallback |
| `mode_selector.py` | ~981 | Sélection mode via DyLAN scores |
| `hybrid_swarm_engine.py` | ~757 | Moteur principal d'orchestration |
| `session_manager.py` | ~669 | Isolation sessions parallèles |
| `negotiation_protocol.py` | ~635 | Négociation inter-agents |
| `agent_metrics.py` | ~628 | DyLAN metrics + AgentPool |
| `task_analyzer.py` | ~518 | Analyse complexité/domaines |
| `adaptive_fallback.py` | ~417 | GROK-004: Fallback contextuel |
| `merge_strategies.py` | ~353 | Fusion résultats (IntelligentMerger) |
| `task_completion_validator.py` | ~319 | Validation complétion tâches |
| `collaboration_modes.py` | ~234 | Définitions 6 modes |
| `__init__.py` | ~185 | Exports publics |

**Total**: ~6,998 lignes

---

## Notes d'Audit Local

### [V8.3.x] Changements

**V8.3.0 SwarmBridge:**
- Nouveau composant `core/hive_mind/swarm_bridge.py`
- Guardrails: modes autorisés par phase HiveMind
- Self-healing avec checkpoints (create/restore)

**V8.3.1 SwarmTool:**
- Handler `_execute_swarm_delegate()` dans ToolManager
- Wrapper async→sync pour intégration
- Feedback loop: injection résultats dans contexte

**V8.3.1-hotfix Depth Guard:**
- `MAX_SWARM_DEPTH = 2` (anti-recursion)
- Paramètre `_swarm_depth` propagé entre appels
- Erreur explicite si profondeur dépassée

### Points d'attention
- **Thread-safety**: `threading.RLock` sur opérations critiques
- **Session cleanup**: 24h retention par défaut
- **Fallback chain**: Testé via `test_self_healing.py`
- **Depth Guard**: Testé via `test_swarm_tool.py`

---

## Dépendances

**Importe**:
- `core/memory/` - SuccessMemory, AutoMemory
- `core/drivers/` - GeminiDriverV7, ClaudeDriverHybrid
- `core/api/rate_limiter.py` - APIRateLimiter (PARALLEL mode)
- `core/utils/atomic_store.py` - AtomicJsonStore (sessions)

**Importé par** (via grep):
- `core/orchestration_v7.py:28-30` - AgentPool, HybridSwarmEngine
- `core/orchestration/swarm_bridge.py:19` - CollaborationMode, SwarmPhase
- `core/adapters/analysis_adapter.py:30` - TaskAnalysis, TaskComplexity
- `core/bootstrap/agent_loader.py:24` - AgentProfile
- `core/execution/tool_manager.py:1763` - CollaborationMode
- `core/execution/agent_tools.py:47` - AgentPool, AgentProfile

## Tests

- `tests/test_swarm_*.py` - Tests Swarm Engine
- `tests/test_self_healing.py` - Fallback chain
- `tests/test_cot_enforcement.py` - Force CoT EXPERT
- `tests/test_automemory_integration.py` - Memory-augmented selection

## Voir Aussi

- [core/memory/README.md](../memory/README.md) - SuccessMemory pour scoring
- [core/orchestration/README.md](../orchestration/README.md) - SwarmBridge
- [core/execution/README.md](../execution/README.md) - AgentToolRegistry
- [core/fsm/README.md](../fsm/README.md) - États SWARM_*
- [docs/PHASE_14E_COT_ENFORCEMENT.md](../../docs/PHASE_14E_COT_ENFORCEMENT.md) - Force CoT
