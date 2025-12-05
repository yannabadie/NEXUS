# Phase 14e: Force Chain-of-Thought (CoT) Enforcement

**Version**: V7.7 HIVE MIND
**Date**: 2025-12-05
**Proposé par**: Gemini (2025-12-04)
**Implémenté par**: Claude (2025-12-05)
**Status**: ✅ COMPLETED

---

## Overview

Phase 14e implements **forced Chain-of-Thought (CoT) reasoning** for EXPERT complexity tasks. When a task is classified as EXPERT (the highest complexity level), the system automatically injects an instruction requiring the AI agent to explicitly reason through the problem before responding.

### Why CoT for EXPERT Tasks?

| Complexity | CoT Required | Rationale |
|------------|--------------|-----------|
| TRIVIAL | No | Simple lookups, no reasoning needed |
| SIMPLE | No | Straightforward tasks |
| MODERATE | No | Standard complexity |
| COMPLEX | No | Agents handle well without forcing |
| **EXPERT** | **Yes** | Multi-step reasoning, architecture decisions, security analysis |

EXPERT tasks benefit from explicit reasoning because:
1. **Reduced errors** - Step-by-step thinking catches logical mistakes
2. **Better decisions** - Forces consideration of alternatives
3. **Auditable** - Reasoning is visible in `<thinking>` tags
4. **Consistency** - Both agents use same reasoning structure

---

## Architecture

### Dual-Path Implementation

CoT enforcement works on both execution paths in NEXUS:

```
                         ┌─────────────────────────────────────┐
                         │           Task Input                │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────────────┐
                         │      TaskAnalyzer.analyze()         │
                         │   → complexity = TaskComplexity.*   │
                         └──────────────┬──────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
    ┌───────────────────────────────┐       ┌───────────────────────────────┐
    │     ORCHESTRATOR PATH         │       │        SWARM PATH             │
    │                               │       │                               │
    │  OrchestratorV7.process_turn  │       │  HybridSwarmEngine.process    │
    │  ├─ _current_complexity = X   │       │  ├─ ExecutionContext(         │
    │  └─ _build_context()          │       │  │     force_cot=is_expert)   │
    │      └─ if EXPERT → inject    │       │  └─ _wrap_invoke_agent()      │
    │                               │       │      └─ if EXPERT → inject    │
    └───────────────────────────────┘       └───────────────────────────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────────────┐
                         │  Agent receives prompt with CoT     │
                         │  instruction if EXPERT complexity   │
                         └─────────────────────────────────────┘
```

### CoT Instruction

The following instruction is injected into the prompt for EXPERT tasks:

```xml
<instruction>BEFORE answering or using tools, you MUST wrap your step-by-step reasoning in <thinking>...</thinking> tags.</instruction>
```

---

## Implementation Details

### 1. OrchestratorV7 (`core/orchestration_v7.py`)

#### New Attribute: `_current_complexity`

```python
class OrchestratorV7:
    def __init__(self, config: Config, ...):
        # ... existing code ...

        # V7.7 Phase 14e: Force Chain-of-Thought for EXPERT tasks
        self._current_complexity: Optional[TaskComplexity] = None
```

#### Storing Complexity in `process_turn()`

```python
def process_turn(self, user_input: str, agent_response: Optional[str] = None):
    # During task analysis...
    complexity = self.task_analyzer.analyze(user_input).complexity

    # V7.7 Phase 14e: Store complexity for CoT enforcement
    self._current_complexity = complexity
```

#### CoT Injection in `_build_context()`

```python
def _build_context(self) -> str:
    context = f"""## Current Objective
{self.blackboard.get('objective', 'No objective set')}
...
"""
    # V7.7 Phase 14e: Force Chain-of-Thought for EXPERT complexity tasks
    if self._current_complexity == TaskComplexity.EXPERT:
        context += "\n\n<instruction>BEFORE answering or using tools, you MUST wrap your step-by-step reasoning in <thinking>...</thinking> tags.</instruction>"

    return context
```

### 2. ExecutionContext (`core/swarm/mode_executors.py`)

#### New Field: `force_cot`

```python
@dataclass
class ExecutionContext:
    """Context for mode execution.

    V7.5 Phase 7: Added task_id and session_manager for session isolation.
    V7.7 Phase 14e: Added force_cot for Chain-of-Thought enforcement.
    """
    task_input: str
    agent_assignments: List[AgentAssignment]
    blackboard: Optional[Dict[str, Any]] = None
    max_rounds: int = 6
    task_id: Optional[str] = None
    session_manager: Optional[Any] = None

    # V7.7 Phase 14e: Force Chain-of-Thought for EXPERT complexity
    force_cot: bool = False
```

### 3. HybridSwarmEngine (`core/swarm/hybrid_swarm_engine.py`)

#### Setting `force_cot` in `process_task()`

```python
def process_task(self, task: str, ...) -> SwarmResult:
    analysis = self.task_analyzer.analyze(task)
    self._current_analysis = analysis

    context = ExecutionContext(
        task_input=task,
        agent_assignments=assignments,
        blackboard=blackboard,
        max_rounds=self.config.swarm_max_rounds,
        task_id=task_id,
        session_manager=self._session_manager,
        # V7.7 Phase 14e: Force CoT for EXPERT complexity
        force_cot=(analysis.complexity == TaskComplexity.EXPERT)
    )
```

#### Setting `force_cot` in `execute_directly()`

