# Étude d'Impact V8.3.1 - SwarmTool

**Date**: 2025-12-09
**Version Cible**: V8.3.1
**Auteur**: Claude Code (Opus 4.5)
**Prérequis**: V8.3.0 SwarmBridge (✅ Complété)

---

## Résumé Exécutif

### Proposition
Transformer le Swarm Engine en **outil invocable** par les agents à n'importe quelle phase du HiveMind, pas seulement en Phase 4 (Execution).

### Problème Actuel (V8.3.0)
- SwarmBridge ne fonctionne qu'en Phase 4 via `ExecutionStep.swarm_mode`
- Les autres phases (Analysis, Debate, Architecture) ne peuvent pas bénéficier du Swarm
- Perte d'opportunités: debates RED_BLUE, analyses PARALLEL, etc.

### Solution Proposée (V8.3.1)
Créer un outil `swarm_delegate` dans `ToolManager` permettant:
```
Agent: "Pour ce débat complexe, je délègue au Swarm en mode RED_BLUE"
<tool_use name="swarm_delegate">
  {"task": "Débattre de l'approche auth", "mode": "red_blue"}
</tool_use>
```

---

## Architecture Proposée

```
┌──────────────────────────────────────────────────────────────────┐
│                    HIVE MIND PHASES                               │
├──────────────────────────────────────────────────────────────────┤
│  Phase 1: ANALYSIS ────┐                                         │
│  Phase 2: DEBATE ──────┼──→ Agent peut invoquer swarm_delegate   │
│  Phase 3: ARCHITECTURE─┘    à n'importe quel moment              │
│  Phase 4: EXECUTION ───────→ (déjà supporté via ExecutionStep)   │
│  Phase 5: DIAGNOSIS ───┐                                         │
│  Phase 6: CONSOLIDATION┘                                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      TOOL MANAGER                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  tools = {                                                   │ │
│  │    "bash": _execute_bash,                                    │ │
│  │    "read": _execute_read,                                    │ │
│  │    ...                                                       │ │
│  │    "swarm_delegate": _execute_swarm_delegate,  # NEW V8.3.1  │ │
│  │  }                                                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SWARM BRIDGE                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  delegate(task, mode, phase, context_categories)            │ │
│  │     → Mode validation (guardrails)                          │ │
│  │     → Context extraction (8k tokens budget)                 │ │
│  │     → execute_with_fallback()  ← SELF-HEALING               │ │
│  │     → Result injection back to HiveMind                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   SWARM ENGINE (6 modes)                          │
│  PARALLEL │ SEQUENTIAL │ LEAD_SUPPORT │ PING_PONG │ RED_BLUE    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Analyse des Points Critiques

### 1. CONTEXTE - Token Management

#### État Actuel
```python
# core/hive_mind/context_manager.py
OPERATION_BUDGETS = {
    "analysis": 10000,
    "debate": 8000,
    "architecture": 6000,
    "execution": 5000,
    "diagnosis": 12000,
    "consolidation": 15000,
    "swarm_delegation": 8000,  # V8.3.0
}
```

#### Problème Potentiel
Quand SwarmTool est invoqué pendant une phase (ex: DEBATE), deux budgets entrent en compétition:
- Budget de la phase courante (debate: 8k)
- Budget swarm_delegation (8k)

#### Solution V8.3.1
```python
# Nouveau budget dédié pour SwarmTool (indépendant de swarm_delegation)
OPERATION_BUDGETS = {
    ...
    "swarm_delegation": 8000,      # Phase 4 via ExecutionStep
    "swarm_tool_invocation": 6000, # V8.3.1: Tool invocation depuis n'importe quelle phase
}
```

**Logique**:
- `swarm_delegation` (8k): Pour Phase 4 avec contexte complet d'exécution
- `swarm_tool_invocation` (6k): Pour invocations ponctuelles, contexte allégé

#### Extraction de Contexte
```python
def _execute_swarm_delegate(self, arguments: Dict) -> ToolResult:
    """Execute swarm_delegate tool."""
    # Extraire contexte minimal pour éviter dilution
    context = self.context_manager.get_context_for(
        operation="swarm_tool_invocation",
        include_categories=arguments.get("context_categories", ["task"]),
        exclude_categories=["chat_history", "debug_logs"]
    )
