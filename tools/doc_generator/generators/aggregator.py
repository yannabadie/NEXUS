# NEXUS Documentation Generator - Document Aggregator
"""
Aggregates documentation from child folders to parent folders.
"""

from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, FolderInfo, ModuleInfo


class DocumentAggregator:
    """Aggregates child documentation into parent documentation."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def aggregate(
        self,
        folders: list[FolderInfo],
        modules: list[ModuleInfo]
    ) -> None:
        """
        Aggregate documentation from children to parents.

        This creates higher-level summaries in parent folders
        based on the documentation of their children.
        """
        # Build folder hierarchy
        hierarchy = self._build_hierarchy(folders)

        # Process from leaves to root
        processed = set()
        for folder in sorted(folders, key=lambda f: len(f.path.parts), reverse=True):
            if str(folder.path) not in processed:
                self._aggregate_folder(folder, hierarchy, modules, processed)
                processed.add(str(folder.path))

    def _build_hierarchy(self, folders: list[FolderInfo]) -> dict[str, FolderInfo]:
        """Build a mapping from path to FolderInfo."""
        return {str(f.path): f for f in folders}

    def _aggregate_folder(
        self,
        folder: FolderInfo,
        hierarchy: dict[str, FolderInfo],
        modules: list[ModuleInfo],
        processed: set[str]
    ) -> None:
        """Aggregate information for a single folder."""
        # Get child folders
        children = []
        for subfolder in folder.subfolders:
            child_key = str(subfolder)
            if child_key in hierarchy:
                children.append(hierarchy[child_key])

        if not children:
            return

        # Calculate aggregated statistics
        total_modules = 0
        total_loc = 0
        total_classes = 0
        total_functions = 0

        for child in children:
            child_modules = self._get_folder_modules(child, modules)
            total_modules += len(child_modules)
            total_loc += sum(m.loc for m in child_modules)
            total_classes += sum(m.class_count for m in child_modules)
            total_functions += sum(m.function_count for m in child_modules)

        # Update or create summary in folder's README
        self._update_folder_summary(
            folder,
            children,
            total_modules,
            total_loc,
            total_classes,
            total_functions,
        )

    def _get_folder_modules(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo]
    ) -> list[ModuleInfo]:
        """Get all modules belonging to a folder and its subfolders."""
        folder_modules = []
        folder_path = str(folder.path)

        for module in modules:
            module_path = str(module.path.parent)
            if module_path.startswith(folder_path):
                folder_modules.append(module)

        return folder_modules

    def _update_folder_summary(
        self,
        folder: FolderInfo,
        children: list[FolderInfo],
        total_modules: int,
        total_loc: int,
        total_classes: int,
        total_functions: int,
    ) -> None:
        """Update folder README with aggregated summary."""
        readme_path = self.config.repo_root / folder.path / "README.md"

        if not readme_path.exists():
            return

        try:
            content = readme_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Check if aggregated stats section exists
        if "## Aggregated Statistics" in content:
            # Update existing section
            lines = content.split("\n")
            new_lines = []
            skip_until_next_section = False

            for line in lines:
                if line.startswith("## Aggregated Statistics"):
                    skip_until_next_section = True
                    new_lines.extend(self._create_stats_section(
                        children, total_modules, total_loc,
                        total_classes, total_functions
                    ))
                elif skip_until_next_section and line.startswith("## "):
                    skip_until_next_section = False
                    new_lines.append(line)
                elif not skip_until_next_section:
                    new_lines.append(line)

            content = "\n".join(new_lines)
        else:
            # Add new section before the footer
            footer_marker = "---\n*Auto-generated"
            if footer_marker in content:
                parts = content.rsplit(footer_marker, 1)
                stats_section = "\n".join(self._create_stats_section(
                    children, total_modules, total_loc,
                    total_classes, total_functions
                ))
                content = parts[0] + stats_section + "\n\n" + footer_marker + parts[1]

        readme_path.write_text(content, encoding="utf-8")

    def _create_stats_section(
        self,
        children: list[FolderInfo],
        total_modules: int,
        total_loc: int,
        total_classes: int,
        total_functions: int,
    ) -> list[str]:
        """Create aggregated statistics section."""
        lines = [
            "## Aggregated Statistics",
            "",
            "Statistics from all subpackages:",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Subpackages | {len(children)} |",
            f"| Total Modules | {total_modules} |",
            f"| Total Lines of Code | {total_loc:,} |",
            f"| Total Classes | {total_classes} |",
            f"| Total Functions | {total_functions} |",
            "",
        ]
        return lines

    def get_folder_summary(
        self,
        folder: FolderInfo,
        modules: list[ModuleInfo]
    ) -> dict:
        """
        Get summary information for a folder.

        Returns dict with statistics and key information.
        """
        folder_modules = self._get_folder_modules(folder, modules)

        # Find key classes (classes with many methods or public APIs)
        key_classes = []
        for module in folder_modules:
            for cls in module.classes:
                if not cls.name.startswith("_"):
                    method_count = len([m for m in cls.methods if not m.name.startswith("_")])
                    if method_count >= 3:
                        key_classes.append({
                            "name": cls.name,
                            "module": module.name,
                            "method_count": method_count,
                        })

        key_classes.sort(key=lambda x: x["method_count"], reverse=True)

        return {
            "path": str(folder.path),
            "name": folder.name,
            "module_count": len(folder_modules),
            "total_loc": sum(m.loc for m in folder_modules),
            "total_classes": sum(m.class_count for m in folder_modules),
            "total_functions": sum(m.function_count for m in folder_modules),
            "key_classes": key_classes[:5],
            "has_readme": folder.has_readme,
            "is_package": folder.is_python_package,
        }
