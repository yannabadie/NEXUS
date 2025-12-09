#!/usr/bin/env python3
"""
NEXUS Documentation Engine V1.0

Unified documentation synchronization system.
Single source of truth: .env (NEXUS_VERSION, NEXUS_CODENAME)

Modes:
    --check      : Read-only audit (CI-safe, returns exit code 1 if issues)
    --sync       : Update version patterns in docs (requires --apply to write)
    --gen-map    : Generate ARCHITECTURE_MAP_GENERATED.md
    --audit      : Check module READMEs exist and are up-to-date
    --full       : All of the above

Safety:
    - Idempotent (same result if run multiple times)
    - Minimal changes (only version patterns, never content)
    - Dry-run by default (--apply to actually write)
    - All changes logged with before/after

Usage:
    python scripts/doc_engine.py --check              # CI: verify consistency
    python scripts/doc_engine.py --sync               # Show what would change
    python scripts/doc_engine.py --sync --apply       # Actually update files
    python scripts/doc_engine.py --gen-map --apply    # Generate architecture map
    python scripts/doc_engine.py --full --apply       # Everything

Exit Codes:
    0: Success (or dry-run complete)
    1: Issues found (--check mode)
    2: Error during execution
"""

import os
import re
import sys
import ast
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Issue:
    """Documentation issue found during check."""
    severity: str  # ERROR, WARNING, INFO
    file: str
    message: str
    current: str = ""
    expected: str = ""

    def __str__(self):
        result = f"[{self.severity}] {self.file}: {self.message}"
        if self.current and self.expected:
            result += f"\n  Current:  {self.current}\n  Expected: {self.expected}"
        return result


@dataclass
class Change:
    """A change to be applied to a file."""
    file: str
    pattern: str
    old_value: str
    new_value: str
    line_number: int = 0

    def __str__(self):
        return f"{self.file}:{self.line_number} | '{self.old_value}' -> '{self.new_value}'"


@dataclass
class ClassInfo:
    """Information about a Python class."""
    name: str
    file_path: str
    line_number: int
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_enum: bool = False


@dataclass
class FunctionInfo:
    """Information about a Python function."""
    name: str
    file_path: str
    line_number: int
    is_async: bool = False
    docstring: Optional[str] = None


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    lines_of_code: int = 0


@dataclass
class ComponentInfo:
    """Information about a logical component (directory)."""
    name: str
    path: str
    modules: List[ModuleInfo] = field(default_factory=list)
    total_loc: int = 0
    total_classes: int = 0
    total_functions: int = 0


# =============================================================================
# DOCUMENTATION ENGINE
# =============================================================================