```

**Verdict**: ✅ GÉRABLE - Ajout d'un budget dédié + extraction ciblée

---

### 2. FEEDBACK LOOP - Injection des Résultats

#### État Actuel (SwarmBridge)
```python
# core/hive_mind/swarm_bridge.py:382-412
def inject_results_into_context(self, delegation_result: SwarmDelegationResult) -> bool:
    self.context.add_entry(
        category="swarm_results",
        content=delegation_result.summary,
        priority="HIGH"
    )
```

#### Problème
Le feedback loop existe mais n'est pas automatiquement appelé après un tool call.
Le pattern Tool → ToolResult ne garantit pas l'injection dans le contexte HiveMind.

#### Solution V8.3.1
```python
def _execute_swarm_delegate(self, arguments: Dict) -> ToolResult:
    # 1. Délégation au Swarm
    result = await self.swarm_bridge.delegate(...)

    # 2. FEEDBACK LOOP AUTOMATIQUE
    if result.success:
        self.swarm_bridge.inject_results_into_context(result)

    # 3. Retourner ToolResult pour le CFL
    return ToolResult(
        status="SUCCESS" if result.success else "ERROR",
        output=result.summary,
        metadata={
            "mode_used": result.mode_used.value,
            "fallback_chain": [m.value for m in result.fallback_chain],
            "execution_time": result.execution_time
        }
    )
```

**Flux Complet**:
```
Agent invoque swarm_delegate
    │
    ▼
ToolManager._execute_swarm_delegate()
    │
    ├──→ SwarmBridge.delegate()
    │       │
    │       ▼
    │    SwarmEngine.execute_swarm_mode()
    │       │
    │       ▼
    │    SwarmDelegationResult
    │
    ├──→ SwarmBridge.inject_results_into_context()  ← FEEDBACK
    │       │
    │       ▼
    │    HiveMindContextManager.add_entry(category="swarm_results")
    │
    ▼
ToolResult → FSM → VALIDATING_CFL → Agent reçoit résultat
```

**Verdict**: ✅ GÉRABLE - Feedback automatique intégré dans le handler du tool

---

### 3. SELF-HEALING - Connexion au Système d'Auto-Réparation

#### État Actuel du Self-Healing

**Fichier**: `core/swarm/mode_executors.py:346-463`
```python
async def execute_with_fallback(
    self,
    context: ExecutionContext,
    max_fallbacks: int = 2
) -> SwarmResult:
    """
    Execute with automatic fallback on failure.

    Fallback chain:
    - PARALLEL → SEQUENTIAL → SPECIALIST
    - RED_BLUE → LEAD_SUPPORT → SPECIALIST
    """
    current_mode = context.mode
    attempts = 0

    while current_mode is not None and attempts <= max_fallbacks:
        # 1. Create checkpoint before execution
        checkpoint = self.session_manager.create_checkpoint()

        try:
            result = await self._execute_mode(context, current_mode)

            if self._is_success(result):
                return result

            # Result not successful, prepare fallback
            self.session_manager.restore_checkpoint(checkpoint)

        except Exception as e:
            self.session_manager.restore_checkpoint(checkpoint)

        # Get fallback mode
        current_mode = current_mode.fallback_mode
        attempts += 1
```

**Fichier**: `core/swarm/collaboration_modes.py:85-102`
```python
@property
def fallback_mode(self) -> Optional["CollaborationMode"]:
    fallback_map = {
        CollaborationMode.PARALLEL: CollaborationMode.SEQUENTIAL,
        CollaborationMode.SEQUENTIAL: CollaborationMode.SPECIALIST,
        CollaborationMode.LEAD_SUPPORT: CollaborationMode.SPECIALIST,
        CollaborationMode.PING_PONG: CollaborationMode.LEAD_SUPPORT,
        CollaborationMode.RED_BLUE: CollaborationMode.LEAD_SUPPORT,
        CollaborationMode.SPECIALIST: None,  # Terminal - no fallback
    }
    return fallback_map.get(self)
```

#### Analyse de Connexion

**Question**: Le self-healing est-il branché dans SwarmBridge?

**Réponse**: ✅ **OUI, partiellement**

Dans `swarm_bridge.py:213-264`:
```python
async def _execute_with_fallback(
    self,
    task: str,
    mode: CollaborationMode,
    blackboard: Dict,
    config: Dict,
    fallback_chain: List[CollaborationMode],
    max_fallbacks: int = 2
) -> Any:
    """Execute Swarm mode with fallback chain."""
    current_mode = mode
    attempts = 0

    while current_mode is not None and attempts <= max_fallbacks:
        fallback_chain.append(current_mode)

        try:
            result = await self._call_swarm(task, current_mode, blackboard, config)

            if self._is_success(result):
                return result

        except Exception as e:
            logger.warning(f"SwarmBridge: Mode {current_mode.value} failed, trying fallback")

        current_mode = current_mode.fallback_mode
        attempts += 1
