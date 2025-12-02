# NEXUS Evolution - API Reference

**Version**: 1.0
**Target Audience**: Developers
**Last Updated**: 2025-11-21

---

## Module: `core.evolution.lineage`

Phylogeny management, LINEAGE.json operations, birth certificates.

### `load_lineage(workspace_path: Path = None) -> Dict`

Load LINEAGE.json from project root.

**Parameters**:
- `workspace_path` (Path, optional): Workspace path (defaults to auto-detect)

**Returns**:
- `Dict`: Complete lineage data structure

**Raises**:
- `LineageError`: If LINEAGE.json not found or invalid JSON

**Example**:
```python
from pathlib import Path
from core.evolution.lineage import load_lineage

lineage = load_lineage(workspace_path=Path("workspace"))
print(f"Current parent: {lineage['current_parent']['id']}")
```

---

### `save_lineage(lineage: Dict, workspace_path: Path = None) -> None`

Save LINEAGE.json to project root with timestamp update.

**Parameters**:
- `lineage` (Dict): Lineage data structure
- `workspace_path` (Path, optional): Workspace path

**Returns**: None

**Raises**:
- `LineageError`: If save operation fails

---

### `get_current_parent(lineage: Dict = None) -> Dict`

Get current active parent NEXUS instance metadata.

**Parameters**:
- `lineage` (Dict, optional): Lineage dict (loaded if not provided)

**Returns**:
- `Dict`: Current parent metadata
  ```python
  {
    "id": "NEXUS_V7.0",
    "path": "NEXUS_V7_CHRYSALIS",
    "generation": 6,
    "asi_proximity_score": 0.75,
    "activated_at": "2025-11-21T19:20:00Z",
    "status": "active_parent"
  }
  ```

---

### `create_child_entry(...) -> Dict`

Create child entry metadata for PENDING_REVIEW.

**Parameters**:
- `child_id` (str): Unique child identifier
- `parent_id` (str): Parent NEXUS ID
- `generation` (int): Generation number
- `asi_score` (float): ASI proximity score (0.0-1.0)
- `improvements_summary` (str): Human-readable summary
- `birth_cert_path` (str): Path to birth certificate JSON
- `eval_results_path` (str): Path to evaluation results JSON
- `files_modified` (List[str]): List of modified file paths
- `lines_changed` (int): Total lines changed

**Returns**:
- `Dict`: Child metadata for review

---

### `promote_child_to_parent(...) -> Dict`

Promote child to become new active parent.

**Parameters**:
- `lineage` (Dict): Lineage data structure
- `child_id` (str): Child identifier
- `child_path` (Path): Path to child codebase
- `asi_score` (float): Child's ASI proximity score
- `birth_cert_path` (str): Path to signed birth certificate
- `notable_features` (List[str]): List of improvements

**Returns**:
- `Dict`: Updated lineage

**Side Effects**:
- Updates `current_parent`
- Adds child to `lineage_tree`
- Marks old parent as archived
- Increments generation counter
- Resets stagnation counter

---

### `update_stagnation_counter(lineage: Dict, increment: bool = True) -> Tuple[Dict, int]`

Update or reset stagnation counter (SURVIVAL_LAW enforcement).

**Parameters**:
- `lineage` (Dict): Lineage data structure
- `increment` (bool): True to increment, False to reset

**Returns**:
- `Tuple[Dict, int]`: (updated lineage, new counter value)

**Example**:
```python
lineage, counter = update_stagnation_counter(lineage, increment=True)
if counter >= 3:
    print("SURVIVAL_LAW triggered!")
```

---

### `sign_birth_certificate(birth_cert_path: Path, ssh_key_path: Path = None) -> bool`

Cryptographically sign birth certificate with SSH key.

**Parameters**:
- `birth_cert_path` (Path): Path to birth certificate JSON
- `ssh_key_path` (Path, optional): SSH private key path (defaults to ~/.ssh/id_rsa)

**Returns**:
- `bool`: True if signed successfully, False otherwise

**Side Effects**:
- Creates `.sig` file next to birth certificate

---

### `create_birth_certificate(...) -> Path`

Generate birth certificate JSON for child NEXUS.

**Parameters**:
- `child_id` (str): Child identifier
- `parent_id` (str): Parent identifier
- `generation` (int): Generation number
- `mutations_applied` (List[str]): List of mutation descriptions
- `files_modified` (List[str]): List of modified files
- `asi_score` (float): ASI proximity score
- `benchmarks` (Dict): Benchmark results dict
- `workspace_path` (Path): Workspace path

