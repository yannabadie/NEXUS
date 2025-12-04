# Reasoning Module - NEXUS V7.6 "HIVE MIND"

Advanced reasoning structures (Graph of Thought).

## Status: DORMANT DNA

The Graph of Thought (GoT) implementation is **designed but not yet created**. The module infrastructure exists for future activation.

## Role in Architecture

The Reasoning module is intended to provide **structured problem decomposition**:
- Break complex problems into a Directed Acyclic Graph (DAG)
- Solve sub-problems in parallel
- Synthesize results from multiple thought branches

## Why Dormant?

With the introduction of **Hybrid Swarm Engine**, dynamic agent negotiation effectively handles problem decomposition during the `SWARM_NEGOTIATING` phase. The explicit GoT structure is reserved for:
- EXPERT-level tasks requiring formal decomposition
- Multi-step reasoning chains beyond Swarm's capabilities
- Future "Deep Thinking" modes

## Files

| File | Purpose | Status |
|------|---------|--------|
| `__init__.py` | Lazy loading infrastructure | ✅ EXISTS |
| `graph_of_thought.py` | DAG implementation | ⏳ PLANNED (not created) |

## Module Structure (\_\_init\_\_.py)

The `__init__.py` includes lazy loading for future GoT classes:

```python
# Lazy loading pattern
GOT_AVAILABLE = False

def _load_got():
    global GOT_AVAILABLE
    try:
        from .graph_of_thought import GraphOfThought, ThoughtNode, ThoughtGraph
        GOT_AVAILABLE = True
        return GraphOfThought, ThoughtNode, ThoughtGraph
    except ImportError:
        return None, None, None
```

## Planned Classes

When `graph_of_thought.py` is implemented:

### ThoughtNode

```python
@dataclass
class ThoughtNode:
    id: str
    content: str
    dependencies: List[str]  # IDs of parent nodes
    result: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
```

### ThoughtGraph

```python
class ThoughtGraph:
    def __init__(self):
        self.nodes: Dict[str, ThoughtNode] = {}
        self.root: Optional[str] = None

    def add_node(self, node: ThoughtNode) -> None:
        pass

    def get_ready_nodes(self) -> List[ThoughtNode]:
        """Get nodes with all dependencies satisfied"""
        pass

    def topological_sort(self) -> List[str]:
        """Execution order respecting dependencies"""
        pass
```

### GraphOfThought

```python
class GraphOfThought:
    def decompose(self, problem: str) -> ThoughtGraph:
        """Break problem into sub-problems as DAG"""
        pass

    def execute(self, graph: ThoughtGraph, executor: Callable) -> str:
        """Execute graph with parallel sub-problem solving"""
        pass

    def synthesize(self, graph: ThoughtGraph) -> str:
        """Combine results from all nodes"""
        pass
```

## Integration with Swarm (Planned)

The GoT module is referenced in `hybrid_swarm_engine.py:605-786` as dormant code:

```python
# hybrid_swarm_engine.py (dormant)
_GOT_AVAILABLE = False

def should_use_got(self, analysis: TaskAnalysis) -> bool:
    """Determine if GoT decomposition would benefit task"""
    return (
        _GOT_AVAILABLE and
        analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT] and
        len(analysis.sub_tasks or []) > 2
    )

def decompose_with_got(self, task: str) -> ThoughtGraph:
    """Use GoT to decompose complex task"""
    pass
```

## Activation Path

To activate Graph of Thought:

1. **Create** `core/reasoning/graph_of_thought.py` with ThoughtNode, ThoughtGraph, GraphOfThought
2. **Set** `GOT_AVAILABLE = True` in `__init__.py`
3. **Set** `SWARM_GOT_ENABLED=True` in config
4. **Connect** to `hybrid_swarm_engine.py:decompose_with_got()`

## Audit Notes

### [DORMANT_DNA]
- **Location**: `core/reasoning/`
- **Status**: Infrastructure exists, implementation pending
- **Lines of dormant code**: ~180 lines in `hybrid_swarm_engine.py` referencing GoT
- **Activation effort**: 1-2 days

### [CLARIFICATION]
The README previously stated `graph_of_thought.py` exists - this has been corrected. Only `__init__.py` with lazy loading infrastructure exists.

## Future Vision (V8)

- **Deep Thinking Mode**: Multi-level thought decomposition
- **Parallel Branch Execution**: Swarm agents work on separate graph branches
- **Thought Caching**: Reuse decomposition patterns for similar problems

## See Also

- [Swarm Module](../swarm/README.md) - Current problem decomposition via negotiation
- [ROADMAP](../../ROADMAP_HIVE_MIND.md) - GoT activation planning
