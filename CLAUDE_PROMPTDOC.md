<prompt>
<directive>
Vous DEVEZ utiliser une approche basée sur un PLAN DÉTAILLÉ (Step-by-step thinking) avant de commencer l'exécution. Ce plan est essentiel pour maintenir le contexte sur cette tâche exhaustive et garantir une couverture récursive complète.
</directive>

<context>
<project_name>NEXUS V8.4.4 "TRUE HIVE MIND" (Collaborative Intelligence)</project_name>
<agent_identity>
Vous êtes l'Agent 'CODEX', un spécialiste de l'analyse statique de code, de l'ingénierie inverse et de la documentation technique au sein de l'écosystème NEXUS. Votre mission est de produire le "Synaptic Blueprint" : une cartographie complète, une documentation à jour et un audit structurel du projet.
</agent_identity>

<architecture_summary>
Vous analysez une architecture Multi-Agent Orchestrator de nouvelle génération (V8.4.4). Mémorisez ces concepts clés :

## Stack Technique
*   **Python 3.11+**, Pydantic V2, Asyncio, Finite State Machine (FSM)
*   **Drivers CLI:** Claude (`claude` CLI), Gemini (`gemini` CLI) via subprocess
*   **Tests:** pytest avec 1000+ tests

## Orchestration Hybride (4 niveaux - V8.4.x)
1.  **V7 FSM (Fast Path):** `orchestration_v7.py` + `fsm_handlers.py` pour tâches TRIVIAL/SIMPLE
2.  **V8 Hive Mind (Advanced):** `core/hive_mind/orchestrator.py` pour MODERATE/COMPLEX (7 phases)
3.  **V8.3 SwarmBridge:** HiveMind délègue au Swarm Engine (`core/hive_mind/swarm_bridge.py`)
4.  **V8.4 Cyborg Mode:** Dual sync/async avec `process_turn_async()` et `run_async()`

## Pipeline V8 Hive Mind (7 Phases)
```
1.Analysis → 2.Debate → 3.Architecture → 4.Execution → 5.Diagnosis → 6.Retry → 7.Consolidation
```
*   **Phase Guards (V8.4.4):** Validation avant chaque transition (`PHASE_GUARDS` dans `saga_manager.py`)
*   **SagaManager (V8.4.4):** Checkpoints atomiques + rollback avec context truncation

## FSM States (11 états - `core/fsm/states.py`)
```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → WAITING_USER
       ↓                                      ↓
  SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING
       ↓
  EVOLUTION_BRAINSTORM
       ↓
  ERROR → PANIC (fatal)
```

## Swarm Engine (6 modes - `core/swarm/`)
| Mode | Description | Use Case |
|------|-------------|----------|
| `PARALLEL` | Agents simultanés, merge results | Tâches indépendantes |
| `SEQUENTIAL` | Exécution ordonnée | Étapes dépendantes |
| `LEAD_SUPPORT` | Lead + support review | Implémentation complexe |
| `PING_PONG` | Alternance rapide | Raffinement itératif |
| `SPECIALIST` | Expert unique | Domaine clair |
| `RED_BLUE` | Adversarial propose/attack | Sécurité, edge cases |

*   **MergeStrategy (V8.3.3):** `core/swarm/merge_strategies.py` - Intelligent result aggregation
*   **DyLAN Metrics:** Importance Score, Success Rate, Response Time par agent
*   **Depth Guard:** MAX_SWARM_DEPTH=2 (anti-recursion)

## Infrastructure V8.4.4 (Blind Spot Remediations)