```

**Gap Identifié**:
- SwarmBridge a sa propre implémentation de fallback
- Mais ne crée PAS de checkpoints (contrairement à mode_executors.py)
- Pas de stagnation detection

#### Solution V8.3.1 - Alignement Self-Healing

```python
# Option A: Utiliser directement mode_executors
async def _call_swarm(self, task, mode, blackboard, config):
    if hasattr(self.swarm, 'execute_with_fallback'):
        # Utilise le self-healing complet du SwarmEngine
        return await self.swarm.execute_with_fallback(
            ExecutionContext(task=task, mode=mode, blackboard=blackboard),
            max_fallbacks=config.get('max_fallbacks', 2)
        )
    # Fallback si méthode non disponible
    return await self.swarm.execute_swarm_mode(task=task, mode=mode, ...)

# Option B: Intégrer checkpoints dans SwarmBridge
async def _execute_with_fallback(self, ...):
    while current_mode is not None and attempts <= max_fallbacks:
        # V8.3.1: Créer checkpoint
        checkpoint = None
        if hasattr(self.swarm, 'session_manager'):
            checkpoint = self.swarm.session_manager.create_checkpoint()

        try:
            result = await self._call_swarm(...)
            if self._is_success(result):
                return result
        except Exception:
            # V8.3.1: Restaurer checkpoint
            if checkpoint:
                self.swarm.session_manager.restore_checkpoint(checkpoint)

        current_mode = current_mode.fallback_mode
```

**Recommandation**: Option A (délégation au SwarmEngine) pour éviter duplication

**Verdict**: ⚠️ PARTIELLEMENT BRANCHÉ - Fallback fonctionne mais manque checkpoints

---

### 4. GUARDRAILS - Validation des Modes par Phase

#### État Actuel (SwarmBridge)
```python
ALLOWED_MODES = {
    HivePhase.ANALYSIS: [CollaborationMode.SPECIALIST],
    HivePhase.DEBATE: [CollaborationMode.PING_PONG, CollaborationMode.RED_BLUE],
    HivePhase.ARCHITECTURE: [CollaborationMode.LEAD_SUPPORT],
    HivePhase.EXECUTION: [CollaborationMode.PARALLEL, CollaborationMode.SEQUENTIAL, CollaborationMode.SPECIALIST],
    HivePhase.DIAGNOSIS: [CollaborationMode.RED_BLUE],
    HivePhase.CONSOLIDATION: [CollaborationMode.SPECIALIST],
}
```

#### Problème pour SwarmTool
Quand un agent invoque `swarm_delegate` via tool call, comment détermine-t-on la phase courante?

#### Solution V8.3.1
```python
def _execute_swarm_delegate(self, arguments: Dict) -> ToolResult:
    task = arguments["task"]
    mode = CollaborationMode.from_string(arguments["mode"])

    # Option 1: Phase explicite dans les arguments
    phase_str = arguments.get("phase")
    if phase_str:
        phase = HivePhase(phase_str)
    else:
        # Option 2: Inférer depuis l'état FSM courant
        phase = self._infer_phase_from_fsm_state()

    # Validation guardrails
    result = await self.swarm_bridge.delegate(
        task=task,
        mode=mode,
        phase=phase  # Validation automatique
    )
```

**Verdict**: ✅ GÉRABLE - Phase explicite ou inférée

---

### 5. TOOL REGISTRATION - Intégration dans ToolManager

#### État Actuel
```python
# core/execution/tool_manager.py
class ToolManager:
    def __init__(self, ...):
        self.tools = {
            "bash": self._execute_bash,
            "read": self._execute_read,
            "write": self._execute_write,
            # ... 14 tools
            "create_tool": self._execute_create_tool,
        }
```

#### Solution V8.3.1
```python
# Modification de ToolManager.__init__
def __init__(
    self,
    workspace_path: Path,
    context_manager: HiveMindContextManager = None,
    swarm_bridge: SwarmBridge = None,  # NEW V8.3.1
):
    self.swarm_bridge = swarm_bridge
    self.tools = {
        ...
        "swarm_delegate": self._execute_swarm_delegate,  # NEW V8.3.1
    }

