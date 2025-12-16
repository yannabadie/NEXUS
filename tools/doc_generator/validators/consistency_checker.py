# NEXUS Documentation Generator - Consistency Checker
"""
Checks for code consistency issues like dead imports, missing docs, etc.
"""

from pathlib import Path

from ..config import DocGeneratorConfig, ModuleInfo, Issue, Severity, IssueCategory


class ConsistencyChecker:
    """Checks for consistency issues in code."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def check(self, modules: list[ModuleInfo]) -> list[Issue]:
        """
        Run all consistency checks.

        Args:
            modules: List of analyzed modules

        Returns:
            List of issues found
        """
        issues = []

        # Build module index for import checking
        module_index = self._build_module_index(modules)

        for module in modules:
            issues.extend(self._check_dead_imports(module, module_index))
            issues.extend(self._check_missing_docs(module))
            issues.extend(self._check_type_hints(module))

        return issues

    def _build_module_index(self, modules: list[ModuleInfo]) -> set[str]:
        """Build index of available module names."""
        index = set()

        for module in modules:
            # Add full path as module name
            parts = list(module.path.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            if parts[-1] == "__init__":
                parts = parts[:-1]

            module_name = ".".join(parts)
            index.add(module_name)

            # Add all prefixes
            for i in range(1, len(parts) + 1):
                index.add(".".join(parts[:i]))

        return index

    def _check_dead_imports(
        self,
        module: ModuleInfo,
        module_index: set[str]
    ) -> list[Issue]:
        """Check for imports that don't resolve."""
        issues = []

        for imp in module.imports:
            # Only check internal imports
            if not self._is_internal_import(imp.module):
                continue

            # Check if module exists
            if not self._import_exists(imp.module, module_index):
                issues.append(Issue(
                    file=str(module.path),
                    line=imp.line,
                    category=IssueCategory.DEAD_IMPORT,
                    severity=Severity.MEDIUM,
                    message=f"Import '{imp.module}' may not exist",
                    suggestion=f"Verify that module '{imp.module}' exists or remove unused import",
                ))

        return issues

    def _is_internal_import(self, module_name: str) -> bool:
        """Check if import is internal to the project."""
        internal_prefixes = ["core", "tools", "tests", "interface", "prompts"]
        return any(module_name.startswith(p) for p in internal_prefixes)

    def _import_exists(self, module_name: str, module_index: set[str]) -> bool:
        """Check if import target exists in module index."""
        if module_name in module_index:
            return True

        # Check if any module starts with this name (package import)
        return any(m.startswith(module_name + ".") for m in module_index)

    def _check_missing_docs(self, module: ModuleInfo) -> list[Issue]:
        """Check for missing docstrings on public APIs."""
        issues = []

        # Check module docstring
        if not module.docstring:
            issues.append(Issue(
                file=str(module.path),
                line=1,
                category=IssueCategory.MISSING_DOC,
                severity=Severity.LOW,
                message=f"Module '{module.name}' has no docstring",
                suggestion="Add a module-level docstring describing purpose",
            ))

        # Check classes
        for cls in module.classes:
            if cls.name.startswith("_"):
                continue

            if not cls.docstring:
                issues.append(Issue(
                    file=str(module.path),
                    line=cls.line,
                    category=IssueCategory.MISSING_DOC,
                    severity=Severity.LOW,
                    message=f"Class '{cls.name}' has no docstring",
                    suggestion=f"Add a docstring to class '{cls.name}'",
                ))

            # Check public methods
            for method in cls.methods:
                if method.name.startswith("_") and method.name != "__init__":
                    continue

                if not method.docstring and len(method.signature) > 30:
                    # Only flag complex methods
                    issues.append(Issue(
                        file=str(module.path),
                        line=method.line,
                        category=IssueCategory.MISSING_DOC,
                        severity=Severity.INFO,
                        message=f"Method '{cls.name}.{method.name}' has no docstring",
                        suggestion=f"Consider adding a docstring for complex method",
                    ))

        # Check public functions
        for func in module.functions:
            if func.name.startswith("_"):
                continue

            if not func.docstring and len(func.signature) > 30:
                issues.append(Issue(
                    file=str(module.path),
                    line=func.line,
                    category=IssueCategory.MISSING_DOC,
                    severity=Severity.INFO,
                    message=f"Function '{func.name}' has no docstring",
                    suggestion=f"Consider adding a docstring",
                ))

        return issues

    def _check_type_hints(self, module: ModuleInfo) -> list[Issue]:
        """Check for missing type hints on public APIs."""
        issues = []

        for func in module.functions:
            if func.name.startswith("_"):
                continue

            # Check if return type is missing
            if " -> " not in func.signature:
                issues.append(Issue(
                    file=str(module.path),
                    line=func.line,
                    category=IssueCategory.TYPE_ERROR,
                    severity=Severity.INFO,
                    message=f"Function '{func.name}' has no return type hint",
                    suggestion="Add return type annotation",
                ))

        for cls in module.classes:
            if cls.name.startswith("_"):
                continue

            for method in cls.methods:
                if method.name.startswith("_") and method.name not in ("__init__", "__call__"):
                    continue

                # Skip __init__ return type (always None)
                if method.name == "__init__":
                    continue

                if " -> " not in method.signature:
                    issues.append(Issue(
                        file=str(module.path),
                        line=method.line,
                        category=IssueCategory.TYPE_ERROR,
                        severity=Severity.INFO,
                        message=f"Method '{cls.name}.{method.name}' has no return type hint",
                        suggestion="Add return type annotation",
                    ))

        return issues