**Returns**:
- `Path`: Path to created birth certificate

---

## Module: `core.evolution.mutator`

Child generation, mutation application, diff documentation.

### `clone_parent(parent_path: Path, child_id: str, workspace_path: Path) -> Path`

Clone parent NEXUS to GENERATION_ACTIVE/ directory.

**Parameters**:
- `parent_path` (Path): Path to current parent NEXUS
- `child_id` (str): Unique child identifier
- `workspace_path` (Path): Workspace root path

**Returns**:
- `Path`: Child directory path

**Raises**:
- `MutationError`: If cloning fails or child already exists

**Example**:
```python
child_path = clone_parent(
    parent_path=Path("NEXUS_V7_CHRYSALIS"),
    child_id="NEXUS_V7.1_CHILD_001",
    workspace_path=Path("workspace")
)
# Returns: Path("GENERATION_ACTIVE/NEXUS_V7.1_CHILD_001")
```

---

### `apply_mutations(child_path: Path, mutation_functions: List[Callable], mutation_params: List[Dict]) -> List[Dict]`

Apply mutation functions to child NEXUS.

**Parameters**:
- `child_path` (Path): Path to child directory
- `mutation_functions` (List[Callable]): List of mutation functions
- `mutation_params` (List[Dict]): Parameters for each mutation

**Returns**:
- `List[Dict]`: Applied mutations with metadata

**Example**:
```python
mutations = apply_mutations(
    child_path=Path("GENERATION_ACTIVE/NEXUS_V7.1_CHILD_001"),
    mutation_functions=[optimize_fsm_transitions],
    mutation_params=[{"target_file": "core/orchestration_v7.py"}]
)
```

---

### `generate_diff(parent_path: Path, child_path: Path, output_file: str = "DIFF_FROM_PARENT.md") -> Path`

Generate diff documentation between parent and child.

**Parameters**:
- `parent_path` (Path): Parent NEXUS path
- `child_path` (Path): Child NEXUS path
- `output_file` (str): Output diff filename

**Returns**:
- `Path`: Path to diff file

---

### `create_child(...) -> Dict`

Complete child creation workflow (clone � mutate � diff � birth cert).

**Parameters**:
- `parent_path` (Path): Parent NEXUS path
- `child_id` (str): Child identifier
- `parent_id` (str): Parent identifier
- `generation` (int): Generation number
- `justification` (str): Detailed mutation justification
- `mutation_functions` (List[Callable]): List of mutation functions
- `mutation_params` (List[Dict]): Parameters for mutations
- `expected_improvements` (Dict): Expected improvement percentages
- `workspace_path` (Path): Workspace path

**Returns**:
- `Dict`: Child creation result
  ```python
  {
    "child_id": "NEXUS_V7.1_CHILD_001",
    "child_path": Path(...),
    "cert_path": Path(...),
    "diff_path": Path(...),
    "mutations_applied": [...],
    "metadata": {...}
  }
  ```

**Example**:
```python
from core.evolution.mutator import create_child, optimize_fsm_transitions

result = create_child(
    parent_path=Path("NEXUS_V7_CHRYSALIS"),
    child_id="NEXUS_V7.1_FSM_OPT",
    parent_id="NEXUS_V7.0",
    generation=7,
    justification="Optimize FSM state transitions with caching",
    mutation_functions=[optimize_fsm_transitions],
    mutation_params=[{"target_file": "core/orchestration_v7.py"}],
    expected_improvements={"latency_reduction": "15%"},
    workspace_path=Path("workspace")
)
```

---

### Mutation Functions

#### `optimize_fsm_transitions(child_path: Path, target_file: str) -> Dict`

Example mutation: Optimize FSM state transitions.

**Parameters**:
- `child_path` (Path): Child directory path
- `target_file` (str): Target file to modify

**Returns**:
- `Dict`: Mutation result metadata

#### `improve_memory_management(child_path: Path, target_file: str) -> Dict`

Example mutation: Improve memory management.

#### `enhance_gemini_prompt(child_path: Path, target_file: str) -> Dict`

Example mutation: Enhance Gemini system prompt.

---

## Module: `core.evolution.evaluator`

Benchmarking, ASI scoring, winner selection.

### `run_benchmarks(nexus_path: Path, nexus_id: str, benchmark_suite: str = "asi_proximity") -> Dict`