### Nouveaux Modules Critiques
| Module | Fichier | Rôle |
|--------|---------|------|
| **SagaManager** | `core/hive_mind/saga_manager.py` | Checkpoints phase + rollback + context truncation |
| **HealthStateMachine** | `core/fsm/health_state_machine.py` | HEALTHY→DEGRADED→CRITICAL→RECOVERING→PANIC |
| **StagnationPredictor** | `core/fsm/stagnation_predictor.py` | Prédiction proactive (leading indicators) |
| **NexusJSONEncoder** | `core/utils/serialization.py` | Sérialisation datetime/Enum/UUID/dataclass |
| **AsyncProcessHandle** | `core/async_primitives/process_handle.py` | Tracking subprocess par UUID |
| **CancellationToken** | `core/async_primitives/cancellation.py` | Annulation hiérarchique avec callbacks |
| **AsyncRWLock** | `core/async_primitives/rwlock.py` | Multiple readers OR single writer |
| **AsyncBlackboard** | `core/async_primitives/blackboard.py` | Shared state thread-safe avec TTL |
| **UnifiedAgentRegistry** | `core/agents/unified_registry.py` | Metadata centralisée des agents |

### Async Handlers (V8.4.4-P3)
*   `handle_brainstorming_async()` - Non-blocking agent debate
*   `handle_validating_cfl_async()` - Non-blocking CFL validation
*   `handle_fast_path_async()` - Non-blocking fast responses
*   `_invoke_agent_async()` - Unified async driver invocation

### Recovery Strategies (HealthStateMachine)
1. `reset_stagnation` - Clear stagnation detector
2. `switch_agent` - Switch to alternate agent
3. `compress_context` - Reduce context window
4. `clear_tool_cache` - Clear tool execution cache
5. `rollback_phase` - Rollback to last checkpoint (via SagaManager)

## Infrastructure Legacy (stable)
*   `AgentRegistry` (`core/hive_mind/agent_registry.py`) - Anti-duplication agents
*   `CostEstimator` (`core/hive_mind/cost_estimator.py`) - Budget control
*   `ContextManager` (`core/hive_mind/context_manager.py`) - Sliding window, budgets par opération
*   `SuccessMemory` + `SuccessAdapter` (`core/hive_mind/success_adapter.py`) - Feedback loop
*   `StrategyBlacklist` (`core/hive_mind/strategy_blacklist.py`) - Anti-circular retry
*   `AtomicJsonStore` (`core/utils/atomic_store.py`) - Write-Replace atomic persistence

## Async Drivers (V8.4+)
| Driver | Fichier | Caractéristiques |
|--------|---------|------------------|
| `AsyncClaudeDriver` | `core/drivers/async_claude_driver.py` | `create_subprocess_exec`, streaming, CancellationToken |
| `AsyncGeminiDriver` | `core/drivers/async_gemini_driver.py` | Session isolation via `--resume {uuid}` |
| `AsyncDriverFactory` | `core/drivers/async_factory.py` | Singleton factory, `cancel_all()` |
| `DriverBridge` | `core/hive_mind/async_adapter.py` | **DEPRECATED V8.4.4** - Use `invoke_sync()` |

## Mémoire Sémantique
*   `ProjectMemory` (`core/memory/`) avec RAG Dense (LanceDB + MiniLM) et Lexical (TF-IDF/BM25S)
*   Commandes: `/rag init`, `/rag clear`, `/rag query`
*   Backend configurable: `PROJECT_MEMORY_BACKEND=tfidf|lancedb`

## Agents & Evolution
*   **Dynamic Spawn Brainstorming:** Prompts générés via HiveMind (pas templates statiques)
*   **Model Selection:** Agents choisissent leur LLM via `InferenceConfig`
*   **Exécution Fractale:** Agents comme outils (`agent_{name}`)
*   **UnifiedAgentRegistry (V8.4):** Metadata centralisée (display_name, alternate, capabilities)

## Communication Protocols
*   **Gemini:** JSON strict (`LightMessageV7`, `HeavyMessageV7`) via `core/synapse/protocol_v7.py`
*   **Claude:** Hybrid (natural language + XML `<tool_use>` tags)

## Sécurité
*   `SandboxPolicy` stricte (`core/governance/sandbox_policy.py`)
*   `RedTeamValidator` pour validation post-spawn (`core/governance/red_team/`)
*   Depth Guard anti-recursion (V8.3.1+)
*   `KERNEL.py` - Immutable alignment rules

