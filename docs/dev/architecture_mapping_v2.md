# MISSION: Map NEXUS V8.1 Architecture & Processes (V2 - ENRICHED)

## Context
NEXUS has evolved significantly (V8.1 "True Hive Mind"). We need a comprehensive visual map of all current processes, features, and data flows to update the documentation. The system includes a Hybrid Swarm Engine, FSM Orchestrator, Evolution Phases, Hive Mind 7-Phase Pipeline, Project Memory (RAG), and multi-provider LLM routing.

---

## Your Task
Analyze the codebase (focusing on `core/`) and generate a detailed **Mermaid.js flowchart** accompanied by a functional summary.

---

## 1. Scope of Analysis (EXHAUSTIVE)

You must cover ALL of these components:

### 1.1 Entry Points & Security
- **KERNEL.py** - Creator alignment check (immutable security layer)
- **nexus7.py** - Main entry point, bootstrap, CLI inspection
- **KERNEL_HASH.txt** - Integrity verification

### 1.2 Orchestration Core
- **FSM States** (`core/fsm/states.py`) - 11 Orchestrator states
- **Main Loop** (`orchestration_v7.py`) - Central state machine driver
- **FSM Handlers** (`core/orchestration/fsm_handlers.py`) - State transition handlers
- **Agent Invoker** (`core/orchestration/agent_invoker.py`) - Agent invocation with provider routing (V8.1.8-B)
- **Context Builder** (`core/orchestration/context_builder.py`) - Context construction
- **Swarm Bridge** (`core/orchestration/swarm_bridge.py`) - Integration to Swarm Engine
- **Stagnation Detector** (`core/fsm/stagnation_detector.py`) - Hot-Swap Lead detection

### 1.3 LLM Drivers (Multi-Provider)
- **Gemini Driver** (`core/drivers/gemini_driver_v7.py`) - Gemini CLI wrapper, persistent sessions
- **Claude Driver** (`core/drivers/claude_driver_hybrid.py`) - Claude API, hybrid XML/natural
- **Async Adapter** (`core/drivers/async_adapter.py`) - Async/sync bridge
- **Model Router** (`core/routing/model_router.py`) - Opus/Sonnet/Flash/Pro routing

### 1.4 Swarm Engine (6 Modes)
- **Hybrid Swarm Engine** (`core/swarm/hybrid_swarm_engine.py`) - Main orchestrator
- **Mode Selector** (`core/swarm/mode_selector.py`) - DyLAN-based selection with memory boost
- **Mode Executors** (`core/swarm/mode_executors.py`) - 6 mode implementations
- **Negotiation Protocol** (`core/swarm/negotiation_protocol.py`) - Agent negotiation
- **Task Analyzer** (`core/swarm/task_analyzer.py`) - Complexity analysis (TRIVIAL→EXPERT)
- **Agent Metrics** (`core/swarm/agent_metrics.py`) - DyLAN scoring
- **Session Manager** (`core/swarm/session_manager.py`) - Session isolation (V8.1.6)
- **Collaboration Modes** (`core/swarm/collaboration_modes.py`) - Mode definitions + fallback chain

### 1.5 Hive Mind Phases (7-Phase Pipeline, V8.0)
- **Orchestrator** (`core/hive_mind/orchestrator.py`) - TrueHiveMind coordinator
- **Types** (`core/hive_mind/types.py`) - 25+ dataclasses, 7 enums, 28 states
- **Phase 1: Analysis** (`phases/phase_analysis.py`) - Independent analysis
- **Phase 2: Debate** (`phases/phase_debate.py`) - Strategic debate
- **Phase 3: Architecture** (`phases/phase_architecture.py`) - Plan generation
- **Phase 4: Execution** (`phases/phase_execution.py`) - Monitored execution
- **Phase 5: Diagnosis** (`phases/phase_diagnosis.py`) - Failure analysis
- **Phase 6: Retry** (`phases/phase_retry.py`) - Adaptive retry
- **Phase 7: Consolidation** (`phases/phase_consolidation.py`) - Knowledge archiving
- **Agent Registry** (`core/hive_mind/agent_registry.py`) - Spawned agent registry
- **Strategy Blacklist** (`core/hive_mind/strategy_blacklist.py`) - Failed strategy tracking
- **Cost Estimator** (`core/hive_mind/cost_estimator.py`) - Token cost estimation
- **User Interaction** (`core/hive_mind/user_interaction.py`) - Breakpoint handling
- **Adaptive Debate** (`core/hive_mind/adaptive_debate.py`) - Debate turn calculation

