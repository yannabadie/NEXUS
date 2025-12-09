#!/usr/bin/env python3
"""
NEXUS Architecture Map Generator

Generates a comprehensive, auto-adaptive architecture mapping document
by scanning the codebase and extracting structural information.

Usage:
    python scripts/generate_architecture_map.py [--output FILE]

Output:
    docs/ARCHITECTURE_MAP_GENERATED.md (default)
"""

import ast
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict


# =============================================================================
# DATA STRUCTURES
# =============================================================================

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
class ImportInfo:
    """Information about imports."""
    module: str
    names: List[str] = field(default_factory=list)
    is_from: bool = False


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
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
# AST VISITOR
# =============================================================================

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to extract code structure."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[ClassInfo] = []
        self.functions: List[FunctionInfo] = []
        self.imports: List[ImportInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._get_name(b) for b in node.bases]

        # Check if dataclass
        is_dataclass = any(
            self._get_decorator_name(d) == 'dataclass'
            for d in node.decorator_list
        )

        # Check if enum
        is_enum = any(b in ('Enum', 'IntEnum', 'StrEnum') for b in bases)

        # Extract methods
        methods = [
            n.name for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        self.classes.append(ClassInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            bases=bases,
            docstring=ast.get_docstring(node),
            methods=methods,
            is_dataclass=is_dataclass,
            is_enum=is_enum
        ))

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Only top-level functions
        self.functions.append(FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            is_async=False,
            docstring=ast.get_docstring(node)
        ))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.functions.append(FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            is_async=True,
            docstring=ast.get_docstring(node)
        ))

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=alias.name,
                is_from=False
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.append(ImportInfo(
                module=node.module,
                names=[a.name for a in node.names],
                is_from=True
            ))

    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)

    def _get_decorator_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""


# =============================================================================
# SCANNER
# =============================================================================

class CodebaseScanner:
    """Scans the codebase and extracts structural information."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.components: Dict[str, ComponentInfo] = {}
        self.all_classes: List[ClassInfo] = []
        self.all_enums: List[ClassInfo] = []
        self.all_dataclasses: List[ClassInfo] = []

    def scan(self) -> Dict[str, ComponentInfo]:
        """Scan the codebase and return component info."""
        core_path = self.root_path / "core"

        if not core_path.exists():
            raise FileNotFoundError(f"Core directory not found: {core_path}")

        # Scan each subdirectory as a component
        for subdir in sorted(core_path.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith('__'):
                component = self._scan_component(subdir)
                self.components[subdir.name] = component

        # Also scan root core files
        root_component = self._scan_component(core_path, recursive=False)
        self.components['_root'] = root_component

        return self.components

    def _scan_component(self, path: Path, recursive: bool = True) -> ComponentInfo:
        """Scan a component directory."""
        component = ComponentInfo(
            name=path.name,
            path=str(path.relative_to(self.root_path))
        )

        pattern = "**/*.py" if recursive else "*.py"

        for py_file in path.glob(pattern):
            if '__pycache__' in str(py_file):
                continue

            module = self._scan_module(py_file)
            if module:
                component.modules.append(module)
                component.total_loc += module.lines_of_code
                component.total_classes += len(module.classes)
                component.total_functions += len(module.functions)

                # Collect all classes
                for cls in module.classes:
                    self.all_classes.append(cls)
                    if cls.is_enum:
                        self.all_enums.append(cls)
                    if cls.is_dataclass:
                        self.all_dataclasses.append(cls)

        return component

    def _scan_module(self, file_path: Path) -> Optional[ModuleInfo]:
        """Scan a Python module."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            analyzer = CodeAnalyzer(str(file_path.relative_to(self.root_path)))
            analyzer.visit(tree)

            return ModuleInfo(
                path=str(file_path.relative_to(self.root_path)),
                classes=analyzer.classes,
                functions=analyzer.functions,
                imports=analyzer.imports,
                lines_of_code=len(content.splitlines())
            )
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None


# =============================================================================
# EXTRACTORS
# =============================================================================

