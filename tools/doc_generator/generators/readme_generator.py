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
        # Build relative path for protection check
        readme_rel_path = str(folder.path / "README.md").replace("\\", "/")
        if readme_rel_path.startswith("./"):
            readme_rel_path = readme_rel_path[2:]

        # V13.0: Check protected READMEs
        if self.config.respect_protected:
            # Full protection - never touch these files
            if readme_rel_path in self.config.protected_readmes:
                if self.config.verbose:
                    print(f"  [PROTECTED] Skipping {readme_rel_path}")
                return

        # Find modules in this folder
        folder_modules = [
            m for m in all_modules
            if self._module_in_folder(m, folder.path)
        ]

        if not folder_modules and not folder.subfolders:
            return

        # Determine if this is a package or a single-file folder
        is_package = folder.is_python_package

        # V13.0: Check preserve header READMEs
        readme_path = self.config.repo_root / folder.path / "README.md"
        if (self.config.respect_protected and
            readme_rel_path in self.config.preserve_header_readmes and
            readme_path.exists()):
            # Preserve existing header, only update stats section
            existing_content = readme_path.read_text(encoding="utf-8")
            header = self._extract_header(existing_content)
            if header:
                stats = self._generate_stats_only(folder, folder_modules)
                content = header + "\n\n---\n\n## Auto-Generated Statistics\n\n" + stats
                if self.config.verbose:
                    print(f"  [PRESERVE HEADER] Updating stats only for {readme_rel_path}")
            else:
                # No header found, generate normally
                if is_package:
                    content = self._generate_package_readme(folder, folder_modules, dep_graph)
                else:
                    content = self._generate_simple_readme(folder, folder_modules)
        else:
            if is_package:
                content = self._generate_package_readme(folder, folder_modules, dep_graph)
            else:
                content = self._generate_simple_readme(folder, folder_modules)

        # Write README
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
                total_functions, class_diagram, dep_graph
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
        class_diagram: Optional[str],
        dep_graph=None
    ) -> str:
        """
        Generate package README without Jinja2.

        V13.0: Now follows the documentation prompt structure:
        - SYNOPSIS
        - COMPONENT MAP (Mermaid)
        - INTERACTION MATRIX
        - HIERARCHY
        """
        lines = [f"# {folder.name}", ""]

        # =========================================================================
        # SYNOPSIS (V13.0)
        # =========================================================================
        lines.append("## Synopsis")
        lines.append("")
        if docstring:
            lines.append(docstring)
        else:
            lines.append(f"Component located at `{folder.path}`.")
        lines.append("")

        # Quick stats
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| **Modules** | {len(modules)} |")
        lines.append(f"| **Lines of Code** | {total_loc:,} |")
        lines.append(f"| **Classes** | {total_classes} |")
        lines.append(f"| **Functions** | {total_functions} |")
        lines.append("")

        # =========================================================================
        # COMPONENT MAP (Mermaid) - V13.0
        # =========================================================================
        if class_diagram:
            lines.append("## Component Map")
            lines.append("")
            lines.append("```mermaid")
            lines.append(class_diagram)
            lines.append("```")
            lines.append("")

        # =========================================================================
        # INTERACTION MATRIX (V13.0 - NEW)
        # =========================================================================
        lines.append("## Interaction Matrix")
        lines.append("")
        lines.append("| Component/File | Calls (Outbound) | Called By (Inbound) | Data Type |")
        lines.append("|----------------|------------------|---------------------|-----------|")

        for m in modules:
            if m.name == "__init__":
                continue

            # Get interaction data from dependency graph builder
            module_name = str(folder.path / m.name).replace("\\", "/").replace("/", ".")
            if module_name.endswith(".py"):
                module_name = module_name[:-3]

            # Collect outbound/inbound from calls
            outbound_calls = set()
            inbound_calls = set()

            for call in m.calls:
                if call.callee_module:
                    outbound_calls.add(f"{call.callee_module}.{call.callee}")
                else:
                    outbound_calls.add(call.callee)

            # Format for table
            outbound_str = ", ".join(sorted(outbound_calls)[:3])
            if len(outbound_calls) > 3:
                outbound_str += f" (+{len(outbound_calls) - 3})"
            if not outbound_str:
                outbound_str = "-"

            # Inbound would need cross-module analysis (simplified here)
            inbound_str = "-"

            # Data types from imports
            data_types = set()
            for imp in m.imports:
                if imp.is_from and any(n[0].isupper() for n in imp.names):
                    data_types.update(n for n in imp.names if n[0].isupper())
            data_type_str = ", ".join(sorted(data_types)[:3]) if data_types else "-"
            if len(data_types) > 3:
                data_type_str += f" (+{len(data_types) - 3})"

            lines.append(f"| `{m.name}` | {outbound_str} | {inbound_str} | {data_type_str} |")

        lines.append("")

        # =========================================================================
        # HIERARCHY (V13.0 - NEW)
        # =========================================================================
        lines.append("## Hierarchy")
        lines.append("")

        # Parent path
        parent_parts = folder.path.parts[:-1] if folder.path.parts else []
        if parent_parts:
            parent_path = "/".join(parent_parts)
            lines.append(f"**Parent**: [`{parent_path}/`](../README.md)")
        else:
            lines.append("**Parent**: Repository root")
        lines.append("")

        # Current folder
        lines.append(f"**Current**: `{folder.path}/`")
        lines.append("")

        # Subfolders
        if folder.subfolders:
            lines.append("**Children**:")
            for sf in folder.subfolders:
                lines.append(f"- [`{sf.name}/`]({sf.name}/README.md)")
            lines.append("")

        # Module list
        if modules:
            lines.append("**Modules**:")
            lines.append("")
            lines.append("| Module | Description | Classes | Functions |")
            lines.append("|--------|-------------|---------|-----------|")
            for m in sorted(modules, key=lambda x: x.name):
                if m.name != "__init__":
                    summary = self._get_summary(m.docstring) or "_No description_"
                    lines.append(f"| `{m.name}` | {summary} | {m.class_count} | {m.function_count} |")
            lines.append("")

        lines.append("---")
        lines.append(f"*Auto-generated by nexus-doc-generator V13.0 - {datetime.now().strftime('%Y-%m-%d')}*")

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

    def _extract_header(self, content: str) -> Optional[str]:
        """
        Extract the header section from an existing README.

        The header is everything before the first '---' separator
        or before '## Overview' / '## Auto-Generated'.

        Returns None if no clear header is found.
        """
        if not content:
            return None

        lines = content.split("\n")
        header_lines = []

        for i, line in enumerate(lines):
            # Stop at horizontal rule
            if line.strip() == "---":
                break
            # Stop at auto-generated section markers
            if line.startswith("## Overview") or line.startswith("## Auto-Generated"):
                break
            # Stop at Mermaid diagrams (typically auto-generated)
            if line.strip() == "```mermaid":
                break
            header_lines.append(line)

        # Only return header if it has meaningful content
        header = "\n".join(header_lines).strip()
        if header and len(header) > 20:  # At least a title
            return header
        return None

    def _generate_stats_only(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo]
    ) -> str:
        """Generate only the statistics section without header."""
        total_loc = sum(m.loc for m in modules)
        total_classes = sum(m.class_count for m in modules)
        total_functions = sum(m.function_count for m in modules)

        lines = [
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Path** | `{folder.path}` |",
            f"| **Modules** | {len(modules)} |",
            f"| **Lines of Code** | {total_loc:,} |",
            f"| **Classes** | {total_classes} |",
            f"| **Functions** | {total_functions} |",
            "",
        ]

        if modules:
            lines.extend([
                "### Modules",
                "",
                "| Module | Classes | Functions | LOC |",
                "|--------|---------|-----------|-----|",
            ])
            for m in sorted(modules, key=lambda x: x.name):
                if m.name != "__init__":
                    lines.append(f"| `{m.name}` | {m.class_count} | {m.function_count} | {m.loc} |")
            lines.append("")

        lines.append(f"*Updated by nexus-doc-generator - {datetime.now().strftime('%Y-%m-%d')}*")

        return "\n".join(lines)