Run benchmark suite on NEXUS instance.

**Parameters**:
- `nexus_path` (Path): Path to NEXUS codebase
- `nexus_id` (str): NEXUS identifier
- `benchmark_suite` (str): Benchmark suite name

**Returns**:
- `Dict`: Benchmark results with scores per dimension
  ```python
  {
    "nexus_id": "NEXUS_V7.1_FSM_OPT",
    "benchmark_suite": "asi_proximity",
    "timestamp": "2025-11-21T21:00:00Z",
    "scores": {
      "coding": 0.82,
      "reasoning": 0.75,
      "creativity": 0.73,
      "scalability": 0.81
    },
    "raw_results": {...},
    "simulated": True  # MVP mode
  }
  ```

**Note**: MVP version uses simulated benchmarks. Production will execute real tasks.

---

### `calculate_asi_proximity(benchmark_results: Dict, weights: Dict = None) -> float`

Calculate ASI Proximity Score from benchmark results.

**Parameters**:
- `benchmark_results` (Dict): Results from `run_benchmarks()`
- `weights` (Dict, optional): Custom weights (defaults to Q2C: 30/30/25/15)

**Returns**:
- `float`: ASI Proximity Score (0.0-1.0)

**Formula**:
```
ASI = (coding * 0.30) + (reasoning * 0.30) + (creativity * 0.25) + (scalability * 0.15)
```

**Interpretation**:
- 0.95+: ASI-level (superintelligence)
- 0.80-0.95: Expert-level
- 0.60-0.80: Competent
- <0.60: Needs improvement

---

### `compare_to_parent(child_results: Dict, parent_results: Dict) -> Dict`

Compare child ASI score to parent.

**Parameters**:
- `child_results` (Dict): Child benchmark results
- `parent_results` (Dict): Parent benchmark results

**Returns**:
- `Dict`: Comparison metadata
  ```python
  {
    "child_id": "NEXUS_V7.1_CHILD_001",
    "parent_id": "NEXUS_V7.0",
    "child_score": 0.78,
    "parent_score": 0.75,
    "improvement_percent": 4.0,
    "significance": "significant",  # significant|minor|negligible|regression
    "dimensions": {
      "coding": {"child": 0.82, "parent": 0.80, "delta": +0.02},
      ...
    }
  }
  ```

---

### `select_winner(candidates: List[Dict], parent_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]`

Select winner from candidates (children + parent).

**Parameters**:
- `candidates` (List[Dict]): List of benchmark results dicts
- `parent_id` (Optional[str]): Parent ID for tie-breaking

**Returns**:
- `Tuple[Dict, List[Dict]]`: (winner_dict, ranked_losers_list)

**Selection Criterion**: Highest ASI Proximity Score wins.

**Tie-Breaker**: If scores equal, parent wins (stability preference).

---

### `generate_evaluation_report(nexus_id: str, nexus_path: Path, benchmark_results: Dict, comparison: Optional[Dict] = None, output_file: str = "EVALUATION_RESULTS.json") -> Path`

Generate comprehensive evaluation report JSON.

**Parameters**:
- `nexus_id` (str): NEXUS identifier
- `nexus_path` (Path): Path to NEXUS codebase
- `benchmark_results` (Dict): Benchmark results
- `comparison` (Optional[Dict]): Comparison to parent
- `output_file` (str): Output filename

**Returns**:
- `Path`: Path to evaluation report

---

### `evaluate_child(child_path: Path, child_id: str, parent_path: Path, parent_id: str) -> Dict`

Complete evaluation workflow for a single child.

**Parameters**:
- `child_path` (Path): Path to child NEXUS
- `child_id` (str): Child identifier
- `parent_path` (Path): Path to parent NEXUS
- `parent_id` (str): Parent identifier

**Returns**:
- `Dict`: Complete evaluation results
  ```python
  {
    "child_id": "NEXUS_V7.1_CHILD_001",
    "child_results": {...},
    "parent_results": {...},
    "comparison": {...},
    "report_path": Path(...)
  }
  ```

**Steps**:
1. Run benchmarks on child
2. Load/run benchmarks on parent
3. Calculate ASI scores
4. Compare child to parent
5. Generate evaluation report

---

## Data Structures

### Lineage Structure