class DocEngine:
    """
    Unified documentation synchronization engine.

    Design Principles:
    1. Single Source of Truth: .env (NEXUS_VERSION, NEXUS_CODENAME)
    2. Minimal Changes: Only version patterns, never content
    3. Idempotent: Same result if run multiple times
    4. Fail-Safe: Pattern not found = WARNING, not ERROR
    5. Visible: All changes logged with before/after
    """

    # Files to synchronize
    SYNC_FILES = {
        "README.md": [
            # Title: NEXUS V7.8 "HIVE MIND" -> NEXUS V8.3.2 "TRUE HIVE MIND"
            (r'NEXUS V[\d.]+\s*"[^"]*"', 'NEXUS V{version} "{codename}"'),
            # Badge: Version-7.8.0-blue -> Version-8.3.2-blue
            (r'Version-[\d.]+-blue', 'Version-{version}-blue'),
            # Section: ## V7.8 Features -> ## V8.3 Features
            (r'## V[\d.]+ Features', '## V{major_minor} Features'),
            # Architecture header
            (r'NEXUS V[\d.]+ HIVE MIND', 'NEXUS V{major_minor} {codename}'),
            # Architecture section title
            (r'## Architecture \(V[\d.]+\)', '## Architecture (V{major_minor})'),
        ],
        "CLAUDE.md": [
            # Header version
            (r'\*\*Version\*\*: [\d.]+', '**Version**: {version}'),
            # Title if present
            (r'# NEXUS V[\d.]+', '# NEXUS V{major_minor}'),
        ],
    }

    # Module README patterns (for audit)
    MODULE_README_VERSION_PATTERN = r'NEXUS V[\d.]+\.?x?'

    def __init__(self, project_root: Path):
        self.root = project_root
        self.version = self._read_env_value("NEXUS_VERSION", "0.0.0")
        self.codename = self._read_env_value("NEXUS_CODENAME", "UNKNOWN")
        self.major_minor = ".".join(self.version.split(".")[:2])

        self.issues: List[Issue] = []
        self.changes: List[Change] = []

    def _read_env_value(self, key: str, default: str) -> str:
        """Read a value from .env file."""
        env_path = self.root / ".env"
        if not env_path.exists():
            return default

        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith(f"{key}="):
                value = line.split("=", 1)[1].strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return value
        return default

    def _format_pattern(self, pattern: str) -> str:
        """Format a pattern with version variables."""
        return pattern.format(
            version=self.version,
            codename=self.codename,
            major_minor=self.major_minor
        )

    # =========================================================================
    # MODE: CHECK
    # =========================================================================

    def check(self) -> List[Issue]:
        """
        Check documentation consistency (read-only).
        Returns list of issues found.
        """
        self.issues = []

        print(f"\n{'='*60}")
        print(f"NEXUS Documentation Check")
        print(f"Source of Truth: .env -> NEXUS_VERSION={self.version}")
        print(f"{'='*60}\n")

        # Check main documentation files
        for filename, patterns in self.SYNC_FILES.items():
            file_path = self.root / filename
            if not file_path.exists():
                self.issues.append(Issue(
                    severity="ERROR",
                    file=filename,
                    message="File not found"
                ))
                continue

            content = file_path.read_text(encoding="utf-8")

            for pattern, replacement in patterns:
                expected = self._format_pattern(replacement)
                match = re.search(pattern, content)

                if match:
                    current = match.group(0)
                    # Check if it matches expected
                    expected_pattern = self._format_pattern(replacement)
                    # Convert replacement to regex for comparison
                    expected_regex = re.escape(expected_pattern)
                    if not re.match(expected_regex.replace(r'\{', '{').replace(r'\}', '}'), current):
                        self.issues.append(Issue(
                            severity="ERROR",
                            file=filename,
                            message=f"Version mismatch for pattern '{pattern}'",
                            current=current,
                            expected=expected_pattern
                        ))
                else:
                    self.issues.append(Issue(
                        severity="WARNING",
                        file=filename,
                        message=f"Pattern not found: '{pattern}'"
                    ))

        # Check module READMEs
        self._check_module_readmes()

        # Print results
        self._print_check_results()

        return self.issues

    def _check_module_readmes(self):
        """Check that each core/* module has a README."""
        core_path = self.root / "core"
        if not core_path.exists():
            return

        for module_dir in sorted(core_path.iterdir()):
            if not module_dir.is_dir():
                continue
            if module_dir.name.startswith("_"):
                continue

            readme_path = module_dir / "README.md"
            if not readme_path.exists():
                self.issues.append(Issue(
                    severity="WARNING",
                    file=f"core/{module_dir.name}/README.md",
                    message="Missing README.md"
                ))
            else:
                # Check if version is outdated
                content = readme_path.read_text(encoding="utf-8")
                if "V7." in content and "V8" not in content:
                    self.issues.append(Issue(
                        severity="WARNING",
                        file=f"core/{module_dir.name}/README.md",
                        message="May be outdated (references V7 but not V8)"
                    ))

    def _print_check_results(self):
        """Print check results."""
        errors = [i for i in self.issues if i.severity == "ERROR"]
        warnings = [i for i in self.issues if i.severity == "WARNING"]

        if errors:
            print("[ERRORS]")
            for issue in errors:
                print(f"  {issue}")
            print()

        if warnings:
            print("[WARNINGS]")
            for issue in warnings:
                print(f"  {issue}")
            print()

        if not errors and not warnings:
            print("[OK] All documentation is in sync with version {self.version}")
        else:
            print(f"\nSummary: {len(errors)} errors, {len(warnings)} warnings")

    # =========================================================================
    # MODE: SYNC
    # =========================================================================

    def sync(self, apply: bool = False) -> List[Change]:
        """
        Synchronize version patterns in documentation files.

        Args:
            apply: If True, write changes. If False, dry-run.

        Returns:
            List of changes (made or would-be-made).
        """
        self.changes = []

        print(f"\n{'='*60}")
        print(f"NEXUS Documentation Sync {'(DRY RUN)' if not apply else '(APPLYING)'}")
        print(f"Target Version: {self.version} \"{self.codename}\"")
        print(f"{'='*60}\n")

        for filename, patterns in self.SYNC_FILES.items():
            file_path = self.root / filename
            if not file_path.exists():
                print(f"[SKIP] {filename}: File not found")
                continue

            content = file_path.read_text(encoding="utf-8")
            new_content = content
            file_changes = []

            for pattern, replacement in patterns:
                expected = self._format_pattern(replacement)

                def replacer(match):
                    old_value = match.group(0)
                    if old_value != expected:
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        file_changes.append(Change(
                            file=filename,
                            pattern=pattern,
                            old_value=old_value,
                            new_value=expected,
                            line_number=line_num
                        ))
                    return expected

                new_content = re.sub(pattern, replacer, new_content)

            if file_changes:
                print(f"[CHANGES] {filename}:")
                for change in file_changes:
                    print(f"  Line {change.line_number}: '{change.old_value}' -> '{change.new_value}'")
                self.changes.extend(file_changes)

                if apply:
                    file_path.write_text(new_content, encoding="utf-8")
                    print(f"  -> Written!")
            else:
                print(f"[OK] {filename}: Already in sync")

        print(f"\nTotal changes: {len(self.changes)}")
        if not apply and self.changes:
            print("(Use --apply to write changes)")

        return self.changes

    # =========================================================================
    # MODE: GENERATE MAP
    # =========================================================================

    def generate_map(self, output_path: Optional[Path] = None, apply: bool = False) -> str:
        """
        Generate architecture map document.

        This integrates the functionality from generate_architecture_map.py
        """
        if output_path is None:
            output_path = self.root / "docs" / "ARCHITECTURE_MAP_GENERATED.md"

        print(f"\n{'='*60}")
        print(f"NEXUS Architecture Map Generator")
        print(f"{'='*60}\n")

        # Scan codebase
        scanner = CodebaseScanner(self.root)
        components = scanner.scan()

        # Extract structures
        extractor = StructureExtractor(self.root)
        structures = extractor.extract()

        # Generate document
        generator = MapGenerator(
            version=self.version,
            codename=self.codename,
            components=components,
            structures=structures
        )
        content = generator.generate()

        if apply:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"[OK] Generated: {output_path}")
            print(f"     {len(content)} bytes, {content.count(chr(10))} lines")
        else:
            print(f"[DRY RUN] Would generate: {output_path}")
            print(f"          {len(content)} bytes, {content.count(chr(10))} lines")
            print("(Use --apply to write)")

        return content

    # =========================================================================
    # MODE: AUDIT
    # =========================================================================

    def audit(self) -> Dict[str, str]:
        """
        Audit module READMEs for existence and currency.

        Returns:
            Dict mapping module name to status (OK, MISSING, OUTDATED)
        """
        print(f"\n{'='*60}")
        print(f"NEXUS Module README Audit")
        print(f"{'='*60}\n")

        results = {}
        core_path = self.root / "core"

        for module_dir in sorted(core_path.iterdir()):
            if not module_dir.is_dir():
                continue
            if module_dir.name.startswith("_"):
                continue

            readme_path = module_dir / "README.md"
            module_name = module_dir.name

            if not readme_path.exists():
                results[module_name] = "MISSING"
                print(f"[MISSING] core/{module_name}/README.md")
            else:
                content = readme_path.read_text(encoding="utf-8")
                # Check version references
                has_v8 = "V8" in content or "v8" in content
                has_v7_only = ("V7" in content or "v7" in content) and not has_v8

                if has_v7_only:
                    results[module_name] = "OUTDATED"
                    print(f"[OUTDATED] core/{module_name}/README.md (V7 references, no V8)")
                else:
                    results[module_name] = "OK"
                    print(f"[OK] core/{module_name}/README.md")

        # Summary
        ok_count = sum(1 for v in results.values() if v == "OK")
        missing_count = sum(1 for v in results.values() if v == "MISSING")
        outdated_count = sum(1 for v in results.values() if v == "OUTDATED")

        print(f"\nSummary: {ok_count} OK, {missing_count} missing, {outdated_count} outdated")

        return results

    # =========================================================================
    # MODE: FULL
    # =========================================================================

    def full(self, apply: bool = False) -> bool:
        """
        Run all modes: check, sync, gen-map, audit.

        Returns:
            True if all passed, False if issues found.
        """
        print(f"\n{'#'*60}")
        print(f"# NEXUS Documentation Engine - FULL RUN")
        print(f"# Version: {self.version} \"{self.codename}\"")
        print(f"# Apply: {apply}")
        print(f"{'#'*60}")

        # 1. Check
        issues = self.check()
        has_errors = any(i.severity == "ERROR" for i in issues)

        # 2. Sync
        changes = self.sync(apply=apply)

        # 3. Generate map
        self.generate_map(apply=apply)

        # 4. Audit
        audit_results = self.audit()

        # Final summary
        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"  Check:  {len(issues)} issues ({sum(1 for i in issues if i.severity == 'ERROR')} errors)")
        print(f"  Sync:   {len(changes)} changes {'applied' if apply else '(dry run)'}")
        print(f"  Audit:  {sum(1 for v in audit_results.values() if v != 'OK')} modules need attention")

        return not has_errors


