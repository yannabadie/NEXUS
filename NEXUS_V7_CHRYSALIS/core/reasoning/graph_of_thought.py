"""
Graph of Thought (GoT) - Advanced Reasoning for Complex Problems

GoT extends Chain of Thought by allowing non-linear reasoning:
- Decompose complex problems into sub-problems (nodes)
- Track dependencies between sub-problems
- Explore multiple solution paths (branches)
- Merge successful branches into final solution
- Backtrack on failed paths

Use Cases:
- Multi-step code refactoring
- Complex bug analysis
- Architecture decisions
- Research tasks with multiple angles

Reference: "Graph of Thoughts" (Besta et al., 2023)
"""

import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime


class ThoughtStatus(Enum):
    """Status of a thought node."""
    PENDING = auto()      # Not yet processed
    IN_PROGRESS = auto()  # Currently being processed
    COMPLETED = auto()    # Successfully completed
    FAILED = auto()       # Failed to complete
    SKIPPED = auto()      # Skipped (dependency failed)
    MERGED = auto()       # Merged into another node


class ThoughtType(Enum):
    """Type of thought operation."""
    DECOMPOSE = auto()    # Break problem into sub-problems
    ANALYZE = auto()      # Analyze information
    GENERATE = auto()     # Generate solution/code
    EVALUATE = auto()     # Evaluate a solution
    AGGREGATE = auto()    # Merge multiple solutions
    DECISION = auto()     # Make a choice between options