### 1.6 Evolution System (5-Phase)
- **Evolution Manager** (`core/evolution/manager.py`) - Evolution orchestrator
- **Child Validator** (`core/evolution/validator.py`) - 5-tier validation
- **Tiered Validator** (`core/evolution/tiered_validator.py`) - syntax→smoke→benchmark→redteam→live
- **Child Evaluator** (`core/evolution/evaluator.py`) - Fitness evaluation
- **Lineage Tracker** (`core/evolution/lineage.py`) - Parent-child relationships
- **Mutation Parser** (`core/evolution/mutation_parser.py`) - Parse mutations
- **BrainstormPhase** (`phases/brainstorm.py`) - Mutation/prompt brainstorming
- **CreatePhase** (`phases/create.py`) - Child creation
- **PromotePhase** (`phases/promote.py`) - Child promotion

### 1.7 Bootstrap & Agent Loading
- **Auto Bootstrap** (`core/bootstrap/auto_bootstrap.py`) - NEXUS.md generation
- **Spawned Agent Loader** (`core/bootstrap/agent_loader.py`) - Load spawned agents
- **Agent Pool** (`core/swarm/agent_metrics.py`) - AgentProfile, DyLAN metrics
- **InferenceConfig** (V8.1.8-B) - Provider/model selection for spawned agents

### 1.8 Memory Systems
- **Project Memory (RAG)** (`core/memory/project_memory.py`) - Codebase indexing
- **Success Memory** (`core/memory/success_memory.py`) - Successful task patterns
- **Auto Memory** (`core/memory/auto_memory.py`) - Task-type patterns
- **Memory Backends** (`core/memory/backends/`) - Dense, TF-IDF, BM25
- **Legacy Memory V7** (`core/synapse/memory_v7.py`) - Token compression
- **Blackboard** (`workspace/.nexus/blackboard.json`) - Shared state

### 1.9 Tool Execution
- **Tool Manager** (`core/execution/tool_manager.py`) - 11 core tools
- **Agent Tools** (`core/execution/agent_tools.py`) - Agent-as-tool wrappers
- **Dynamic Tools** (`core/execution/dynamic_tools.py`) - Runtime tool creation

### 1.10 Security & Governance
- **Execution Policy** (`core/security/execution_policy.py`) - Command validation
- **Path Guardian** (`core/security/path_guardian.py`) - Path traversal protection
- **Integrity Monitor** (`core/security/integrity_monitor.py`) - File integrity
- **Mutation Validator** (`core/security/mutation_validator.py`) - Mutation safety
- **Sandbox Policy** (`core/governance/sandbox_policy.py`) - Sandbox rules
- **Red Team Validator** (`core/governance/red_team/validator.py`) - Alignment tests

### 1.11 Interfaces & Commands
- **REPL** (`core/interface/repl.py`) - 40+ slash commands
- **Commands** (`core/interface/commands.py`) - Command definitions, categories
- **Console V7** (`core/ui/console_v7.py`) - Console output

### 1.12 Telemetry & Budget
- **Budget Tracker** (`core/telemetry/budget_tracker.py`) - USD budget enforcement
- **Telemetry Exporter** (`core/telemetry/exporter.py`) - CSV export
- **Metrics** (`core/telemetry/metrics.py`) - Metric collection

### 1.13 MCP Integration
- **MCP Client** (`core/mcp/client.py`) - Model Context Protocol
- **MCP Protocol** (`core/mcp/protocol.py`) - Protocol dataclasses
- **MCP Registry** (`core/mcp/registry.py`) - Server registry

### 1.14 Configuration & Logging
- **Config** (`core/config.py`) - 50+ configuration parameters
- **Structured Logger** (`core/logging/logger_v7.py`) - JSON event logging

---

## 2. Deliverable Format

### Part A: The Mega-Map (Mermaid)