```python
{
  "lineage_version": "1.0",
  "created_at": "2025-11-21T20:00:00Z",
  "last_updated": "2025-11-21T20:00:00Z",
  "current_parent": {
    "id": "NEXUS_V7.0",
    "path": "NEXUS_V7_CHRYSALIS",
    "generation": 6,
    "asi_proximity_score": 0.75,
    "activated_at": "2025-11-21T19:20:00Z",
    "status": "active_parent"
  },
  "evolution_stats": {
    "total_generations": 6,
    "total_children_created": 0,
    "successful_promotions": 5,
    "stagnation_counter": 0
  },
  "lineage_tree": {
    "NEXUS_V7.0": {
      "generation": 6,
      "parent": "NEXUS_V5.1",
      "children": [],
      "status": "active_parent",
      "created_at": "2025-11-21T19:20:00Z",
      "asi_proximity_score": 0.75,
      "notable_features": [...],
      "birth_certificate": null,
      "stagnation_counter": 0
    }
  },
  "archived_generations": {...},
  "security_log": {...}
}
```

### Birth Certificate Structure

```python
{
  "birth_certificate": {
    "child_id": "NEXUS_V7.1_FSM_OPT",
    "parent_id": "NEXUS_V7.0",
    "generation": 7,
    "birth_timestamp": "2025-11-21T20:30:00Z",
    "creator": "NEXUS Evolution Engine",
    "human_authority": "Yann Abadie",
    "justification": "Optimize FSM state transitions with caching",
    "code_changes": {
      "files_modified": ["core/orchestration_v7.py"],
      "diff_hash": "sha256:...",
      "lines_changed": 127
    },
    "mutations_applied": [{
      "function": "optimize_fsm_transitions",
      "params": {...},
      "result": {...},
      "timestamp": "2025-11-21T20:30:05Z"
    }],
    "expected_improvements": {
      "latency_reduction": "15%"
    },
    "test_protocol": "benchmarks/asi_proximity.py",
    "signature": "-----BEGIN SSH SIGNATURE-----..."
  }
}
```

### Benchmark Results Structure

```python
{
  "nexus_id": "NEXUS_V7.1_FSM_OPT",
  "benchmark_suite": "asi_proximity",
  "timestamp": "2025-11-21T21:00:00Z",
  "scores": {
    "coding": 0.82,      # 0.0-1.0
    "reasoning": 0.75,
    "creativity": 0.73,
    "scalability": 0.81
  },
  "raw_results": {
    "coding_tasks_passed": 14,
    "coding_tasks_total": 15,
    "reasoning_puzzles_solved": 8,
    "reasoning_puzzles_total": 10,
    "creativity_score": 0.85,
    "scalability_max_problem_size": 1100
  },
  "asi_proximity_score": 0.78,  # Calculated
  "simulated": True  # MVP flag
}
```

---

## Configuration

### ASI Metrics Weights (Q2C)

```python
asi_metrics = {
    "coding": 0.30,
    "reasoning": 0.30,
    "creativity": 0.25,
    "scalability": 0.15
}
```

### Evolution Parameters

```python
# Q1C: Max Children
max_children_concurrent = 3  # MVP mode
max_children_stable = 10     # After 5 successful generations

# Q3B: Rate Limiting
max_generations_per_day = 3
min_hours_between_gen = 8

# Q4B: Evaluation Timeline
minimum_eval_hours = 24
recommended_eval_hours = 48
critical_eval_hours = 72

# Auto-evolution
evolution_trigger_turns = 50
```

---

## Error Handling

### Exception Classes

```python
class LineageError(Exception):
    """Raised when LINEAGE.json operations fail"""
    pass

class MutationError(Exception):
    """Raised when child creation or mutation fails"""
    pass

class EvaluationError(Exception):
    """Raised when benchmarking fails"""
    pass
```

### Common Errors

**`LineageError: LINEAGE.json not found`**
- Cause: Missing LINEAGE.json in project root
- Solution: Ensure file exists or create from template

**`MutationError: Child already exists`**
- Cause: Child directory not cleaned up
- Solution: Delete existing child or use unique ID

**`EvaluationError: Benchmark timeout`**
- Cause: Benchmark taking too long
- Solution: Use simulated benchmarks or increase timeout

---

## Module: `core.bootstrap`

AutoBootstrap module for automatic NEXUS.md generation when deployed to new projects.

### `class AutoBootstrap`

Automatically analyze a project and generate NEXUS.md.

**Constructor**:
```python
AutoBootstrap(project_path: Path)
```

**Parameters**:
- `project_path` (Path): Path to project root