# =============================================================================
# CODEBASE SCANNER (from generate_architecture_map.py)
# =============================================================================

class CodebaseScanner:
    """Scans the codebase and extracts structural information."""

    def __init__(self, root: Path):
        self.root = root

    def scan(self) -> List[ComponentInfo]:
        """Scan core/ directory and return component information."""
        components = []
        core_path = self.root / "core"

        if not core_path.exists():
            return components

        for component_dir in sorted(core_path.iterdir()):
            if not component_dir.is_dir():
                continue
            if component_dir.name.startswith("_"):
                continue

            component = self._scan_component(component_dir)
            components.append(component)

        return components

    def _scan_component(self, path: Path) -> ComponentInfo:
        """Scan a single component directory."""
        component = ComponentInfo(
            name=path.name,
            path=str(path.relative_to(self.root))
        )

        for py_file in path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module = self._scan_module(py_file)
            component.modules.append(module)
            component.total_loc += module.lines_of_code
            component.total_classes += len(module.classes)
            component.total_functions += len(module.functions)

        return component

    def _scan_module(self, path: Path) -> ModuleInfo:
        """Scan a single Python module."""
        module = ModuleInfo(path=str(path.relative_to(self.root)))

        try:
            content = path.read_text(encoding="utf-8")
            module.lines_of_code = len(content.splitlines())

            tree = ast.parse(content)
            analyzer = CodeAnalyzer(str(path))
            analyzer.visit(tree)

            module.classes = analyzer.classes
            module.functions = analyzer.functions

        except Exception as e:
            pass  # Skip files that can't be parsed

        return module


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to extract code structure."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[ClassInfo] = []
        self.functions: List[FunctionInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._get_name(b) for b in node.bases]

        # Check if dataclass or enum
        is_dataclass = any(
            self._get_name(d) == "dataclass"
            for d in node.decorator_list
        )
        is_enum = "Enum" in bases or "IntEnum" in bases or "StrEnum" in bases

        methods = [
            n.name for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            bases=bases,
            docstring=ast.get_docstring(node),
            methods=methods,
            is_dataclass=is_dataclass,
            is_enum=is_enum
        )
        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not hasattr(self, '_in_class'):
            self.functions.append(FunctionInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                is_async=False,
                docstring=ast.get_docstring(node)
            ))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if not hasattr(self, '_in_class'):
            self.functions.append(FunctionInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                is_async=True,
                docstring=ast.get_docstring(node)
            ))
        self.generic_visit(node)

    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ""


