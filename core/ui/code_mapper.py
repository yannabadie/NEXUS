import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any

class CodeMapper:
    """
    Analyzes the codebase to build a dependency graph (Neural Code Map).
    """
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.nodes: Set[str] = set()
        self.edges: List[Dict[str, str]] = []

    def scan(self) -> Dict[str, Any]:
        """
        Scan the codebase and return the dependency graph.
        """
        self.nodes.clear()
        self.edges.clear()

        # Walk through all python files
        for root, _, files in os.walk(self.root):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    self._analyze_file(file_path)

        return {
            "nodes": list(self.nodes),
            "edges": self.edges
        }

    def _analyze_file(self, file_path: Path):
        """
        Parse a single file to find imports.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            # Module name from path (e.g., core/ui/code_mapper.py -> core.ui.code_mapper)
            try:
                rel_path = file_path.relative_to(self.root)
                module_name = str(rel_path).replace(os.sep, ".").replace(".py", "")
            except ValueError:
                return # Outside root

            self.nodes.add(module_name)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_edge(module_name, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_edge(module_name, node.module)

        except Exception:
            pass # Skip errors (syntax errors, etc.)

    def _add_edge(self, source: str, target: str):
        """
        Add a dependency edge.
        """
        # Filter out external libs (simple heuristic: if it starts with known internal prefixes)
        # For NEXUS, internal modules start with 'core', 'tests', 'nexus7'
        is_internal = any(target.startswith(p) for p in ["core", "tests", "nexus7"])
        
        if is_internal:
            self.nodes.add(target)
            self.edges.append({"source": source, "target": target})

# Global instance
code_mapper = CodeMapper()