Generate a single, comprehensive Mermaid graph (`graph TD`) that connects ALL components.

**Required Subgraphs** (use these exact names):
```mermaid
subgraph SecurityLayer[🔐 Security Layer]
    KERNEL, PathGuardian, ExecutionPolicy, RedTeam
end

subgraph EntryPoints[🚪 Entry Points]
    nexus7.py, REPL, Commands
end

subgraph OrchestratorCore[🎯 Orchestrator Core]
    FSM_States, OrchestratorV7, FSMHandlers, AgentInvoker
end

subgraph LLMDrivers[🤖 LLM Drivers]
    GeminiDriver, ClaudeDriver, AsyncAdapter, ModelRouter
end

subgraph SwarmEngine[🐝 Swarm Engine]
    HybridSwarmEngine, ModeSelector, ModeExecutors, Negotiation
    Mode_PARALLEL, Mode_SEQUENTIAL, Mode_LEAD_SUPPORT
    Mode_PING_PONG, Mode_SPECIALIST, Mode_RED_BLUE
end

subgraph HiveMindPhases[🧠 Hive Mind (7 Phases)]
    Phase1_Analysis, Phase2_Debate, Phase3_Architecture
    Phase4_Execution, Phase5_Diagnosis, Phase6_Retry, Phase7_Consolidation
end

subgraph EvolutionSystem[🧬 Evolution System]
    EvolutionManager, BrainstormPhase, CreatePhase, PromotePhase
    TieredValidator, Lineage
end

subgraph MemoryLayer[💾 Memory Layer]
    ProjectMemory_RAG, SuccessMemory, AutoMemory, Blackboard
end

subgraph ToolExecution[🔧 Tool Execution]
    ToolManager, AgentTools, DynamicTools
end

subgraph TelemetryBudget[📊 Telemetry & Budget]
    BudgetTracker, TelemetryExporter, Metrics
end
```

**Required Flows to Show**:
1. User Input → REPL → Orchestrator → (Swarm or HiveMind) → LLM Drivers
2. Security Check: KERNEL → every action
3. Model Routing: TaskType → ModelRouter → Driver selection
4. Swarm Flow: TaskAnalyzer → ModeSelector → Negotiation → ModeExecutor
5. HiveMind Flow: Phase 1 → 2 → 3 → 4 → (5 → 6 if fail) → 7
6. Memory Flow: SuccessMemory ↔ ModeSelector (memory boost)
7. Evolution Flow: /spawn → BrainstormPhase → AgentLoader → AgentPool
8. Budget Flow: BudgetTracker → enforce_budget() → all invocations

**Decision Points to Highlight**:
- `Is Task Complex?` → Route to Swarm vs Direct
- `Complexity >= MODERATE?` → Route to HiveMind vs Swarm
- `Agreement Score > 0.85?` → Skip Debate
- `Execution Failed?` → Diagnosis → Retry or Escalate
- `Provider = Gemini?` → GeminiDriver vs ClaudeDriver (V8.1.8-B)

### Part B: Functional Inventory

Provide a structured list of features currently *implemented*:

#### B.1 Core Capabilities
List ALL major capabilities with their source files:
```markdown
| Capability | Description | Source File(s) |
|------------|-------------|----------------|
| Dynamic Agent Spawning | Brainstorm specialized agents | repl.py, brainstorm.py |
| ... | ... | ... |
```

#### B.2 All Slash Commands
List ALL 40+ commands organized by category (from commands.py):
```markdown
### 🐝 Collaboration (Swarm)
- `/swarm <task>` - Route through Hybrid Swarm
...
```

#### B.3 FSM States Inventory
List ALL 39 states (11 Orchestrator + 28 HiveMind):
```markdown
### Orchestrator States
1. IDLE - Waiting for input
...

### HiveMind States
1. HIVE_ANALYZING_GEMINI - Phase 1
...
```

#### B.4 Data Structures Inventory
List key dataclasses with their fields:
```markdown
| Dataclass | Fields | File |
|-----------|--------|------|
| TaskAnalysis | complexity, domains, recommended_mode | task_analyzer.py |
...
```

#### B.5 File-to-Feature Map
Map major features to their source files:
```markdown
| Feature | Primary File | LOC |
|---------|-------------|-----|
| Main Orchestrator | orchestration_v7.py | 783 |
...
```