# =============================================================================
# STRUCTURE EXTRACTOR
# =============================================================================

class StructureExtractor:
    """Extracts high-level structures from the codebase."""

    def __init__(self, root: Path):
        self.root = root

    def extract(self) -> Dict:
        """Extract all structures."""
        return {
            "fsm_states": self._extract_fsm_states(),
            "hive_states": self._extract_hive_states(),
            "swarm_modes": self._extract_swarm_modes(),
            "commands": self._extract_commands(),
            "enums": self._extract_all_enums(),
            "dataclasses": self._extract_all_dataclasses(),
        }

    def _extract_fsm_states(self) -> List[str]:
        """Extract FSM states from states.py."""
        states_file = self.root / "core" / "fsm" / "states.py"
        return self._extract_enum_values(states_file, "OrchestratorState")

    def _extract_hive_states(self) -> List[str]:
        """Extract HiveMind states from types.py."""
        types_file = self.root / "core" / "hive_mind" / "types.py"
        return self._extract_enum_values(types_file, "HiveMindState")

    def _extract_swarm_modes(self) -> List[str]:
        """Extract collaboration modes."""
        modes_file = self.root / "core" / "swarm" / "collaboration_modes.py"
        return self._extract_enum_values(modes_file, "CollaborationMode")

    def _extract_commands(self) -> List[str]:
        """Extract slash commands from REPL."""
        repl_file = self.root / "core" / "interface" / "repl.py"
        commands = []

        if repl_file.exists():
            content = repl_file.read_text(encoding="utf-8")
            # Find command patterns
            pattern = r'elif\s+command\s*==\s*["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)
            commands.extend(matches)

            # Also look for COMMAND_CATEGORIES
            pattern2 = r'"/([^"]+)"'
            matches2 = re.findall(pattern2, content)
            commands.extend(matches2)

        return sorted(set(commands))

    def _extract_enum_values(self, file_path: Path, enum_name: str) -> List[str]:
        """Extract values from an enum class."""
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == enum_name:
                    values = []
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    values.append(target.id)
                    return values
        except Exception:
            pass

        return []

    def _extract_all_enums(self) -> List[str]:
        """Extract all enum names from codebase."""
        enums = []
        for py_file in (self.root / "core").rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = [self._get_base_name(b) for b in node.bases]
                        if any(b in ("Enum", "IntEnum", "StrEnum") for b in bases):
                            enums.append(node.name)
            except Exception:
                pass

        return sorted(set(enums))

    def _extract_all_dataclasses(self) -> List[str]:
        """Extract all dataclass names from codebase."""
        dataclasses = []
        for py_file in (self.root / "core").rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for decorator in node.decorator_list:
                            if self._get_base_name(decorator) == "dataclass":
                                dataclasses.append(node.name)
                                break
            except Exception:
                pass

        return sorted(set(dataclasses))

    def _get_base_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return ""