class StructureExtractor:
    """Extracts specific structural patterns from scanned data."""

    def __init__(self, scanner: CodebaseScanner):
        self.scanner = scanner

    def get_fsm_states(self) -> List[Tuple[str, str, List[str]]]:
        """Extract FSM states from enums."""
        states = []
        for enum in self.scanner.all_enums:
            if 'State' in enum.name:
                # Try to extract values from the file
                values = self._extract_enum_values(enum)
                states.append((enum.name, enum.file_path, values))
        return states

    def get_collaboration_modes(self) -> List[Tuple[str, str]]:
        """Extract collaboration modes."""
        for enum in self.scanner.all_enums:
            if 'CollaborationMode' in enum.name or 'Mode' in enum.name:
                values = self._extract_enum_values(enum)
                return [(v, enum.file_path) for v in values]
        return []

    def get_commands(self) -> Dict[str, List[str]]:
        """Extract slash commands from commands.py."""
        commands = {}
        for comp in self.scanner.components.values():
            for module in comp.modules:
                if 'commands.py' in module.path:
                    commands = self._extract_commands_from_file(
                        self.scanner.root_path / module.path
                    )
        return commands

    def get_dataclasses_by_component(self) -> Dict[str, List[ClassInfo]]:
        """Group dataclasses by component."""
        result = defaultdict(list)
        for dc in self.scanner.all_dataclasses:
            # Extract component from path
            parts = dc.file_path.split('/')
            if len(parts) >= 2:
                component = parts[1]
            else:
                component = '_root'
            result[component].append(dc)
        return dict(result)

    def get_drivers(self) -> List[ClassInfo]:
        """Extract LLM driver classes."""
        drivers = []
        for cls in self.scanner.all_classes:
            if 'Driver' in cls.name:
                drivers.append(cls)
        return drivers

    def get_phases(self) -> List[Tuple[str, str]]:
        """Extract HiveMind phases."""
        phases = []
        for comp in self.scanner.components.values():
            for module in comp.modules:
                if 'phase_' in module.path:
                    phase_name = Path(module.path).stem.replace('phase_', '')
                    phases.append((phase_name, module.path))
        return sorted(phases)

    def _extract_enum_values(self, enum: ClassInfo) -> List[str]:
        """Extract enum values from source file."""
        try:
            file_path = self.scanner.root_path / enum.file_path
            content = file_path.read_text(encoding='utf-8')

            # Find the enum class
            pattern = rf'class\s+{enum.name}.*?(?=\nclass|\Z)'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                enum_content = match.group()
                # Extract values (NAME = "value" or NAME = auto())
                values = re.findall(r'^\s+(\w+)\s*=', enum_content, re.MULTILINE)
                return [v for v in values if v.isupper() or not v.startswith('_')]
        except Exception:
            pass
        return []

    def _extract_commands_from_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Extract COMMAND_CATEGORIES from commands.py."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Find COMMAND_CATEGORIES dict
            pattern = r'COMMAND_CATEGORIES\s*=\s*\{([^}]+(?:\{[^}]+\}[^}]+)*)\}'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                # Parse categories
                categories = {}
                cat_pattern = r'"([^"]+)":\s*\{([^}]+)\}'
                for cat_match in re.finditer(cat_pattern, content):
                    cat_name = cat_match.group(1)
                    cat_content = cat_match.group(2)

                    # Extract commands
                    cmd_pattern = r'"(/[^"]+)"'
                    commands = re.findall(cmd_pattern, cat_content)
                    categories[cat_name] = commands

                return categories
        except Exception:
            pass
        return {}


# =============================================================================
# MERMAID GENERATOR
# =============================================================================