**Methods**:

#### `analyze() -> ProjectAnalysis`

Analyze project structure, detect tech stack, frameworks, and commands.

**Returns**:
- `ProjectAnalysis`: Dataclass with detected information

**Example**:
```python
from pathlib import Path
from core.bootstrap import AutoBootstrap

bootstrap = AutoBootstrap(Path("/path/to/project"))
analysis = bootstrap.analyze()

print(f"Languages: {analysis.languages}")
print(f"Frameworks: {analysis.frameworks}")
print(f"Has tests: {analysis.has_tests}")
```

#### `generate_nexus_md(analysis: ProjectAnalysis = None) -> str`

Generate NEXUS.md content from analysis results.

**Parameters**:
- `analysis` (ProjectAnalysis, optional): Analysis results (runs analyze() if not provided)

**Returns**:
- `str`: Complete NEXUS.md markdown content

#### `save(content: str = None, path: Path = None) -> Path`

Save NEXUS.md to project.

**Parameters**:
- `content` (str, optional): NEXUS.md content (generates if not provided)
- `path` (Path, optional): Save path (defaults to project_path/NEXUS.md)

**Returns**:
- `Path`: Path where file was saved

---

### `class ProjectAnalysis`

Dataclass containing project analysis results.

**Fields**:
- `languages` (List[str]): Detected programming languages
- `frameworks` (List[str]): Detected frameworks (FastAPI, React, etc.)
- `databases` (List[str]): Detected databases
- `tools` (List[str]): Detected tools (pytest, eslint, etc.)
- `directories` (List[str]): Top-level directories
- `key_files` (List[str]): Important files found
- `commands` (Dict[str, str]): Discovered commands (name -> description)
- `has_tests` (bool): Tests directory detected
- `has_docs` (bool): Documentation directory detected
- `has_ci` (bool): CI/CD configuration detected
- `project_name` (str): Inferred project name

---

## Module: `core.reasoning`

Graph of Thought (GoT) module for advanced non-linear reasoning.

### `class GraphOfThought`

Main interface for Graph of Thought reasoning.

**Methods**:

#### `decompose_problem(...) -> ThoughtGraph`

Decompose a complex problem into a graph of sub-problems.

**Parameters**:
- `main_problem` (str): Main problem description
- `sub_problems` (List[str]): List of sub-problem descriptions
- `parallel_groups` (List[List[int]], optional): Groups of sub-problem indices to run in parallel
- `name` (str, optional): Graph name

**Returns**:
- `ThoughtGraph`: Graph with root, sub-problem nodes, and aggregation node

**Example**:
```python
from core.reasoning import GraphOfThought

got = GraphOfThought()
graph = got.decompose_problem(
    main_problem="Refactor authentication module",
    sub_problems=[
        "Analyze current code",
        "Identify security issues",
        "Design new architecture",
        "Implement changes",
        "Add tests"
    ],
    parallel_groups=[[3, 4]]  # Implement and test in parallel
)
```

#### `execute(graph, executor, max_iterations=100) -> ThoughtGraph`

Execute graph sequentially using provided executor function.

**Parameters**:
- `graph` (ThoughtGraph): Graph to execute
- `executor` (Callable[[ThoughtNode], str]): Function that processes a node and returns answer
- `max_iterations` (int): Maximum iterations

**Returns**:
- `ThoughtGraph`: Completed graph with answers

#### `execute_parallel(...) -> ThoughtGraph`

Execute graph with parallel node processing.

**Parameters**:
- `graph` (ThoughtGraph): Graph to execute
- `executor` (Callable[[ThoughtNode], str]): Executor function
- `max_workers` (int): Maximum parallel workers (default: 3)
- `max_iterations` (int): Maximum iterations (default: 100)
- `on_progress` (Callable, optional): Progress callback(graph, node, event)

**Returns**:
- `ThoughtGraph`: Completed graph

**Example**:
```python
def my_executor(node):
    # Call LLM with node.question
    return llm_response

def on_progress(graph, node, event):
    print(f"{event}: {node.name}")

result = got.execute_parallel(
    graph,
    my_executor,
    max_workers=3,
    on_progress=on_progress
)
```

#### `visualize_progress(graph) -> str`

Generate progress visualization string for REPL display.

**Returns**:
- `str`: Formatted ASCII progress display

---

### `class ThoughtGraph`

Graph structure containing thought nodes.