# =============================================================================
# MAP GENERATOR
# =============================================================================

class MapGenerator:
    """Generates the architecture map document."""

    def __init__(
        self,
        version: str,
        codename: str,
        components: List[ComponentInfo],
        structures: Dict
    ):
        self.version = version
        self.codename = codename
        self.components = components
        self.structures = structures
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.git_commit = self._get_git_commit()

    def _get_git_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def generate(self) -> str:
        """Generate the complete architecture map."""
        sections = [
            self._generate_header(),
            self._generate_overview(),
            self._generate_component_summary(),
            self._generate_fsm_diagram(),
            self._generate_swarm_diagram(),
            self._generate_hive_diagram(),
            self._generate_memory_diagram(),
            self._generate_functional_inventory(),
            self._generate_statistics(),
            self._generate_footer(),
        ]
        return "\n".join(sections)

    def _generate_header(self) -> str:
        return f"""# NEXUS V{self.version} Architecture Map

**Auto-Generated**: {self.timestamp}
**Git Commit**: {self.git_commit}
**Generator**: `scripts/doc_engine.py`

---

> This document is automatically generated by scanning the codebase.
> Re-run the generator after significant changes to keep it updated.

---
"""

    def _generate_overview(self) -> str:
        return """## 1. HIGH-LEVEL OVERVIEW

```mermaid
graph TD
    subgraph Entry["Entry Layer"]
        USER[User Input]
        REPL[REPL<br/>Commands]
    end

    subgraph Core["Orchestration Core"]
        ORCH[OrchestratorV7<br/>FSM]
        SWARM[Swarm Engine<br/>6 modes]
        HIVE[Hive Mind<br/>7 phases]
    end

    subgraph LLM["LLM Drivers"]
        GEMINI[Gemini Driver]
        CLAUDE[Claude Driver]
    end

    subgraph Support["Support Systems"]
        MEM[Memory<br/>RAG + Success]
        SEC[Security<br/>KERNEL + Policy]
        EVOL[Evolution<br/>Spawn + Validate]
        TEL[Telemetry<br/>Budget]
    end

    USER --> REPL
    REPL --> ORCH
    ORCH -->|"MODERATE+"| HIVE
    ORCH -->|"SIMPLE"| SWARM
    HIVE -->|"delegate"| SWARM
    SWARM --> GEMINI
    SWARM --> CLAUDE
    SEC -.->|"validates"| ORCH
    MEM -.->|"boosts"| SWARM
    TEL -.->|"limits"| LLM
    EVOL -.->|"spawns"| SWARM
```
"""

    def _generate_component_summary(self) -> str:
        lines = ["### Component Summary", "", "| Component | Files | LOC | Classes | Functions |", "|-----------|-------|-----|---------|-----------"]

        for comp in sorted(self.components, key=lambda c: c.name):
            lines.append(f"| {comp.name} | {len(comp.modules)} | {comp.total_loc:,} | {comp.total_classes} | {comp.total_functions} |")

        return "\n".join(lines) + "\n"

    def _generate_fsm_diagram(self) -> str:
        states = self.structures.get("fsm_states", [])
        states_str = ", ".join(f"`{s}`" for s in states[:10])
        if len(states) > 10:
            states_str += f" ... (+{len(states)-10} more)"

        return f"""## 2. ZOOM: Orchestration Core

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> BRAINSTORMING: user_input
    IDLE --> SWARM_ANALYZING: /swarm

    BRAINSTORMING --> EXECUTING_TOOL: tool_call
    BRAINSTORMING --> WAITING_USER: task_done

    EXECUTING_TOOL --> VALIDATING_CFL: result
    VALIDATING_CFL --> BRAINSTORMING: continue
    VALIDATING_CFL --> WAITING_USER: done

    SWARM_ANALYZING --> SWARM_NEGOTIATING: analyzed
    SWARM_NEGOTIATING --> SWARM_EXECUTING: agreed
    SWARM_EXECUTING --> VALIDATING_CFL: executed

    WAITING_USER --> IDLE: new_input

    BRAINSTORMING --> ERROR: exception
    ERROR --> IDLE: /reset
    ERROR --> PANIC: fatal

    note right of IDLE: States found: {len(states)}
```

### FSM States Discovered

**OrchestratorState** (`core/fsm/states.py`):
{states_str}
"""

    def _generate_swarm_diagram(self) -> str:
        modes = self.structures.get("swarm_modes", [])

        return f"""## 3. ZOOM: Swarm Engine

```mermaid
graph TD
    subgraph Analysis["Task Analysis"]
        TASK[Task] --> ANALYZER[TaskAnalyzer]
        ANALYZER --> COMPLEXITY{{Complexity}}
        COMPLEXITY -->|TRIVIAL| SKIP[Skip Swarm]
        COMPLEXITY -->|SIMPLE+| SELECT[ModeSelector]
    end

    subgraph Selection["Mode Selection"]
        SELECT --> DYLAN[DyLAN Scores]
        SELECT --> MEMORY[SuccessMemory]
        DYLAN --> PROPOSE[Proposed Mode]
        MEMORY --> PROPOSE
    end

    subgraph Modes["Collaboration Modes ({len(modes)})"]
        EXEC[Execute] --> M1[PARALLEL]
        EXEC --> M2[SEQUENTIAL]
        EXEC --> M3[LEAD_SUPPORT]
        EXEC --> M4[PING_PONG]
        EXEC --> M5[SPECIALIST]
        EXEC --> M6[RED_BLUE]
    end

    subgraph Fallback["Fallback Chain"]
        M1 -.->|fail| M2
        M2 -.->|fail| M5
        M6 -.->|fail| M3
        M3 -.->|fail| M5
        M4 -.->|fail| M2
    end

    PROPOSE --> EXEC
```

### Collaboration Modes Discovered

| Mode | Source |
|------|--------|
""" + "\n".join(f"| `{m}` | `core/swarm/collaboration_modes.py` |" for m in modes) + "\n"

    def _generate_hive_diagram(self) -> str:
        states = self.structures.get("hive_states", [])
        states_str = ", ".join(f"`{s}`" for s in states[:10])
        if len(states) > 10:
            states_str += f" ... (+{len(states)-10} more)"

        return f"""## 4. ZOOM: Hive Mind Pipeline

```mermaid
graph TD
    subgraph Phase1["Phase 1: Analysis"]
        P1A[Gemini Analysis] --> P1B[Claude Analysis]
        P1B --> P1C{{Agreement > 85%?}}
    end

    subgraph Phase2["Phase 2: Debate"]
        P1C -->|No| P2A[Debate 3-10 turns]
        P2A --> P2B[Check Consensus]
        P2B --> BP1[BREAKPOINT]
    end

    subgraph Phase3["Phase 3: Architecture"]
        P1C -->|Yes| P3A
        BP1 --> P3A[Generate Plan]
        P3A --> P3B{{Spawn Needed?}}
        P3B -->|Yes| BP2[BREAKPOINT]
        BP2 --> P3C[Spawn Agents]
    end

    subgraph Phase4["Phase 4: Execution"]
        P3B -->|No| P4A
        P3C --> P4A[Execute Steps]
        P4A --> P4B[Monitor]
        P4B --> P4C{{Success?}}
    end

    subgraph Phase5["Phase 5: Diagnosis"]
        P4C -->|No| P5A[Diagnose Failure]
        P5A --> BP3[BREAKPOINT]
    end

    subgraph Phase6["Phase 6: Retry"]
        BP3 --> P6A{{Retry? max 3}}
        P6A -->|Yes| P3A
        P6A -->|No| FAIL[HIVE_FAILED]
    end

    subgraph Phase7["Phase 7: Consolidation"]
        P4C -->|Yes| P7A[Reflect]
        P7A --> P7B[Archive Knowledge]
        P7B --> SUCCESS[HIVE_SUCCESS]
    end
```

### HiveMind States Discovered

**HiveMindState** (`core/hive_mind/types.py`):
{states_str}
"""

    def _generate_memory_diagram(self) -> str:
        return """## 5. ZOOM: Memory Systems

```mermaid
graph TD
    subgraph RAG["Project Memory - RAG"]
        LEARN[/learn path] --> INDEX[Index Files]
        INDEX --> BACKEND{Backend}
        BACKEND --> DENSE[Dense<br/>LanceDB]
        BACKEND --> TFIDF[TF-IDF]
        BACKEND --> BM25[BM25]
        QUERY[/rag query] --> SEARCH[Semantic Search]
        SEARCH --> CHUNKS[Top-K Chunks]
    end

    subgraph Success["Success Memory"]
        DONE[Task Complete] --> RECORD[record_success]
        RECORD --> STORE[(successes.json)]
        NEW[New Task] --> SIMILAR[search_similar]
        SIMILAR --> STORE
        SIMILAR --> BOOST[Mode Boost 0-30%]
    end

    subgraph Integration["Integration"]
        BOOST --> SELECTOR[ModeSelector]
        CHUNKS --> CONTEXT[Context Builder]
    end
```
"""

    def _generate_functional_inventory(self) -> str:
        commands = self.structures.get("commands", [])
        enums = self.structures.get("enums", [])
        dataclasses = self.structures.get("dataclasses", [])

        # Format commands by category
        cmd_lines = []
        for cmd in sorted(set(commands))[:40]:
            if cmd.startswith("/") or len(cmd) < 20:
                cmd_lines.append(f"- `/{cmd}`" if not cmd.startswith("/") else f"- `{cmd}`")

        return f"""## 6. FUNCTIONAL INVENTORY

### Slash Commands ({len(commands)} discovered)

{chr(10).join(cmd_lines[:30])}

### Enums Discovered ({len(enums)} total)

{', '.join(f'`{e}`' for e in enums[:20])}{"..." if len(enums) > 20 else ""}

### Dataclasses Discovered ({len(dataclasses)} total)

{', '.join(f'`{d}`' for d in dataclasses[:20])}{"..." if len(dataclasses) > 20 else ""}
"""

    def _generate_statistics(self) -> str:
        total_files = sum(len(c.modules) for c in self.components)
        total_loc = sum(c.total_loc for c in self.components)
        total_classes = sum(c.total_classes for c in self.components)
        total_functions = sum(c.total_functions for c in self.components)
        total_dataclasses = len(self.structures.get("dataclasses", []))
        total_enums = len(self.structures.get("enums", []))

        # LOC chart
        loc_chart = []
        max_loc = max((c.total_loc for c in self.components), default=1)
        for comp in sorted(self.components, key=lambda c: -c.total_loc)[:15]:
            bar_len = int((comp.total_loc / max_loc) * 30)
            bar = "#" * bar_len
            loc_chart.append(f"{comp.name:<15} | {bar} {comp.total_loc:,}")

        return f"""## 7. STATISTICS

| Metric | Value |
|--------|-------|
| **Total Components** | {len(self.components)} |
| **Total Python Files** | {total_files} |
| **Total Lines of Code** | {total_loc:,} |
| **Total Classes** | {total_classes} |
| **Total Dataclasses** | {total_dataclasses} |
| **Total Enums** | {total_enums} |

### Lines of Code by Component

```
{chr(10).join(loc_chart)}
```
"""

    def _generate_footer(self) -> str:
        return f"""---

## Regeneration

To regenerate this document after code changes:

```bash
python scripts/doc_engine.py --gen-map --apply
```

Or run the full documentation sync:

```bash
python scripts/doc_engine.py --full --apply
```

---

*Generated by NEXUS Documentation Engine*
*Source: `scripts/doc_engine.py`*
"""


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NEXUS Documentation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--check", action="store_true",
                       help="Check documentation consistency (read-only)")
    parser.add_argument("--sync", action="store_true",
                       help="Synchronize version patterns")
    parser.add_argument("--gen-map", action="store_true",
                       help="Generate architecture map")
    parser.add_argument("--audit", action="store_true",
                       help="Audit module READMEs")
    parser.add_argument("--full", action="store_true",
                       help="Run all modes")
    parser.add_argument("--apply", action="store_true",
                       help="Actually write changes (default is dry-run)")
    parser.add_argument("--output", type=str,
                       help="Output path for architecture map")

    args = parser.parse_args()

    # Default to --check if no mode specified
    if not any([args.check, args.sync, args.gen_map, args.audit, args.full]):
        args.check = True

    # Find project root
    project_root = Path(__file__).parent.parent
    engine = DocEngine(project_root)

    exit_code = 0

    try:
        if args.full:
            success = engine.full(apply=args.apply)
            exit_code = 0 if success else 1

        else:
            if args.check:
                issues = engine.check()
                if any(i.severity == "ERROR" for i in issues):
                    exit_code = 1

            if args.sync:
                engine.sync(apply=args.apply)

            if args.gen_map:
                output = Path(args.output) if args.output else None
                engine.generate_map(output_path=output, apply=args.apply)

            if args.audit:
                engine.audit()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit_code = 2

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