class MermaidGenerator:
    """Generates Mermaid diagrams from extracted data."""

    def __init__(self, extractor: StructureExtractor, scanner: CodebaseScanner):
        self.extractor = extractor
        self.scanner = scanner

    def generate_high_level_overview(self) -> str:
        """Generate high-level architecture diagram."""
        components = list(self.scanner.components.keys())

        # Categorize components
        core = ['orchestration', 'fsm']
        collab = ['swarm', 'hive_mind']
        drivers = ['drivers', 'routing']
        support = ['memory', 'security', 'evolution', 'telemetry']
        interface = ['interface', 'ui']

        return f'''```mermaid
graph TD
    subgraph Entry["🚪 Entry Layer"]
        USER[User Input]
        REPL[REPL<br/>{self._count_commands()} commands]
    end

    subgraph Core["🎯 Orchestration Core"]
        ORCH[OrchestratorV7<br/>{self._count_states('OrchestratorState')} FSM states]
        SWARM[Swarm Engine<br/>{len(self.extractor.get_collaboration_modes())} modes]
        HIVE[Hive Mind<br/>{len(self.extractor.get_phases())} phases]
    end

    subgraph LLM["🤖 LLM Drivers"]
        GEMINI[Gemini Driver]
        CLAUDE[Claude Driver]
    end

    subgraph Support["📦 Support Systems"]
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
```'''

    def generate_fsm_states_diagram(self) -> str:
        """Generate FSM states diagram."""
        states = self.extractor.get_fsm_states()

        # Find OrchestratorState
        orch_states = []
        for name, path, values in states:
            if 'Orchestrator' in name:
                orch_states = values
                break

        if not orch_states:
            return "```\nNo OrchestratorState enum found\n```"

        return f'''```mermaid
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

    note right of IDLE: States found: {len(orch_states)}
```'''

    def generate_swarm_modes_diagram(self) -> str:
        """Generate Swarm collaboration modes diagram."""
        modes = self.extractor.get_collaboration_modes()

        if not modes:
            return "```\nNo CollaborationMode enum found\n```"

        mode_names = [m[0] for m in modes]

        return f'''```mermaid
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
```'''

    def generate_hive_mind_diagram(self) -> str:
        """Generate HiveMind pipeline diagram."""
        phases = self.extractor.get_phases()

        return f'''```mermaid
graph TD
    subgraph Phase1["Phase 1: Analysis"]
        P1A[Gemini Analysis] --> P1B[Claude Analysis]
        P1B --> P1C{{Agreement > 85%?}}
    end

    subgraph Phase2["Phase 2: Debate"]
        P1C -->|No| P2A[Debate 3-10 turns]
        P2A --> P2B[Check Consensus]
        P2B --> BP1[🔴 BREAKPOINT]
    end

    subgraph Phase3["Phase 3: Architecture"]
        P1C -->|Yes| P3A
        BP1 --> P3A[Generate Plan]
        P3A --> P3B{{Spawn Needed?}}
        P3B -->|Yes| BP2[🔴 BREAKPOINT]
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
        P5A --> BP3[🔴 BREAKPOINT]
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

    note right of Phase1: Phases found: {len(phases)}
```'''

    def generate_memory_diagram(self) -> str:
        """Generate memory systems diagram."""
        return '''```mermaid
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
```'''

    def _count_commands(self) -> int:
        """Count total commands."""
        commands = self.extractor.get_commands()
        return sum(len(cmds) for cmds in commands.values())

    def _count_states(self, enum_name: str) -> int:
        """Count states in an enum."""
        for name, path, values in self.extractor.get_fsm_states():
            if enum_name in name:
                return len(values)
        return 0


# =============================================================================
# DOCUMENT GENERATOR
# =============================================================================

