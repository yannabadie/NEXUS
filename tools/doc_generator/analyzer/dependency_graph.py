# NEXUS Documentation Generator - Dependency Graph Builder
"""
Builds import dependency graphs using networkx.
"""

from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, ModuleInfo

# Try to import networkx, fall back to a simple implementation
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class SimpleGraph:
    """Simple graph implementation when networkx is not available."""

    def __init__(self):
        self._nodes = {}
        self._edges = []

    def add_node(self, node: str, **attrs):
        self._nodes[node] = attrs

    def add_edge(self, from_node: str, to_node: str, **attrs):
        self._edges.append((from_node, to_node, attrs))

    def number_of_nodes(self) -> int:
        return len(self._nodes)

    def number_of_edges(self) -> int:
        return len(self._edges)

    def nodes(self, data: bool = False):
        if data:
            return list(self._nodes.items())
        return list(self._nodes.keys())

    def edges(self, data: bool = False):
        if data:
            return self._edges
        return [(e[0], e[1]) for e in self._edges]

    def in_edges(self, node: str):
        return [(e[0], e[1]) for e in self._edges if e[1] == node]

    def out_edges(self, node: str):
        return [(e[0], e[1]) for e in self._edges if e[0] == node]

    def predecessors(self, node: str):
        return [e[0] for e in self._edges if e[1] == node]

    def successors(self, node: str):
        return [e[1] for e in self._edges if e[0] == node]

    def has_node(self, node: str) -> bool:
        return node in self._nodes

    def get_node_data(self, node: str) -> dict:
        return self._nodes.get(node, {})