@dataclass
class ThoughtNode:
    """
    A single node in the Graph of Thought.

    Represents one step in the reasoning process with:
    - A question/problem to solve
    - Possible answers/solutions
    - Dependencies on other nodes
    - Score/confidence in the solution
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""

    # Content
    question: str = ""                    # What problem to solve
    context: str = ""                     # Additional context
    thought_type: ThoughtType = ThoughtType.ANALYZE

    # Results
    answer: str = ""                      # The solution/answer
    confidence: float = 0.0               # 0.0 to 1.0 confidence
    reasoning: str = ""                   # Chain of thought for this node

    # Graph structure
    dependencies: List[str] = field(default_factory=list)  # Node IDs this depends on
    children: List[str] = field(default_factory=list)      # Node IDs that depend on this

    # State
    status: ThoughtStatus = ThoughtStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    agent: str = ""                       # Which agent processed this

    def is_ready(self, completed_nodes: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_nodes for dep in self.dependencies)

    def mark_completed(self, answer: str, confidence: float = 1.0, reasoning: str = ""):
        """Mark node as completed with answer."""
        self.answer = answer
        self.confidence = confidence
        self.reasoning = reasoning
        self.status = ThoughtStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()

    def mark_failed(self, reason: str = ""):
        """Mark node as failed."""
        self.status = ThoughtStatus.FAILED
        self.reasoning = reason
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "question": self.question,
            "context": self.context[:200] + "..." if len(self.context) > 200 else self.context,
            "thought_type": self.thought_type.name,
            "answer": self.answer[:500] + "..." if len(self.answer) > 500 else self.answer,
            "confidence": self.confidence,
            "status": self.status.name,
            "dependencies": self.dependencies,
            "children": self.children,
            "agent": self.agent
        }


class ThoughtGraph:
    """
    A graph of interconnected thoughts for complex reasoning.

    Supports:
    - Adding nodes with dependencies
    - Finding ready nodes (dependencies satisfied)
    - Topological ordering for execution
    - Branch and merge operations
    """

    def __init__(self, name: str = ""):
        """
        Initialize an empty thought graph.

        Args:
            name: Optional name for this graph
        """
        self.name = name or f"graph_{uuid.uuid4().hex[:6]}"
        self.nodes: Dict[str, ThoughtNode] = {}
        self.root_nodes: List[str] = []      # Nodes with no dependencies
        self.leaf_nodes: List[str] = []      # Nodes with no children
        self.created_at = datetime.now().isoformat()

    def add_node(self, node: ThoughtNode) -> str:
        """
        Add a node to the graph.

        Args:
            node: ThoughtNode to add

        Returns:
            Node ID
        """
        self.nodes[node.id] = node

        # Update root/leaf tracking
        if not node.dependencies:
            self.root_nodes.append(node.id)

        # Update parent nodes' children lists
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                if node.id not in self.nodes[dep_id].children:
                    self.nodes[dep_id].children.append(node.id)
                # Remove from leaf nodes if it was there
                if dep_id in self.leaf_nodes:
                    self.leaf_nodes.remove(dep_id)

        # This node is a leaf until something depends on it
        self.leaf_nodes.append(node.id)

        return node.id

    def create_node(
        self,
        question: str,
        name: str = "",
        thought_type: ThoughtType = ThoughtType.ANALYZE,
        dependencies: List[str] = None,
        context: str = ""
    ) -> ThoughtNode:
        """
        Create and add a new node.

        Args:
            question: The problem/question for this node
            name: Human-readable name
            thought_type: Type of thought operation
            dependencies: List of node IDs this depends on
            context: Additional context

        Returns:
            Created ThoughtNode
        """
        node = ThoughtNode(
            name=name or f"thought_{len(self.nodes) + 1}",
            question=question,
            thought_type=thought_type,
            dependencies=dependencies or [],
            context=context
        )
        self.add_node(node)
        return node

    def get_node(self, node_id: str) -> Optional[ThoughtNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_ready_nodes(self) -> List[ThoughtNode]:
        """
        Get all nodes that are ready to be processed.

        A node is ready if:
        - Status is PENDING
        - All dependencies are COMPLETED
        """
        completed = {
            nid for nid, node in self.nodes.items()
            if node.status == ThoughtStatus.COMPLETED
        }

        ready = []
        for node in self.nodes.values():
            if node.status == ThoughtStatus.PENDING and node.is_ready(completed):
                ready.append(node)

        return ready

    def get_execution_order(self) -> List[str]:
        """
        Get topological order for executing nodes.

        Returns nodes in order such that dependencies come before dependents.
        """
        # Kahn's algorithm
        in_degree = {nid: len(node.dependencies) for nid, node in self.nodes.items()}
        queue = [nid for nid, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node_id = queue.pop(0)
            order.append(node_id)

            for child_id in self.nodes[node_id].children:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        return order

    def get_completed_count(self) -> int:
        """Count completed nodes."""
        return sum(1 for n in self.nodes.values() if n.status == ThoughtStatus.COMPLETED)

    def get_failed_count(self) -> int:
        """Count failed nodes."""
        return sum(1 for n in self.nodes.values() if n.status == ThoughtStatus.FAILED)

    def is_complete(self) -> bool:
        """Check if all nodes are processed (completed or failed)."""
        return all(
            n.status in (ThoughtStatus.COMPLETED, ThoughtStatus.FAILED, ThoughtStatus.SKIPPED)
            for n in self.nodes.values()
        )

    def get_final_answer(self) -> str:
        """
        Get the aggregated final answer from leaf nodes.

        Returns answers from all completed leaf nodes.
        """
        answers = []
        for leaf_id in self.leaf_nodes:
            node = self.nodes.get(leaf_id)
            if node and node.status == ThoughtStatus.COMPLETED:
                answers.append(f"[{node.name}]: {node.answer}")

        return "\n\n".join(answers) if answers else "No completed answers"

    def to_dict(self) -> Dict:
        """Serialize graph to dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "node_count": len(self.nodes),
            "completed": self.get_completed_count(),
            "failed": self.get_failed_count(),
            "is_complete": self.is_complete(),
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "execution_order": self.get_execution_order()
        }

    def visualize_ascii(self) -> str:
        """
        Create ASCII visualization of the graph.

        Returns simple text representation.
        """
        lines = [f"=== {self.name} ===", ""]

        # Show nodes by level (BFS from roots)
        visited = set()
        current_level = list(self.root_nodes)
        level = 0

        while current_level:
            lines.append(f"Level {level}:")
            next_level = []

            for node_id in current_level:
                if node_id in visited:
                    continue
                visited.add(node_id)

                node = self.nodes[node_id]
                status_icon = {
                    ThoughtStatus.PENDING: "⏳",
                    ThoughtStatus.IN_PROGRESS: "🔄",
                    ThoughtStatus.COMPLETED: "✅",
                    ThoughtStatus.FAILED: "❌",
                    ThoughtStatus.SKIPPED: "⏭️",
                    ThoughtStatus.MERGED: "🔀"
                }.get(node.status, "❓")

                deps = f" <- [{', '.join(node.dependencies)}]" if node.dependencies else ""
                lines.append(f"  {status_icon} {node.name} ({node.id}){deps}")

                next_level.extend(node.children)

            current_level = next_level
            level += 1
            lines.append("")

        return "\n".join(lines)