**Properties**:
- `name` (str): Graph name
- `nodes` (Dict[str, ThoughtNode]): All nodes by ID
- `root_nodes` (List[str]): IDs of root nodes (no dependencies)
- `leaf_nodes` (List[str]): IDs of leaf nodes (no children)

**Methods**:
- `create_node(question, name, ...)` - Create and add a node
- `get_ready_nodes()` - Get nodes ready for execution
- `get_execution_order()` - Get topological execution order
- `is_complete()` - Check if all nodes are processed
- `get_final_answer()` - Aggregate answers from leaf nodes

---

### `class ThoughtNode`

Single node in the thought graph.

**Fields**:
- `id` (str): Unique identifier
- `name` (str): Human-readable name
- `question` (str): Question/task for this node
- `answer` (str): Result after processing
- `status` (ThoughtStatus): PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED
- `dependencies` (List[str]): IDs of nodes this depends on
- `children` (List[str]): IDs of dependent nodes
- `confidence` (float): Confidence in answer (0.0-1.0)

---

## Module: `core.security`

Security modules for protecting parent code and validating mutations.

### `class PathGuardian`

Path validation for read/write operations with zone-based security.

**Constructor**:
```python
PathGuardian(
    workspace_path: Path,
    parent_path: Path,
    generation_active: Path = None
)
```

**Methods**:

#### `validate_read(file_path: str) -> tuple`

Validate a file path for read operations.

**Parameters**:
- `file_path` (str): Path to validate

**Returns**:
- `tuple`: (valid: bool, resolved_path: Path, message: str)

#### `validate_write(file_path: str, is_evolution_mode: bool = False) -> tuple`

Validate a file path for write operations.

**Parameters**:
- `file_path` (str): Path to validate
- `is_evolution_mode` (bool): Whether evolution mode is active

**Returns**:
- `tuple`: (valid: bool, resolved_path: Path, message: str)

**Example**:
```python
from core.security import PathGuardian

guardian = PathGuardian(
    workspace_path=Path("workspace"),
    parent_path=Path("NEXUS_V7_CHRYSALIS")
)

valid, path, msg = guardian.validate_write("new_file.py")
if valid:
    print(f"OK to write: {path}")
else:
    print(f"BLOCKED: {msg}")
```

**Security Zones**:
- **Workspace**: Full read/write access
- **Parent**: Read-only access (no writes)
- **GENERATION_ACTIVE**: Write access only in evolution mode
- **Sacred files**: KERNEL.py, MISSION.md, .env always protected

---

### `class MutationValidator`

AST-based behavioral analysis for mutation code.

**Constructor**:
```python
MutationValidator(workspace_path: Path)
```

**Methods**:

#### `validate(code: str, filename: str) -> tuple`

Validate Python code for suspicious patterns.

**Parameters**:
- `code` (str): Python source code
- `filename` (str): Filename for context

**Returns**:
- `tuple`: (warnings: List[str], info: List[str])

**Example**:
```python
from core.security import MutationValidator

validator = MutationValidator(Path("workspace"))

code = '''
import os
os.system("rm -rf /")
'''

warnings, info = validator.validate(code, "dangerous.py")
# warnings: ["Suspicious import: os", "Suspicious call: os.system"]
```

**Detected Patterns**:
- Suspicious imports: os, subprocess, shutil, socket
- Dangerous calls: exec(), eval(), os.system(), subprocess.run()
- Path traversal in open(): "../" paths, absolute paths

---

## REPL Commands

### `/bootstrap [path]`

Analyze project and generate NEXUS.md.

**Parameters**:
- `path` (optional): Project path (defaults to current directory)

**Example**:
```
nexus7> /bootstrap /path/to/project
🔍 Analyzing project: /path/to/project

📊 Analysis Results:
   Project: my-project
   Languages: Python
   Frameworks: FastAPI
   Has tests: Yes

✅ Generated: /path/to/project/NEXUS.md
```

---

## References

- **core/evolution/README.md** - Evolution module documentation
- **core/bootstrap/README.md** - Bootstrap module documentation
- **core/reasoning/README.md** - Reasoning module documentation
- **EVOLUTION_GUIDE.md** - User guide
- **EVOLUTION_PROTOCOL.md** - Protocol specification
- **INVARIANTS.md** - Immutable laws
- **MISSION.md** - NEXUS vision

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-21 | Initial API reference |
| 1.1 | 2025-11-27 | Added bootstrap, reasoning, security modules |
