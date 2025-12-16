# NEXUS Documentation Generator - README Generator
"""
Generates README.md files using Jinja2 templates.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, FolderInfo, ModuleInfo
from .mermaid_generator import MermaidGenerator

# Try to import jinja2, fall back to simple string formatting
try:
    from jinja2 import Environment, FileSystemLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


class ReadmeGenerator:
    """Generates README.md files for folders."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config
        self.mermaid_gen = MermaidGenerator(config)

        if HAS_JINJA2 and config.templates_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(config.templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.env = None

    def generate_for_folder(
        self,
        folder: FolderInfo,
        all_modules: list[ModuleInfo],
        dep_graph
    ) -> None:
        """
        Generate README.md for a folder.

        Args:
            folder: FolderInfo for the folder
            all_modules: All analyzed modules
            dep_graph: Dependency graph
        """
        # Find modules in this folder
        folder_modules = [
            m for m in all_modules
            if self._module_in_folder(m, folder.path)
        ]

        if not folder_modules and not folder.subfolders:
            return

        # Determine if this is a package or a single-file folder
        is_package = folder.is_python_package

        if is_package:
            content = self._generate_package_readme(folder, folder_modules, dep_graph)
        else:
            content = self._generate_simple_readme(folder, folder_modules)

        # Write README
        readme_path = self.config.repo_root / folder.path / "README.md"
        readme_path.write_text(content, encoding="utf-8")

    def _module_in_folder(self, module: ModuleInfo, folder_path: Path) -> bool:
        """Check if module is in the given folder."""
        try:
            module_folder = module.path.parent
            rel_folder = folder_path.relative_to(self.config.repo_root)
            return str(module_folder) == str(rel_folder)
        except ValueError:
            return str(module.path.parent) == str(folder_path.name)

    def _generate_package_readme(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo],
        dep_graph
    ) -> str:
        """Generate README for a Python package."""
        # Get package docstring from __init__.py
        init_module = next(
            (m for m in modules if m.name == "__init__"),
            None
        )
        docstring = init_module.docstring if init_module else None

        # Collect statistics
        total_loc = sum(m.loc for m in modules)
        total_classes = sum(m.class_count for m in modules)
        total_functions = sum(m.function_count for m in modules)

        # Collect all classes for diagram
        all_classes = []
        for m in modules:
            all_classes.extend(m.classes)

        # Generate class diagram
        class_diagram = None
        if all_classes:
            class_diagram = self.mermaid_gen.class_diagram(all_classes[:15])

        # Build content
        if self.env:
            return self._render_template("readme_package.md.j2", {
                "package": {
                    "name": folder.name,
                    "path": folder.path,
                    "docstring": docstring,
                    "module_count": len(modules),
                    "total_loc": total_loc,
                    "total_classes": total_classes,
                    "total_functions": total_functions,
                },
                "modules": [
                    {
                        "name": m.name,
                        "readme_path": f"{m.name}.py",
                        "summary": self._get_summary(m.docstring),
                        "class_count": m.class_count,
                        "function_count": m.function_count,
                    }
                    for m in modules if m.name != "__init__"
                ],
                "subpackages": [
                    {
                        "name": sp.name,
                        "path": sp,
                        "summary": "",
                        "module_count": 0,
                    }
                    for sp in folder.subfolders
                ],
                "architecture_diagram": class_diagram,
                "version": "1.0.0",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        else:
            return self._generate_simple_package_readme(
                folder, modules, docstring, total_loc, total_classes,
                total_functions, class_diagram
            )

    def _generate_simple_readme(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo]
    ) -> str:
        """Generate a simple README for non-package folders."""
        lines = [f"# {folder.name}", ""]

        if folder.python_files:
            lines.append("## Python Files")
            lines.append("")
            for f in folder.python_files:
                lines.append(f"- `{f.name}`")
            lines.append("")

        if folder.typescript_files:
            lines.append("## TypeScript Files")
            lines.append("")
            for f in folder.typescript_files:
                lines.append(f"- `{f.name}`")
            lines.append("")

        if folder.subfolders:
            lines.append("## Subdirectories")
            lines.append("")
            for sf in folder.subfolders:
                lines.append(f"- [{sf.name}/]({sf.name}/)")
            lines.append("")

        lines.append("---")
        lines.append(f"*Auto-generated by nexus-doc-generator - {datetime.now().strftime('%Y-%m-%d')}*")

        return "\n".join(lines)

    def _generate_simple_package_readme(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo],
        docstring: Optional[str],
        total_loc: int,
        total_classes: int,
        total_functions: int,
        class_diagram: Optional[str]
    ) -> str:
        """Generate package README without Jinja2."""
        lines = [f"# {folder.name}", ""]

        if docstring:
            lines.append(docstring)
            lines.append("")

        lines.append("## Overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| **Path** | `{folder.path}` |")
        lines.append(f"| **Modules** | {len(modules)} |")
        lines.append(f"| **Lines of Code** | {total_loc} |")
        lines.append(f"| **Classes** | {total_classes} |")
        lines.append(f"| **Functions** | {total_functions} |")
        lines.append("")

        if class_diagram:
            lines.append("## Architecture")
            lines.append("")
            lines.append("```mermaid")
            lines.append(class_diagram)
            lines.append("```")
            lines.append("")

        if modules:
            lines.append("## Modules")
            lines.append("")
            lines.append("| Module | Description | Classes | Functions |")
            lines.append("|--------|-------------|---------|-----------|")
            for m in modules:
                if m.name != "__init__":
                    summary = self._get_summary(m.docstring) or "_No description_"
                    lines.append(f"| `{m.name}` | {summary} | {m.class_count} | {m.function_count} |")
            lines.append("")

        if folder.subfolders:
            lines.append("## Subpackages")
            lines.append("")
            for sf in folder.subfolders:
                lines.append(f"- [{sf.name}/]({sf.name}/README.md)")
            lines.append("")

        lines.append("---")
        lines.append(f"*Auto-generated by nexus-doc-generator - {datetime.now().strftime('%Y-%m-%d')}*")

        return "\n".join(lines)

    def _get_summary(self, docstring: Optional[str]) -> str:
        """Get first line of docstring as summary."""
        if not docstring:
            return ""
        lines = docstring.strip().split("\n")
        return lines[0].strip() if lines else ""

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render a Jinja2 template."""
        if self.env:
            template = self.env.get_template(template_name)
            return template.render(**context)
        return ""
