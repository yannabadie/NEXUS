# NEXUS Documentation Generator - Mermaid Generator
"""
Generates Mermaid diagrams from code analysis.
"""

from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, ModuleInfo, ClassInfo


class MermaidGenerator:
    """Generates Mermaid diagrams from code analysis."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def generate_all(self, modules: list[ModuleInfo], dep_graph) -> None:
        """Generate all Mermaid diagrams."""
        output_dir = self.config.mermaid_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate class diagrams
        class_diagram = self.class_diagram_from_modules(modules)
        (output_dir / "CLASS_DIAGRAMS.md").write_text(
            f"# NEXUS Class Diagrams\n\n```mermaid\n{class_diagram}\n```\n",
            encoding="utf-8"
        )

        # Generate dependency graph
        from ..analyzer.dependency_graph import DependencyGraphBuilder
        builder = DependencyGraphBuilder(self.config)
        dep_mermaid = builder.to_mermaid(dep_graph)
        (output_dir / "DEPENDENCY_GRAPH.md").write_text(
            f"# NEXUS Dependency Graph\n\n```mermaid\n{dep_mermaid}\n```\n",
            encoding="utf-8"
        )

    def class_diagram(self, classes: list[ClassInfo]) -> str:
        """
        Generate a Mermaid class diagram.

        Args:
            classes: List of ClassInfo objects

        Returns:
            Mermaid class diagram string
        """
        lines = ["classDiagram"]

        for cls in classes:
            # Class definition
            lines.append(f"    class {cls.name} {{")

            # Attributes
            for attr in cls.attributes:
                visibility = attr.get("visibility", "+")
                type_hint = attr.get("type", "")
                name = attr.get("name", "")
                if type_hint:
                    lines.append(f"        {visibility}{type_hint} {name}")
                else:
                    lines.append(f"        {visibility}{name}")

            # Methods
            for method in cls.methods:
                visibility = "+" if not method.name.startswith("_") else "-"
                # Simplify signature
                sig = method.signature
                if " -> " in sig:
                    sig, ret = sig.rsplit(" -> ", 1)
                    lines.append(f"        {visibility}{sig} {ret}")
                else:
                    lines.append(f"        {visibility}{sig}")

            lines.append("    }")

            # Inheritance relationships
            for base in cls.bases:
                if base not in ("object", "ABC"):
                    lines.append(f"    {base} <|-- {cls.name}")

        return "\n".join(lines)

    def class_diagram_from_modules(
        self,
        modules: list[ModuleInfo],
        max_classes: int = 30
    ) -> str:
        """Generate class diagram from multiple modules."""
        all_classes = []
        for mod in modules:
            for cls in mod.classes:
                if not cls.name.startswith("_"):
                    all_classes.append(cls)

        # Limit to most important classes
        all_classes = all_classes[:max_classes]

        return self.class_diagram(all_classes)

    def flowchart(
        self,
        nodes: list[dict],
        edges: list[dict],
        direction: str = "TB"
    ) -> str:
        """
        Generate a Mermaid flowchart.

        Args:
            nodes: List of dicts with 'id', 'label', 'shape' keys
            edges: List of dicts with 'from', 'to', 'label' keys
            direction: Flow direction (TB, BT, LR, RL)

        Returns:
            Mermaid flowchart string
        """
        lines = [f"flowchart {direction}"]

        # Add nodes
        for node in nodes:
            node_id = node["id"]
            label = node.get("label", node_id)
            shape = node.get("shape", "box")

            if shape == "round":
                lines.append(f"    {node_id}({label})")
            elif shape == "diamond":
                lines.append(f"    {node_id}{{{label}}}")
            elif shape == "stadium":
                lines.append(f"    {node_id}([{label}])")
            else:
                lines.append(f"    {node_id}[{label}]")

        # Add edges
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            style = edge.get("style", "solid")

            if style == "dotted":
                arrow = "-..->"
            elif style == "thick":
                arrow = "==>"
            else:
                arrow = "-->"

            if label:
                lines.append(f"    {from_id} {arrow}|{label}| {to_id}")
            else:
                lines.append(f"    {from_id} {arrow} {to_id}")

        return "\n".join(lines)

    def sequence_diagram(
        self,
        participants: list[dict],
        steps: list[dict]
    ) -> str:
        """
        Generate a Mermaid sequence diagram.

        Args:
            participants: List of dicts with 'id', 'alias' keys
            steps: List of dicts with 'type', 'from', 'to', 'label' keys

        Returns:
            Mermaid sequence diagram string
        """
        lines = ["sequenceDiagram"]

        # Add participants
        for p in participants:
            if p.get("alias"):
                lines.append(f"    participant {p['id']} as {p['alias']}")
            else:
                lines.append(f"    participant {p['id']}")

        # Add steps
        for step in steps:
            step_type = step.get("type", "message")

            if step_type == "message":
                from_id = step["from"]
                to_id = step["to"]
                label = step.get("label", "")
                style = step.get("style", "sync")

                if style == "async":
                    arrow = "->>"
                elif style == "reply":
                    arrow = "-->>"
                else:
                    arrow = "->>"

                lines.append(f"    {from_id} {arrow} {to_id}: {label}")

            elif step_type == "note":
                target = step["target"]
                text = step["text"]
                position = step.get("position", "over")
                lines.append(f"    Note {position} {target}: {text}")

            elif step_type == "activate":
                lines.append(f"    activate {step['target']}")

            elif step_type == "deactivate":
                lines.append(f"    deactivate {step['target']}")

        return "\n".join(lines)

    def state_diagram(
        self,
        states: list[dict],
        transitions: list[dict]
    ) -> str:
        """
        Generate a Mermaid state diagram.

        Args:
            states: List of dicts with 'id', 'label' keys
            transitions: List of dicts with 'from', 'to', 'label' keys

        Returns:
            Mermaid state diagram string
        """
        lines = ["stateDiagram-v2"]

        # Add states
        for state in states:
            state_id = state["id"]
            label = state.get("label", state_id)
            if label != state_id:
                lines.append(f"    {state_id}: {label}")

        # Add transitions
        for trans in transitions:
            from_id = trans["from"]
            to_id = trans["to"]
            label = trans.get("label", "")

            if label:
                lines.append(f"    {from_id} --> {to_id}: {label}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def module_diagram(self, folder_path: Path, modules: list[ModuleInfo]) -> str:
        """
        Generate a diagram showing module structure of a folder.

        Args:
            folder_path: Path to the folder
            modules: List of modules in the folder

        Returns:
            Mermaid flowchart string
        """
        nodes = []
        edges = []

        # Add package node
        package_name = folder_path.name
        nodes.append({
            "id": "pkg",
            "label": package_name,
            "shape": "stadium"
        })

        # Add module nodes
        for i, mod in enumerate(modules):
            mod_id = f"mod_{i}"
            nodes.append({
                "id": mod_id,
                "label": mod.name,
                "shape": "box"
            })
            edges.append({
                "from": "pkg",
                "to": mod_id
            })

        return self.flowchart(nodes, edges, direction="TB")

    def generate_for_folder(
        self,
        folder_path: Path,
        classes: list[ClassInfo]
    ) -> Optional[str]:
        """Generate class diagram for a specific folder."""
        if not classes:
            return None

        return self.class_diagram(classes[:15])  # Limit to 15 classes