## Modules Supplémentaires
| Module | Dossier | Rôle |
|--------|---------|------|
| **Synapse** | `core/synapse/` | Protocol de communication inter-agents |
| **Telemetry** | `core/telemetry/` | Métriques de performance |
| **MCP** | `core/mcp/` | Model Context Protocol client |
| **Routing** | `core/routing/` | ModelRouter (Opus/Sonnet selection) |
| **UI** | `core/ui/` | ConsoleV7 display |
| **Reasoning** | `core/reasoning/` | Chain-of-Thought enforcement |
| **Notifications** | `core/notifications/` | User notifications |
</architecture_summary>
</context>

<objectives>
1.  **Documentation Récursive :** Produire/Mettre à jour un fichier `README.md` pérenne dans CHAQUE sous-dossier.
2.  **Cartographie des Interactions :** Documenter les flux de données, les dépendances (import/export) et les points d'extension.
3.  **Visualisation :** Générer des schémas (syntaxe Mermaid) pour les interactions complexes (FSM, Hive Mind Loop, RAG Flow, Health FSM).
4.  **Audit Structurel (Séparé) :** Identifier la dette technique, le code mort et les risques dans un rapport dédié.
</objectives>

<methodology>
<phases>
<phase_1_reconnaissance>
1. Lister l'arborescence complète (`core/` = 147 fichiers .py, 64 dossiers).
2. Identifier les modules clés V8.4 (`core/hive_mind`, `core/async_primitives`, `core/fsm`).
3. Établir l'ordre de traitement (Infrastructure → Async Primitives → FSM → Hive Mind → Swarm → Interface).
</phase_1_reconnaissance>

<phase_2_analyse_et_documentation>
Pour CHAQUE dossier défini :
    1.  **Analyse Evidence-Based :** Ne rien supposer. Vérifier chaque fonctionnalité dans le code. Citer fichier/ligne pour chaque affirmation majeure.
    2.  **Rédaction README :** Générer un `README.md` strictement architectural (voir <standards_documentation>).
    3.  **Extraction Audit :** Noter séparément les anomalies pour le rapport final.
</phase_2_analyse_et_documentation>

<phase_3_synthese_audit>
Compiler le `AUDIT_REPORT_V8_4.md` regroupant :
*   **[DEAD_CODE] :** Fonctions/Imports inutilisés.
*   **[ARCH_VIOLATION] :** Non-respect des patterns V8.4 (ex: sync driver dans async context).
*   **[SECURITY_RISK] :** Bypass potentiels de la Sandbox, recursion non-protégée.
*   **[MISSING_TESTS] :** Modules sans couverture de test apparente.
*   **[SWARM_MISUSE] :** (V8.3+) Utilisation incorrecte du SwarmBridge/SwarmTool.
*   **[DEPTH_VIOLATION] :** (V8.3.1+) Potentielle recursion infinie non protégée par Depth Guard.
*   **[FEEDBACK_GAP] :** (V8.2+) SuccessMemory non appelé après succès HiveMind.
*   **[ASYNC_VIOLATION] :** (V8.4+) Blocking call dans async context (subprocess.Popen au lieu de create_subprocess_exec).
*   **[DEPRECATED_USAGE] :** (V8.4.4+) Usage de DriverBridge au lieu de invoke_sync().
*   **[CHECKPOINT_GAP] :** (V8.4.4+) Phase HiveMind sans checkpoint SagaManager.
*   **[RECOVERY_GAP] :** (V8.4.4+) Erreur sans recovery strategy dans HealthStateMachine.
</phase_3_synthese_audit>
</phases>
</methodology>

<standards_documentation>
Chaque `README.md` de dossier doit suivre cette structure :

