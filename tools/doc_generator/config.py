# NEXUS Documentation Generator - Configuration
"""
Configuration for the documentation generator.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DocGeneratorConfig:
    """Configuration for documentation generation."""

    # Root paths
    repo_root: Path = field(default_factory=lambda: Path.cwd())

    # Scan configuration
    scan_roots: list[str] = field(default_factory=lambda: [
        "core/",
        "interface/",
        "tests/",
        "tools/",
        "prompts/",
        "docs/",
        "audit/",
    ])

    ignore_patterns: list[str] = field(default_factory=lambda: [
        ".git",
        "node_modules",
        "__pycache__",
        ".nexus",
        "workspace/logs",
        "dist",
        "build",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "*.egg-info",
    ])

    # File patterns
    python_extensions: list[str] = field(default_factory=lambda: [".py"])
    typescript_extensions: list[str] = field(default_factory=lambda: [".ts", ".tsx"])
    markdown_extensions: list[str] = field(default_factory=lambda: [".md"])
    config_extensions: list[str] = field(default_factory=lambda: [
        ".json", ".yaml", ".yml", ".toml", ".ini", ".env"
    ])

    # Output configuration
    output_dir: Optional[Path] = None
    mermaid_output_dir: Optional[Path] = None
    audit_output_dir: Optional[Path] = None

    # Generation options
    generate_readmes: bool = True
    generate_mermaid: bool = True
    generate_global_views: bool = True

    # Validation options
    check_dead_code: bool = True
    check_dead_imports: bool = True
    check_missing_docs: bool = True
    check_bug_patterns: bool = True

    # CI/CD options
    fail_on_critical: bool = False
    fail_on_high: bool = False
    fail_on_drift: bool = False

    # Template configuration
    templates_dir: Optional[Path] = None

    # Verbosity
    verbose: bool = False

    # README Protection (V13.0 - CRITICAL)
    # These files will NEVER be overwritten by doc generator
    protected_readmes: list[str] = field(default_factory=lambda: [
        "README.md",           # Root - NEVER overwrite
        "docs/README.md",      # Docs index - NEVER overwrite
        "CLAUDE.md",           # Claude instructions
        "GEMINI.md",           # Gemini instructions
        "MISSION.md",          # Mission statement
        "ROADMAP.md",          # Development roadmap
    ])

    # READMEs that keep their existing header but receive updated stats
    preserve_header_readmes: list[str] = field(default_factory=lambda: [
        "core/README.md",
        "core/swarm/README.md",
        "core/memory/README.md",
        "core/hive_mind/README.md",
        "core/fsm/README.md",
        "core/drivers/README.md",
        "core/security/README.md",
        "core/evolution/README.md",
        "core/synapse/README.md",
        "interface/README.md",
        "interface/ui/cerebro/README.md",
    ])

    # Respect protection lists (can be disabled with CLI flag for testing)
    respect_protected: bool = True

    def __post_init__(self):
        """Initialize derived paths."""
        if self.output_dir is None:
            self.output_dir = self.repo_root / "docs"
        if self.mermaid_output_dir is None:
            self.mermaid_output_dir = self.repo_root / "docs" / "architecture"
        if self.audit_output_dir is None:
            self.audit_output_dir = self.repo_root / "audit"
        if self.templates_dir is None:
            self.templates_dir = Path(__file__).parent / "templates"

    @classmethod
    def from_repo(cls, repo_path: Path | str) -> "DocGeneratorConfig":
        """Create configuration from repository path."""
        repo_path = Path(repo_path)
        return cls(repo_root=repo_path)


# Issue severity levels
class Severity:
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Issue categories
class IssueCategory:
    """Issue categories for audit reports."""
    DEAD_CODE = "dead_code"
    DEAD_IMPORT = "dead_import"
    MISSING_DOC = "missing_doc"
    OUTDATED_REF = "outdated_ref"
    BUG_PATTERN = "bug_pattern"
    TYPE_ERROR = "type_error"
    DOC_DRIFT = "doc_drift"
    SECURITY = "security"


@dataclass
class Issue:
    """Represents a detected issue."""

    file: str
    line: int
    category: str
    severity: str
    message: str
    context: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "file": self.file,
            "line": self.line,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "context": self.context,
            "suggestion": self.suggestion,
        }


@dataclass
class ModuleInfo:
    """Information about a Python module."""

    path: Path
    name: str
    docstring: Optional[str] = None
    classes: list = field(default_factory=list)
    functions: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    loc: int = 0

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @property
    def function_count(self) -> int:
        return len(self.functions)


@dataclass
class ClassInfo:
    """Information about a Python class."""

    name: str
    docstring: Optional[str] = None
    methods: list = field(default_factory=list)
    attributes: list = field(default_factory=list)
    bases: list = field(default_factory=list)
    decorators: list = field(default_factory=list)
    line: int = 0


@dataclass
class FunctionInfo:
    """Information about a Python function."""

    name: str
    signature: str
    docstring: Optional[str] = None
    decorators: list = field(default_factory=list)
    line: int = 0
    is_async: bool = False


@dataclass
class ImportInfo:
    """Information about an import statement."""

    module: str
    names: list[str] = field(default_factory=list)
    is_from: bool = False
    line: int = 0


@dataclass
class FolderInfo:
    """Information about a folder in the repository."""

    path: Path
    name: str
    python_files: list[Path] = field(default_factory=list)
    typescript_files: list[Path] = field(default_factory=list)
    markdown_files: list[Path] = field(default_factory=list)
    config_files: list[Path] = field(default_factory=list)
    subfolders: list[Path] = field(default_factory=list)
    has_init: bool = False
    has_readme: bool = False

    @property
    def file_count(self) -> int:
        return (
            len(self.python_files) +
            len(self.typescript_files) +
            len(self.markdown_files) +
            len(self.config_files)
        )

    @property
    def is_python_package(self) -> bool:
        return self.has_init