class GraphOfThought:
    """
    Main interface for Graph of Thought reasoning.

    Usage:
        got = GraphOfThought()

        # Decompose problem
        graph = got.decompose_problem(
            "Refactor the authentication system",
            sub_problems=[
                "Analyze current auth code",
                "Identify security issues",
                "Design new auth flow",
                "Implement changes"
            ]
        )

        # Execute (with custom executor)
        result = got.execute(graph, executor=my_agent_executor)
    """

    def __init__(self):
        """Initialize GraphOfThought processor."""
        self.graphs: Dict[str, ThoughtGraph] = {}

    def decompose_problem(
        self,
        main_problem: str,
        sub_problems: List[str],
        parallel_groups: List[List[int]] = None,
        name: str = ""
    ) -> ThoughtGraph:
        """
        Decompose a complex problem into a graph of sub-problems.

        Args:
            main_problem: The main problem to solve
            sub_problems: List of sub-problem descriptions
            parallel_groups: Optional groups of indices that can run in parallel
                            e.g., [[0, 1], [2, 3]] means 0,1 parallel, then 2,3 parallel
            name: Optional name for the graph

        Returns:
            ThoughtGraph with decomposed problems

        Example:
            graph = got.decompose_problem(
                "Fix authentication bug",
                [
                    "Read auth.py and understand current flow",
                    "Read test_auth.py for expected behavior",
                    "Identify the bug location",
                    "Design fix approach",
                    "Implement fix",
                    "Verify with tests"
                ],
                parallel_groups=[[0, 1], [4, 5]]  # Read files in parallel
            )
        """
        graph = ThoughtGraph(name or f"got_{uuid.uuid4().hex[:6]}")

        # Create root node for the main problem
        root = graph.create_node(
            question=main_problem,
            name="main_problem",
            thought_type=ThoughtType.DECOMPOSE,
            context="This is the main problem to be decomposed."
        )

        # Track node IDs by sub-problem index
        node_ids: Dict[int, str] = {}

        # Create nodes for sub-problems
        prev_group_ids: List[str] = [root.id]

        if parallel_groups:
            # Process with explicit parallel groups
            processed_indices = set()

            for group in parallel_groups:
                group_ids = []
                for idx in group:
                    if idx < len(sub_problems):
                        node = graph.create_node(
                            question=sub_problems[idx],
                            name=f"step_{idx + 1}",
                            thought_type=ThoughtType.ANALYZE,
                            dependencies=prev_group_ids.copy()
                        )
                        node_ids[idx] = node.id
                        group_ids.append(node.id)
                        processed_indices.add(idx)

                if group_ids:
                    prev_group_ids = group_ids

            # Add any remaining sub-problems sequentially
            for idx, sp in enumerate(sub_problems):
                if idx not in processed_indices:
                    node = graph.create_node(
                        question=sp,
                        name=f"step_{idx + 1}",
                        thought_type=ThoughtType.ANALYZE,
                        dependencies=prev_group_ids.copy()
                    )
                    node_ids[idx] = node.id
                    prev_group_ids = [node.id]

        else:
            # Simple sequential chain
            for idx, sp in enumerate(sub_problems):
                node = graph.create_node(
                    question=sp,
                    name=f"step_{idx + 1}",
                    thought_type=ThoughtType.ANALYZE,
                    dependencies=prev_group_ids.copy()
                )
                node_ids[idx] = node.id
                prev_group_ids = [node.id]

        # Create aggregation node
        all_step_ids = list(node_ids.values())
        agg = graph.create_node(
            question=f"Aggregate results to answer: {main_problem}",
            name="aggregate",
            thought_type=ThoughtType.AGGREGATE,
            dependencies=all_step_ids
        )

        self.graphs[graph.name] = graph
        return graph

    def create_decision_tree(
        self,
        question: str,
        options: List[str],
        evaluation_criteria: str = "",
        name: str = ""
    ) -> ThoughtGraph:
        """
        Create a decision tree for choosing between options.

        Args:
            question: The decision question
            options: List of options to evaluate
            evaluation_criteria: Criteria for evaluation
            name: Optional name

        Returns:
            ThoughtGraph for the decision

        Example:
            graph = got.create_decision_tree(
                "Which database should we use?",
                ["PostgreSQL", "MongoDB", "SQLite"],
                "Consider: performance, scalability, ease of use"
            )
        """
        graph = ThoughtGraph(name or f"decision_{uuid.uuid4().hex[:6]}")

        # Create root analysis node
        root = graph.create_node(
            question=question,
            name="decision_question",
            thought_type=ThoughtType.ANALYZE,
            context=evaluation_criteria
        )

        # Create evaluation nodes for each option (parallel)
        eval_ids = []
        for i, option in enumerate(options):
            node = graph.create_node(
                question=f"Evaluate option: {option}",
                name=f"eval_{option[:20]}",
                thought_type=ThoughtType.EVALUATE,
                dependencies=[root.id],
                context=f"Criteria: {evaluation_criteria}"
            )
            eval_ids.append(node.id)

        # Create decision node
        decision = graph.create_node(
            question=f"Make final decision: {question}",
            name="final_decision",
            thought_type=ThoughtType.DECISION,
            dependencies=eval_ids,
            context=f"Options evaluated: {', '.join(options)}"
        )

        self.graphs[graph.name] = graph
        return graph

    def execute(
        self,
        graph: ThoughtGraph,
        executor: Callable[[ThoughtNode], str],
        max_iterations: int = 100
    ) -> ThoughtGraph:
        """
        Execute the thought graph using provided executor.

        Args:
            graph: The ThoughtGraph to execute
            executor: Function that takes a ThoughtNode and returns answer string
            max_iterations: Maximum iterations to prevent infinite loops

        Returns:
            The executed ThoughtGraph with answers

        Example:
            def my_executor(node: ThoughtNode) -> str:
                # Call LLM with node.question
                return llm_response

            result = got.execute(graph, my_executor)
        """
        iterations = 0

        while not graph.is_complete() and iterations < max_iterations:
            iterations += 1

            # Get nodes ready to process
            ready_nodes = graph.get_ready_nodes()

            if not ready_nodes:
                # No ready nodes but not complete - might be stuck
                pending = [n for n in graph.nodes.values() if n.status == ThoughtStatus.PENDING]
                if pending:
                    # Check if dependencies failed
                    for node in pending:
                        failed_deps = [
                            d for d in node.dependencies
                            if graph.nodes.get(d) and graph.nodes[d].status == ThoughtStatus.FAILED
                        ]
                        if failed_deps:
                            node.status = ThoughtStatus.SKIPPED
                            node.reasoning = f"Skipped due to failed dependencies: {failed_deps}"
                continue

            # Process ready nodes (could be parallelized)
            for node in ready_nodes:
                node.status = ThoughtStatus.IN_PROGRESS
                node.attempts += 1

                try:
                    # Build context from completed dependencies
                    dep_context = []
                    for dep_id in node.dependencies:
                        dep_node = graph.get_node(dep_id)
                        if dep_node and dep_node.status == ThoughtStatus.COMPLETED:
                            dep_context.append(f"[{dep_node.name}]: {dep_node.answer}")

                    if dep_context:
                        node.context = f"Previous results:\n" + "\n".join(dep_context) + "\n\n" + node.context

                    # Execute
                    answer = executor(node)
                    node.mark_completed(answer, confidence=1.0)

                except Exception as e:
                    if node.attempts >= node.max_attempts:
                        node.mark_failed(str(e))
                    else:
                        node.status = ThoughtStatus.PENDING  # Retry

        return graph

    def get_graph(self, name: str) -> Optional[ThoughtGraph]:
        """Get a graph by name."""
        return self.graphs.get(name)