class ArchitectureMapGenerator:
    """Generates the complete architecture map document."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.scanner = CodebaseScanner(root_path)
        self.extractor: Optional[StructureExtractor] = None
        self.mermaid: Optional[MermaidGenerator] = None

    def generate(self) -> str:
        """Generate the complete architecture map."""
        # Scan codebase
        print("Scanning codebase...")
        self.scanner.scan()

        self.extractor = StructureExtractor(self.scanner)
        self.mermaid = MermaidGenerator(self.extractor, self.scanner)

        # Get version info
        version = self._get_version()
        git_commit = self._get_git_commit()

        # Build document
        doc = []
        doc.append(self._generate_header(version, git_commit))
        doc.append(self._generate_overview())
        doc.append(self._generate_orchestration_zoom())
        doc.append(self._generate_drivers_zoom())
        doc.append(self._generate_swarm_zoom())
        doc.append(self._generate_hive_mind_zoom())
        doc.append(self._generate_evolution_zoom())
        doc.append(self._generate_memory_zoom())
        doc.append(self._generate_functional_inventory())
        doc.append(self._generate_statistics())
        doc.append(self._generate_footer())

        return "\n\n".join(doc)

    def _get_version(self) -> str:
        """Get NEXUS version from .env or core/__init__.py."""
        try:
            env_file = self.root_path / ".env"
            if env_file.exists():
                content = env_file.read_text()
                match = re.search(r'NEXUS_VERSION=(.+)', content)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass

        try:
            init_file = self.root_path / "core" / "__init__.py"
            if init_file.exists():
                content = init_file.read_text()
                match = re.search(r'__version__\s*=\s*["\'](.+)["\']', content)
                if match:
                    return match.group(1)
        except Exception:
            pass

        return "Unknown"

    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"

    def _generate_header(self, version: str, git_commit: str) -> str:
        """Generate document header."""
        return f'''# NEXUS V{version} Architecture Map

**Auto-Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Git Commit**: {git_commit}
**Generator**: `scripts/generate_architecture_map.py`

---

> This document is automatically generated by scanning the codebase.
> Re-run the generator after significant changes to keep it updated.

---'''

    def _generate_overview(self) -> str:
        """Generate high-level overview section."""
        return f'''## 1. HIGH-LEVEL OVERVIEW

{self.mermaid.generate_high_level_overview()}

### Component Summary

| Component | Files | LOC | Classes | Functions |
|-----------|-------|-----|---------|-----------|
{self._generate_component_table()}'''

    def _generate_component_table(self) -> str:
        """Generate component statistics table."""
        rows = []
        for name, comp in sorted(self.scanner.components.items()):
            if name == '_root':
                continue
            rows.append(
                f"| {name} | {len(comp.modules)} | {comp.total_loc:,} | "
                f"{comp.total_classes} | {comp.total_functions} |"
            )
        return "\n".join(rows)

    def _generate_orchestration_zoom(self) -> str:
        """Generate orchestration zoom section."""
        states = self.extractor.get_fsm_states()

        states_table = ""
        for name, path, values in states:
            if values:
                states_table += f"\n**{name}** (`{path}`):\n"
                states_table += ", ".join(f"`{v}`" for v in values[:10])
                if len(values) > 10:
                    states_table += f" ... (+{len(values)-10} more)"
                states_table += "\n"

        return f'''## 2. ZOOM: Orchestration Core

{self.mermaid.generate_fsm_states_diagram()}

### FSM States Discovered
{states_table}

### Key Files
| File | Role |
|------|------|
| `core/orchestration_v7.py` | Main orchestrator |
| `core/fsm/states.py` | State definitions |
| `core/orchestration/fsm_handlers.py` | State handlers |'''

    def _generate_drivers_zoom(self) -> str:
        """Generate drivers zoom section."""
        drivers = self.extractor.get_drivers()

        drivers_table = ""
        for d in drivers:
            drivers_table += f"| `{d.name}` | `{d.file_path}` |\n"

        return f'''## 3. ZOOM: LLM Drivers & Routing

```mermaid
graph TD
    subgraph Routing["Model Router"]
        TASK[Task Type] --> ROUTER{{Router}}
        ROUTER -->|BRAINSTORM| OPUS[Claude Opus]
        ROUTER -->|TOOL| SONNET[Claude Sonnet]
        ROUTER -->|FAST| FLASH[Gemini Flash]
    end

    subgraph Drivers["Driver Layer"]
        OPUS --> CLAUDE[Claude Driver]
        SONNET --> CLAUDE
        FLASH --> GEMINI[Gemini Driver]
    end
```

### Drivers Discovered

| Class | File |
|-------|------|
{drivers_table}'''

    def _generate_swarm_zoom(self) -> str:
        """Generate Swarm zoom section."""
        modes = self.extractor.get_collaboration_modes()

        modes_table = ""
        for mode, path in modes:
            modes_table += f"| `{mode}` | `{path}` |\n"

        return f'''## 4. ZOOM: Swarm Engine

{self.mermaid.generate_swarm_modes_diagram()}

### Collaboration Modes Discovered

| Mode | Source |
|------|--------|
{modes_table}'''

    def _generate_hive_mind_zoom(self) -> str:
        """Generate HiveMind zoom section."""
        phases = self.extractor.get_phases()

        phases_table = ""
        for phase, path in phases:
            phases_table += f"| {phase.title()} | `{path}` |\n"

        return f'''## 5. ZOOM: Hive Mind Pipeline

{self.mermaid.generate_hive_mind_diagram()}

### Phases Discovered

| Phase | File |
|-------|------|
{phases_table}'''

    def _generate_evolution_zoom(self) -> str:
        """Generate Evolution zoom section."""
        evolution_comp = self.scanner.components.get('evolution', None)

        files_table = ""
        if evolution_comp:
            for mod in evolution_comp.modules:
                files_table += f"| `{Path(mod.path).name}` | {mod.lines_of_code} LOC |\n"

        return f'''## 6. ZOOM: Evolution & Spawning

```mermaid
graph TD
    subgraph Spawn["/spawn Flow"]
        CMD[/spawn role] --> BUDGET{{Budget OK?}}
        BUDGET -->|Yes| UUID[Generate UUID]
        UUID --> BRAIN[Brainstorm Prompt]
        BRAIN --> CERT[BIRTH_CERTIFICATE]
        CERT --> POOL[Register Agent]
    end

    subgraph Validation["5-Tier Validation"]
        CHILD[Child] --> T1[Syntax]
        T1 --> T2[Smoke Test]
        T2 --> T3[Benchmark]
        T3 --> T4[Red Team]
        T4 --> T5[Live Eval]
    end
```

### Evolution Files

| File | Size |
|------|------|
{files_table}'''

    def _generate_memory_zoom(self) -> str:
        """Generate Memory zoom section."""
        return f'''## 7. ZOOM: Memory Systems

{self.mermaid.generate_memory_diagram()}

### Memory Backends

| Backend | Purpose |
|---------|---------|
| Dense (LanceDB) | Semantic similarity |
| TF-IDF | Lexical fallback |
| BM25 | Keyword search |
| SuccessMemory | Pattern learning |'''

    def _generate_functional_inventory(self) -> str:
        """Generate functional inventory section."""
        commands = self.extractor.get_commands()
        dataclasses = self.extractor.get_dataclasses_by_component()

        # Commands table
        commands_section = ""
        for category, cmds in commands.items():
            commands_section += f"\n**{category}**\n"
            for cmd in cmds:
                commands_section += f"- `{cmd}`\n"

        # Dataclasses table
        dc_section = ""
        for comp, dcs in sorted(dataclasses.items()):
            if dcs:
                dc_section += f"\n**{comp}**: "
                dc_section += ", ".join(f"`{dc.name}`" for dc in dcs[:5])
                if len(dcs) > 5:
                    dc_section += f" (+{len(dcs)-5} more)"
                dc_section += "\n"

        return f'''## 8. FUNCTIONAL INVENTORY

### Slash Commands ({sum(len(c) for c in commands.values())} total)
{commands_section}

### Dataclasses by Component ({len(self.scanner.all_dataclasses)} total)
{dc_section}

### Enums Discovered ({len(self.scanner.all_enums)} total)

{", ".join(f"`{e.name}`" for e in self.scanner.all_enums)}'''

    def _generate_statistics(self) -> str:
        """Generate statistics section."""
        total_loc = sum(c.total_loc for c in self.scanner.components.values())
        total_files = sum(len(c.modules) for c in self.scanner.components.values())
        total_classes = len(self.scanner.all_classes)
        total_dataclasses = len(self.scanner.all_dataclasses)
        total_enums = len(self.scanner.all_enums)

        return f'''## 9. STATISTICS

| Metric | Value |
|--------|-------|
| **Total Components** | {len(self.scanner.components) - 1} |
| **Total Python Files** | {total_files} |
| **Total Lines of Code** | {total_loc:,} |
| **Total Classes** | {total_classes} |
| **Total Dataclasses** | {total_dataclasses} |
| **Total Enums** | {total_enums} |

### Lines of Code by Component

```
{self._generate_loc_bar_chart()}
```'''

    def _generate_loc_bar_chart(self) -> str:
        """Generate ASCII bar chart of LOC by component."""
        components = [
            (name, comp.total_loc)
            for name, comp in self.scanner.components.items()
            if name != '_root' and comp.total_loc > 0
        ]
        components.sort(key=lambda x: x[1], reverse=True)

        max_loc = max(loc for _, loc in components) if components else 1
        max_name_len = max(len(name) for name, _ in components) if components else 10

        lines = []
        for name, loc in components[:15]:  # Top 15
            bar_len = int((loc / max_loc) * 30)
            bar = "█" * bar_len
            lines.append(f"{name:<{max_name_len}} | {bar} {loc:,}")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return f'''---

## Regeneration

To regenerate this document after code changes:

```bash
python scripts/generate_architecture_map.py --output docs/ARCHITECTURE_MAP_GENERATED.md
```

---

*Generated by NEXUS Architecture Map Generator*
*Source: `scripts/generate_architecture_map.py`*'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate NEXUS architecture map from codebase"
    )
    parser.add_argument(
        "--output", "-o",
        default="docs/ARCHITECTURE_MAP_GENERATED.md",
        help="Output file path (default: docs/ARCHITECTURE_MAP_GENERATED.md)"
    )
    parser.add_argument(
        "--root", "-r",
        default=".",
        help="Project root path (default: current directory)"
    )

    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    output_path = root_path / args.output

    print(f"NEXUS Architecture Map Generator")
    print(f"================================")
    print(f"Root: {root_path}")
    print(f"Output: {output_path}")
    print()

    generator = ArchitectureMapGenerator(root_path)
    document = generator.generate()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    output_path.write_text(document, encoding='utf-8')

    print(f"\n[OK] Architecture map generated: {output_path}")
    print(f"     Lines: {len(document.splitlines())}")


if __name__ == "__main__":
    main()