---

## 3. Execution Strategy (DETAILED)

Execute in this exact order:

### Step 1: Security & Entry (5 files)
```bash
# Scan entry points
read KERNEL.py  # Creator alignment
read nexus7.py  # Main entry
read core/config.py  # Configuration
```

### Step 2: Orchestration Core (5 files)
```bash
read core/orchestration_v7.py  # Main FSM
read core/fsm/states.py  # State enum
read core/orchestration/fsm_handlers.py  # Handlers
read core/orchestration/agent_invoker.py  # Invocation + V8.1.8-B routing
read core/orchestration/context_builder.py  # Context
```

### Step 3: LLM Drivers (4 files)
```bash
read core/drivers/gemini_driver_v7.py
read core/drivers/claude_driver_hybrid.py
read core/drivers/async_adapter.py
read core/routing/model_router.py
```

### Step 4: Swarm Engine (9 files)
```bash
read core/swarm/hybrid_swarm_engine.py
read core/swarm/mode_selector.py
read core/swarm/mode_executors.py
read core/swarm/collaboration_modes.py
read core/swarm/negotiation_protocol.py
read core/swarm/task_analyzer.py
read core/swarm/agent_metrics.py
read core/swarm/session_manager.py
```

### Step 5: Hive Mind (10 files)
```bash
read core/hive_mind/orchestrator.py
read core/hive_mind/types.py
read core/hive_mind/phases/phase_analysis.py
read core/hive_mind/phases/phase_debate.py
read core/hive_mind/phases/phase_architecture.py
read core/hive_mind/phases/phase_execution.py
read core/hive_mind/phases/phase_diagnosis.py
read core/hive_mind/phases/phase_retry.py
read core/hive_mind/phases/phase_consolidation.py
```

### Step 6: Evolution (6 files)
```bash
read core/evolution/manager.py
read core/evolution/validator.py
read core/evolution/phases/brainstorm.py
read core/evolution/phases/create.py
read core/evolution/phases/promote.py
```

### Step 7: Memory (5 files)
```bash
read core/memory/project_memory.py
read core/memory/success_memory.py
read core/memory/auto_memory.py
```

### Step 8: Interface & Commands (3 files)
```bash
read core/interface/repl.py
read core/interface/commands.py
grep "def handle_" core/interface/repl.py  # Find all handlers
```

### Step 9: Security (4 files)
```bash
read core/security/execution_policy.py
read core/governance/sandbox_policy.py
read core/governance/red_team/validator.py
```

### Step 10: Synthesize
- Connect all components with data flows
- Identify missing links
- Generate Mermaid + Inventory

---

## 4. Quality Criteria

Your output will be evaluated on:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Completeness | 30% | All 14 subsystems covered |
| Accuracy | 25% | No hallucinated components |
| Data Flows | 20% | Clear arrows showing message flow |
| Decision Points | 15% | Key branching logic highlighted |
| Readability | 10% | Mermaid renders correctly |

---

## 5. Anti-Hallucination Rules

**MUST verify against codebase**:
- Only include classes/functions that EXIST in files
- Only include commands defined in `commands.py`
- Only include states defined in `states.py` and `types.py`
- Cross-reference CODEBASE_SNAPSHOT.md if unsure

**Common mistakes to avoid**:
- `TaskAnalysis.reasoning` → Does NOT exist (use `ModeProposal.reasoning`)
- `HiveMindState.HIVE_COMPLETE` → Use `HIVE_SUCCESS`
- `invoke(task_type=)` → Use `invoke(session_uuid=)`

---

## Expected Output

A markdown document (~2000-3000 lines) containing:
1. **Mermaid Mega-Map** (200+ nodes, 10+ subgraphs)
2. **Functional Inventory** (tables for all categories)
3. **Statistics Summary** (LOC, files, states, commands)

---

## Source
- **Original prompt**: User request for architecture mapping
- **Enriched by**: Claude (2025-12-09)
- **Based on**: NEXUS V8.1 codebase analysis
- **Reference**: CODEBASE_SNAPSHOT.md, docs/ARCHITECTURE_DECISIONS.md
