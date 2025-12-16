# NEXUS Documentation Generator - Dead Code Detector
"""
Detects potentially unused code (functions, classes, imports).
"""

import ast
import re
from pathlib import Path

from ..config import DocGeneratorConfig, ModuleInfo, Issue, Severity, IssueCategory


class DeadCodeDetector:
    """Detects potentially unused code."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def detect(self, modules: list[ModuleInfo]) -> list[Issue]:
        """
        Detect potentially unused code.

        Args:
            modules: List of analyzed modules

        Returns:
            List of issues for potentially dead code
        """
        issues = []

        # Build usage index
        usage_index = self._build_usage_index(modules)

        for module in modules:
            issues.extend(self._check_unused_functions(module, usage_index))
            issues.extend(self._check_unused_classes(module, usage_index))
            issues.extend(self._check_unused_imports(module))

        return issues

    def _build_usage_index(self, modules: list[ModuleInfo]) -> dict[str, int]:
        """
        Build index of name usage counts across all modules.

        Returns dict mapping name to usage count.
        """
        usage = {}

        for module in modules:
            # Count usages in imports
            for imp in module.imports:
                for name in imp.names:
                    usage[name] = usage.get(name, 0) + 1

            # Count class usages (in bases)
            for cls in module.classes:
                for base in cls.bases:
                    usage[base] = usage.get(base, 0) + 1

        return usage

    def _check_unused_functions(
        self,
        module: ModuleInfo,
        usage_index: dict[str, int]
    ) -> list[Issue]:
        """Check for potentially unused functions."""
        issues = []

        for func in module.functions:
            # Skip private functions
            if func.name.startswith("_"):
                continue

            # Skip common entry points
            if func.name in ("main", "run", "execute", "setup", "teardown"):
                continue

            # Skip if used somewhere
            if usage_index.get(func.name, 0) > 0:
                continue

            # Skip decorated functions (may be called by framework)
            if func.decorators:
                continue

            issues.append(Issue(
                file=str(module.path),
                line=func.line,
                category=IssueCategory.DEAD_CODE,
                severity=Severity.LOW,
                message=f"Function '{func.name}' may be unused",
                context=func.signature,
                suggestion="Verify if this function is still needed or remove it",
            ))

        return issues

    def _check_unused_classes(
        self,
        module: ModuleInfo,
        usage_index: dict[str, int]
    ) -> list[Issue]:
        """Check for potentially unused classes."""
        issues = []

        for cls in module.classes:
            # Skip private classes
            if cls.name.startswith("_"):
                continue

            # Skip if used as base class
            if usage_index.get(cls.name, 0) > 0:
                continue

            # Skip certain patterns (Exception classes, etc.)
            if cls.name.endswith("Exception") or cls.name.endswith("Error"):
                continue

            # Skip decorated classes
            if cls.decorators:
                continue

            issues.append(Issue(
                file=str(module.path),
                line=cls.line,
                category=IssueCategory.DEAD_CODE,
                severity=Severity.LOW,
                message=f"Class '{cls.name}' may be unused",
                suggestion="Verify if this class is still needed or remove it",
            ))

        return issues

    def _check_unused_imports(self, module: ModuleInfo) -> list[Issue]:
        """
        Check for imports that may be unused within the module.

        This is a simple heuristic check, not a full static analysis.
        """
        issues = []

        # Read module source to check for name usage
        try:
            source_path = self.config.repo_root / module.path
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return issues

        for imp in module.imports:
            for name in imp.names:
                # Skip wildcard imports
                if name == "*":
                    continue

                # Skip __all__ entries
                if name.startswith("__"):
                    continue

                # Count occurrences in source (excluding the import line)
                # This is a rough heuristic
                pattern = rf'\b{re.escape(name)}\b'
                matches = list(re.finditer(pattern, source))

                # Should appear at least twice (import + usage)
                if len(matches) < 2:
                    issues.append(Issue(
                        file=str(module.path),
                        line=imp.line,
                        category=IssueCategory.DEAD_IMPORT,
                        severity=Severity.LOW,
                        message=f"Import '{name}' from '{imp.module}' may be unused",
                        suggestion=f"Remove if not needed: from {imp.module} import {name}",
                    ))

        return issues

    def find_orphan_files(self, modules: list[ModuleInfo]) -> list[Issue]:
        """
        Find Python files that are never imported.

        These might be orphaned or entry-point scripts.
        """
        issues = []

        # Build set of imported modules
        imported = set()
        for module in modules:
            for imp in module.imports:
                imported.add(imp.module)
                # Add submodule imports
                parts = imp.module.split(".")
                for i in range(1, len(parts) + 1):
                    imported.add(".".join(parts[:i]))

        # Check each module
        for module in modules:
            # Convert path to module name
            parts = list(module.path.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]

            module_name = ".".join(parts)

            # Skip __init__ files
            if module.name == "__init__":
                continue

            # Skip test files
            if "test" in module_name.lower():
                continue

            # Skip entry points
            if module.name in ("__main__", "main", "cli", "app"):
                continue

            # Check if imported anywhere
            if module_name not in imported:
                issues.append(Issue(
                    file=str(module.path),
                    line=1,
                    category=IssueCategory.DEAD_CODE,
                    severity=Severity.INFO,
                    message=f"Module '{module.name}' is never imported",
                    suggestion="This may be an entry point or orphaned code",
                ))

        return issues