class DependencyGraphBuilder:
    """Builds dependency graphs from module information."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config
        self.repo_root = config.repo_root
        self._call_index = {}  # V13.0: Module -> CallInfo list

    def build(self, modules: list[ModuleInfo]) -> "nx.DiGraph | SimpleGraph":
        """
        Build a dependency graph from module information.

        Args:
            modules: List of ModuleInfo objects

        Returns:
            NetworkX DiGraph (or SimpleGraph if networkx not available)
        """
        if HAS_NETWORKX:
            graph = nx.DiGraph()
        else:
            graph = SimpleGraph()

        # Create module path to name mapping
        module_paths = {}
        for mod in modules:
            # Convert path to module name (e.g., core/fsm/states.py -> core.fsm.states)
            module_name = self._path_to_module_name(mod.path)
            module_paths[module_name] = mod
            graph.add_node(module_name, module=mod, path=str(mod.path))

        # Add edges for imports
        for mod in modules:
            module_name = self._path_to_module_name(mod.path)

            for imp in mod.imports:
                # Resolve import to module name
                target = self._resolve_import(imp.module, module_paths)

                if target and target != module_name:
                    graph.add_edge(module_name, target, names=imp.names)

        # V13.0: Build call index for INTERACTION MATRIX
        self._build_call_index(modules, module_paths)

        return graph

    def _build_call_index(
        self,
        modules: list[ModuleInfo],
        module_paths: dict[str, ModuleInfo]
    ) -> None:
        """
        Build an index of calls for INTERACTION MATRIX (V13.0).

        Creates a mapping from module names to their outbound/inbound calls.
        """
        self._call_index = {}

        for mod in modules:
            module_name = self._path_to_module_name(mod.path)
            self._call_index[module_name] = {
                "outbound": [],  # Calls made from this module
                "inbound": [],   # Calls received by this module
                "internal": [],  # Internal calls within this module
            }

            for call in mod.calls:
                # Determine if call is internal or external
                if call.callee_module:
                    # Try to resolve the callee module
                    target_module = self._resolve_import(call.callee_module, module_paths)
                    if target_module and target_module != module_name:
                        # External call
                        self._call_index[module_name]["outbound"].append({
                            "caller": call.caller,
                            "callee": f"{call.callee_module}.{call.callee}",
                            "target_module": target_module,
                            "line": call.line,
                        })
                    else:
                        # Internal call
                        self._call_index[module_name]["internal"].append({
                            "caller": call.caller,
                            "callee": call.callee,
                            "line": call.line,
                        })
                else:
                    # Direct function call - could be internal or imported
                    self._call_index[module_name]["internal"].append({
                        "caller": call.caller,
                        "callee": call.callee,
                        "line": call.line,
                    })

        # Build inbound references
        for module_name, calls in self._call_index.items():
            for out_call in calls["outbound"]:
                target = out_call.get("target_module")
                if target and target in self._call_index:
                    self._call_index[target]["inbound"].append({
                        "caller_module": module_name,
                        "caller": out_call["caller"],
                        "callee": out_call["callee"],
                    })

    def get_interaction_matrix(self, module_name: str) -> dict:
        """
        Get interaction data for INTERACTION MATRIX generation (V13.0).

        Returns dict with:
        - outbound: List of calls made to other modules
        - inbound: List of calls received from other modules
        - internal: List of internal calls within the module
        """
        return self._call_index.get(module_name, {
            "outbound": [],
            "inbound": [],
            "internal": [],
        })

    def _path_to_module_name(self, path: Path) -> str:
        """Convert file path to module name."""
        # Remove .py extension
        parts = list(path.parts)
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        # Handle __init__.py -> use parent
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]

        return ".".join(parts)

    def _resolve_import(
        self,
        import_name: str,
        module_paths: dict[str, ModuleInfo]
    ) -> Optional[str]:
        """Resolve an import to a module name in our graph."""
        # Direct match
        if import_name in module_paths:
            return import_name

        # Try prefixes (e.g., 'core.fsm' for 'core.fsm.states')
        parts = import_name.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in module_paths:
                return prefix

        return None

    def get_internal_dependencies(self, module_name: str, graph) -> list[str]:
        """Get internal dependencies for a module."""
        return list(graph.successors(module_name))

    def get_dependents(self, module_name: str, graph) -> list[str]:
        """Get modules that depend on this module."""
        return list(graph.predecessors(module_name))

    def get_external_dependencies(self, modules: list[ModuleInfo]) -> set[str]:
        """Get all external (non-project) dependencies."""
        external = set()

        for mod in modules:
            for imp in mod.imports:
                # Check if it's an external import
                if not self._is_internal_import(imp.module):
                    # Get top-level package
                    top_level = imp.module.split(".")[0]
                    external.add(top_level)

        return external

    def _is_internal_import(self, module_name: str) -> bool:
        """Check if import is internal to the project."""
        internal_prefixes = ["core", "tools", "tests", "interface", "prompts"]
        return any(module_name.startswith(p) for p in internal_prefixes)

    def to_mermaid(self, graph, max_nodes: int = 50) -> str:
        """
        Convert graph to Mermaid flowchart syntax.

        Args:
            graph: The dependency graph
            max_nodes: Maximum number of nodes to include

        Returns:
            Mermaid flowchart string
        """
        lines = ["flowchart LR"]

        nodes = list(graph.nodes())[:max_nodes]
        edges = [(e[0], e[1]) for e in graph.edges()
                 if e[0] in nodes and e[1] in nodes]

        # Add nodes with shortened names
        for node in nodes:
            short_name = node.split(".")[-1]
            safe_id = node.replace(".", "_")
            lines.append(f"    {safe_id}[{short_name}]")

        # Add edges
        for from_node, to_node in edges:
            from_id = from_node.replace(".", "_")
            to_id = to_node.replace(".", "_")
            lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def get_clusters(self, graph) -> dict[str, list[str]]:
        """
        Group modules by top-level package.

        Returns dict mapping package name to list of module names.
        """
        clusters = {}

        for node in graph.nodes():
            parts = node.split(".")
            if parts:
                package = parts[0]
                if package not in clusters:
                    clusters[package] = []
                clusters[package].append(node)

        return clusters

    def calculate_metrics(self, graph) -> dict:
        """Calculate graph metrics."""
        metrics = {
            "total_modules": graph.number_of_nodes(),
            "total_dependencies": graph.number_of_edges(),
        }

        if graph.number_of_nodes() > 0:
            # Calculate average dependencies per module
            metrics["avg_dependencies"] = (
                graph.number_of_edges() / graph.number_of_nodes()
            )

            # Find most connected modules
            connection_counts = []
            for node in graph.nodes():
                in_count = len(list(graph.predecessors(node)))
                out_count = len(list(graph.successors(node)))
                connection_counts.append((node, in_count, out_count))

            # Sort by total connections
            connection_counts.sort(key=lambda x: x[1] + x[2], reverse=True)
            metrics["most_connected"] = connection_counts[:5]

        return metrics