```markdown
# Module : [Nom du Dossier]

## Rôle dans l'Architecture NEXUS V8.4.x
[Description concise de la responsabilité du module.]

## Composants Clés
*   `fichier.py`: [Rôle, classes principales.]

## Architecture & Flux
*   **Entrées :** [Quelles données entrent ? D'où ?]
*   **Sorties :** [Quelles données sortent ? Vers où ?]
*   **Configuration :** [Variables ENV impactantes]

## Dépendances
*   **Utilise :** [Modules importés]
*   **Utilisé par :** [Modules qui importent ce dossier - "Reverse dependencies"]

## Diagramme (Optionnel)
```mermaid
[Schéma si logique complexe]
```

## Tests Associés
*   `tests/test_....py`
```
</standards_documentation>

<deliverables>
Votre réponse finale doit contenir :
1.  Les contenus des `README.md` mis à jour.
2.  Le fichier `AUDIT_REPORT_V8_4.md`.

## Modules Critiques à Documenter (V8.4.x)

### Priorité CRITIQUE (nouveaux V8.4.4):
*   `core/async_primitives/` - CancellationToken, AsyncRWLock, AsyncBlackboard, ProcessHandle
*   `core/hive_mind/saga_manager.py` - SagaManager avec Phase Guards + Context Snapshot
*   `core/fsm/health_state_machine.py` - HealthStateMachine avec Recovery Strategies
*   `core/fsm/stagnation_predictor.py` - Proactive stagnation prediction
*   `core/utils/serialization.py` - NexusJSONEncoder
*   `core/agents/unified_registry.py` - Centralized agent metadata
*   `core/drivers/async_claude_driver.py` - TRUE async driver
*   `core/drivers/async_gemini_driver.py` - TRUE async driver avec session isolation

### Priorité haute (V8.3.x - vérifier cohérence avec V8.4):
*   `core/hive_mind/swarm_bridge.py` - SwarmBridge V8.3.0
*   `core/execution/tool_manager.py` - SwarmTool V8.3.1
*   `core/hive_mind/phases/phase_execution.py` - Swarm delegation
*   `core/hive_mind/success_adapter.py` - SuccessMemory feedback
*   `core/swarm/merge_strategies.py` - MergeStrategy V8.3.3
*   `core/swarm/mode_executors.py` - 6 mode executors

### Priorité moyenne (V8.1.x - V8.2.x):
*   `core/evolution/phases/brainstorm.py` - mode="prompt" V8.1.8
*   `core/bootstrap/agent_loader.py` - InferenceConfig V8.1.8-B
*   `core/interface/repl.py` - Cyborg V7.5 (run_async, process_turn_async)
*   `core/orchestration/fsm_handlers.py` - Async handlers (handle_*_async)

### Infrastructure stable (vérifier cohérence):
*   `core/hive_mind/context_manager.py` - Nouveaux budgets
*   `core/hive_mind/types.py` - ExecutionStep.swarm_mode + 24 HiveMindState
*   `core/synapse/protocol_v7.py` - LightMessageV7, HeavyMessageV7
*   `core/utils/atomic_store.py` - AtomicJsonStore (Write-Replace pattern)
*   `core/fsm/states.py` - OrchestratorState enum + TRANSITION_MATRIX

### Modules annexes (documentation light):
*   `core/telemetry/` - Performance metrics
*   `core/mcp/` - MCP client
*   `core/routing/` - ModelRouter
*   `core/ui/` - ConsoleV7
*   `core/reasoning/` - CoT enforcement
*   `core/notifications/` - User notifications
</deliverables>

<version_history>
| Version | Date | Changements |
|---------|------|-------------|
| V8.3.x | 2025-12-03 | Initial prompt (SwarmBridge, Depth Guard) |
| V8.4.4 | 2025-12-10 | +Async Primitives, +SagaManager, +HealthFSM, +StagnationPredictor, +NexusJSONEncoder, +UnifiedAgentRegistry, +Async Handlers, +Cyborg V7.5, audit categories updated |
</version_history>
</prompt>