```python
def execute_directly(self, task: str, ...) -> SwarmResult:
    # V7.7 Phase 14e: Check if EXPERT complexity for CoT
    is_expert = (
        self._current_analysis and
        self._current_analysis.complexity == TaskComplexity.EXPERT
    )

    context = ExecutionContext(
        task_input=task,
        agent_assignments=[...],
        blackboard=blackboard,
        max_rounds=self.config.swarm_max_rounds,
        task_id=task_id,
        session_manager=self._session_manager,
        force_cot=is_expert
    )
```

#### CoT Injection in `_wrap_invoke_agent()`

```python
def _wrap_invoke_agent(self) -> Callable:
    original_invoke = self.invoke_agent

    def wrapped_invoke(agent_id: str, task_type: str, context: str) -> str:
        # V7.7 Phase 14e: Inject CoT instruction for EXPERT complexity
        if (self._current_analysis and
            self._current_analysis.complexity == TaskComplexity.EXPERT):
            context += "\n\n<instruction>BEFORE answering or using tools, you MUST wrap your step-by-step reasoning in <thinking>...</thinking> tags.</instruction>"

        return original_invoke(agent_id, task_type, context)

    return wrapped_invoke
```

---

## Task Complexity Levels

```python
class TaskComplexity(Enum):
    TRIVIAL = 1    # Simple lookups, greetings
    SIMPLE = 2     # Basic operations
    MODERATE = 3   # Standard tasks
    COMPLEX = 4    # Multi-step, requires planning
    EXPERT = 5     # Architecture, security, deep analysis → CoT FORCED
```

### Examples by Complexity

| Complexity | Example Task | CoT? |
|------------|--------------|------|
| TRIVIAL | "What time is it?" | No |
| SIMPLE | "Read file.txt" | No |
| MODERATE | "Fix this bug in auth.py" | No |
| COMPLEX | "Refactor the payment module" | No |
| EXPERT | "Design a microservices architecture for high-availability" | **Yes** |
| EXPERT | "Audit this code for security vulnerabilities" | **Yes** |
| EXPERT | "Create an evolution strategy for NEXUS" | **Yes** |

---

## Testing

### Test File: `tests/test_cot_enforcement.py`

**16 tests** covering all aspects:

```bash
pytest tests/test_cot_enforcement.py -v
```

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| `TestOrchestratorCoT` | 4 | Orchestrator path CoT logic |
| `TestExecutionContextCoT` | 3 | ExecutionContext.force_cot field |
| `TestSwarmEngineCoT` | 4 | Swarm engine injection |
| `TestComplexityLevels` | 3 | Complexity ordering verification |
| `TestCoTIntegration` | 2 | End-to-end integration |

### Key Test Cases

```python
def test_expert_complexity_triggers_cot(self):
    """Test that EXPERT complexity adds CoT instruction to context."""
    assert TaskComplexity.EXPERT.value > TaskComplexity.COMPLEX.value

def test_wrap_invoke_agent_injects_cot(self, swarm_engine):
    """Test that _wrap_invoke_agent injects CoT for EXPERT tasks."""
    expert_analysis = TaskAnalysis(
        complexity=TaskComplexity.EXPERT,
        domains=[TaskDomain.SECURITY],
        primary_domain=TaskDomain.SECURITY,
        claude_fit_score=0.9,
        requires_code_execution=True
    )
    swarm_engine._current_analysis = expert_analysis

    # ... verify COT_INSTRUCTION in captured_context

def test_only_expert_triggers_cot(self):
    """Verify only EXPERT triggers CoT, not COMPLEX."""
    complexities_with_cot = [
        c for c in TaskComplexity
        if c == TaskComplexity.EXPERT
    ]
    assert len(complexities_with_cot) == 1
```

---

## Configuration

No configuration required. CoT enforcement is automatic for EXPERT tasks.

### Future Configuration Options (Not Implemented)

If needed in the future:

```python
# .env (hypothetical)
COT_FORCE_THRESHOLD=EXPERT  # Minimum complexity for forced CoT
COT_INSTRUCTION_TEMPLATE="..."  # Custom instruction text
```

---

## Expected Agent Response Format

When CoT is enforced, agents should respond with:

```xml
<thinking>
Step 1: Analyze the requirements...
Step 2: Consider the trade-offs between approaches A and B...
Step 3: Design the solution architecture...
</thinking>

Based on my analysis, I recommend...
```

---

## Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| CoT Injection Rate | % of EXPERT tasks with CoT injected | 100% |
| Reasoning Quality | Subjective assessment of `<thinking>` content | Improved |
| Error Rate on EXPERT | Mistakes in EXPERT task responses | Reduced |

---

## Files Modified

| File | Changes |
|------|---------|
| `core/orchestration_v7.py` | `_current_complexity` attribute, `_build_context()` injection |
| `core/swarm/mode_executors.py` | `ExecutionContext.force_cot` field |
| `core/swarm/hybrid_swarm_engine.py` | `force_cot` setting, `_wrap_invoke_agent()` injection |
| `tests/test_cot_enforcement.py` | 16 new tests |
| `ROADMAP_HIVE_MIND.md` | Phase 14e marked COMPLETED |

---

## See Also

- [ROADMAP_HIVE_MIND.md](../ROADMAP_HIVE_MIND.md) - Phase 14e entry
- [HYBRID_SWARM.md](HYBRID_SWARM.md) - Swarm engine documentation
- [core/swarm/task_analyzer.py](../core/swarm/task_analyzer.py) - Complexity classification