# Convenience functions

def create_simple_chain(steps: List[str], name: str = "") -> ThoughtGraph:
    """
    Create a simple sequential chain of thoughts.

    Args:
        steps: List of step descriptions
        name: Optional name

    Returns:
        ThoughtGraph with sequential steps
    """
    got = GraphOfThought()
    return got.decompose_problem(
        main_problem=steps[0] if steps else "Unknown problem",
        sub_problems=steps[1:] if len(steps) > 1 else [],
        name=name
    )


def create_parallel_exploration(
    question: str,
    approaches: List[str],
    name: str = ""
) -> ThoughtGraph:
    """
    Create parallel exploration of multiple approaches.

    Args:
        question: Main question
        approaches: Different approaches to try in parallel
        name: Optional name

    Returns:
        ThoughtGraph with parallel branches
    """
    graph = ThoughtGraph(name or "parallel_exploration")

    # Root question
    root = graph.create_node(
        question=question,
        name="main_question",
        thought_type=ThoughtType.DECOMPOSE
    )

    # Parallel approach nodes
    approach_ids = []
    for i, approach in enumerate(approaches):
        node = graph.create_node(
            question=f"Explore approach: {approach}",
            name=f"approach_{i + 1}",
            thought_type=ThoughtType.GENERATE,
            dependencies=[root.id]
        )
        approach_ids.append(node.id)

    # Aggregation
    graph.create_node(
        question="Compare approaches and select best solution",
        name="aggregate",
        thought_type=ThoughtType.AGGREGATE,
        dependencies=approach_ids
    )

    return graph