async def _execute_swarm_delegate(self, arguments: Dict) -> ToolResult:
    """
    V8.3.1 SwarmTool - Delegate subtask to Swarm Engine.

    Arguments:
        task: str - The subtask to delegate
        mode: str - Collaboration mode (parallel, red_blue, etc.)
        phase: str (optional) - Current HiveMind phase for validation
        context_categories: List[str] (optional) - Which context to include

    Returns:
        ToolResult with Swarm execution output
    """
    if self.swarm_bridge is None:
        return ToolResult(
            status="ERROR",
            error="SwarmBridge not configured. Cannot delegate."
        )

    task = arguments.get("task")
    mode_str = arguments.get("mode", "specialist")
    phase_str = arguments.get("phase")

    if not task:
        return ToolResult(status="ERROR", error="Missing 'task' argument")

    try:
        mode = CollaborationMode.from_string(mode_str)
    except ValueError:
        return ToolResult(
            status="ERROR",
            error=f"Invalid mode: {mode_str}. Valid: parallel, sequential, lead_support, ping_pong, specialist, red_blue"
        )

    phase = HivePhase(phase_str) if phase_str else None

    # Execute delegation
    result = await self.swarm_bridge.delegate(
        task=task,
        mode=mode,
        phase=phase,
        context_categories=arguments.get("context_categories")
    )

    # Feedback loop: inject results
    if result.success:
        self.swarm_bridge.inject_results_into_context(result)

    return ToolResult(
        status="SUCCESS" if result.success else "ERROR",
        output=result.summary,
        error="; ".join(result.failure_diagnostics) if not result.success else None,
        metadata={
            "mode_used": result.mode_used.value,
            "fallback_chain": [m.value for m in result.fallback_chain],
            "execution_time": result.execution_time
        }
    )
```

**Verdict**: ✅ FAISABLE - Pattern standard ToolManager

---

## Cas d'Usage par Phase

| Phase | Mode Suggéré | Cas d'Usage |
|-------|--------------|-------------|
| ANALYSIS | SPECIALIST | Analyser un fichier complexe avec expertise |
| DEBATE | RED_BLUE | Débat adversarial sur une approche |
| DEBATE | PING_PONG | Raffinement itératif d'une proposition |
| ARCHITECTURE | LEAD_SUPPORT | Architecte principal + reviewer |
| EXECUTION | PARALLEL | Tests parallèles, recherches multiples |
| EXECUTION | SEQUENTIAL | Pipeline d'opérations dépendantes |
| DIAGNOSIS | RED_BLUE | Analyse contradictoire d'une erreur |
| CONSOLIDATION | SPECIALIST | Synthèse par expert |

---

## Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Explosion combinatoire** | Moyenne | Haute | Guardrails stricts (9 combinaisons valides) |
| **Token overflow** | Moyenne | Moyenne | Budget dédié 6k tokens |
| **Circular delegation** | Faible | Haute | Compteur de profondeur max |
| **Self-healing partiel** | Haute | Moyenne | Déléguer à `execute_with_fallback()` |
| **Import circulaire** | Moyenne | Moyenne | Import lazy dans ToolManager |
| **FSM race condition** | Faible | Moyenne | Lock sur tool execution |

---

## Plan d'Implémentation V8.3.1

| # | Tâche | Fichier | Effort |
|---|-------|---------|--------|
| 1 | Ajouter budget swarm_tool_invocation | `context_manager.py` | 10min |
| 2 | Ajouter swarm_delegate handler | `tool_manager.py` | 1h |
| 3 | Câbler SwarmBridge dans ToolManager | `orchestration_v7.py` | 30min |
| 4 | Aligner self-healing (checkpoints) | `swarm_bridge.py` | 30min |
| 5 | Tests SwarmTool | `test_swarm_tool.py` | 1h |
| 6 | Documentation | `ROADMAP.md`, `SESSION_CONTINUITY.md` | 20min |

**Effort Total**: ~3h30

---

## Conclusion

### Faisabilité: ✅ VIABLE

**Points Positifs**:
1. **Contexte**: Budget dédié évite la dilution (6k tokens)
2. **Feedback Loop**: Injection automatique dans le handler
3. **Guardrails**: Validation des modes par phase existante
4. **Tool Pattern**: Intégration standard dans ToolManager

**Points d'Attention**:
1. **Self-Healing**: Partiellement branché - nécessite alignement avec checkpoints
2. **Profondeur**: Ajouter limite pour éviter récursion infinie

### Recommandation

**Procéder avec V8.3.1** en suivant le plan d'implémentation ci-dessus, avec priorité sur l'alignement self-healing (étape 4).

---

*Document généré par Claude Code (Opus 4.5) - 2025-12-09*
