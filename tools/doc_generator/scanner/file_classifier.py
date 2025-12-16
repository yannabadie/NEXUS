# NEXUS Documentation Generator - File Classifier
"""
Classifies files by type and purpose.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig


class FileType(Enum):
    """Types of files in the repository."""
    PYTHON_MODULE = "python_module"
    PYTHON_INIT = "python_init"
    PYTHON_TEST = "python_test"
    PYTHON_CONFIG = "python_config"
    TYPESCRIPT_COMPONENT = "typescript_component"
    TYPESCRIPT_HOOK = "typescript_hook"
    TYPESCRIPT_UTIL = "typescript_util"
    TYPESCRIPT_TYPE = "typescript_type"
    MARKDOWN_README = "markdown_readme"
    MARKDOWN_DOC = "markdown_doc"
    CONFIG_JSON = "config_json"
    CONFIG_YAML = "config_yaml"
    CONFIG_TOML = "config_toml"
    CONFIG_ENV = "config_env"
    UNKNOWN = "unknown"


class FileClassifier:
    """Classifies files by type and purpose."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def classify(self, file_path: Path) -> FileType:
        """
        Classify a file by its type.

        Args:
            file_path: Path to the file

        Returns:
            FileType enum value
        """
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Python files
        if suffix == ".py":
            return self._classify_python(file_path)

        # TypeScript files
        if suffix in (".ts", ".tsx"):
            return self._classify_typescript(file_path)

        # Markdown files
        if suffix == ".md":
            return self._classify_markdown(file_path)

        # Config files
        if suffix == ".json":
            return FileType.CONFIG_JSON
        if suffix in (".yaml", ".yml"):
            return FileType.CONFIG_YAML
        if suffix == ".toml":
            return FileType.CONFIG_TOML
        if name.startswith(".env"):
            return FileType.CONFIG_ENV

        return FileType.UNKNOWN

    def _classify_python(self, file_path: Path) -> FileType:
        """Classify Python file."""
        name = file_path.name.lower()
        parent = file_path.parent.name.lower()

        if name == "__init__.py":
            return FileType.PYTHON_INIT

        if name.startswith("test_") or name.endswith("_test.py"):
            return FileType.PYTHON_TEST

        if parent == "tests":
            return FileType.PYTHON_TEST

        if name in ("conftest.py", "setup.py", "pyproject.toml"):
            return FileType.PYTHON_CONFIG

        return FileType.PYTHON_MODULE

    def _classify_typescript(self, file_path: Path) -> FileType:
        """Classify TypeScript file."""
        name = file_path.name.lower()
        stem = file_path.stem.lower()

        # Check for hooks
        if name.startswith("use") or "hook" in name:
            return FileType.TYPESCRIPT_HOOK

        # Check for type definitions
        if name.endswith(".d.ts") or stem.endswith("types"):
            return FileType.TYPESCRIPT_TYPE

        # Check for utils
        if "util" in name or "helper" in name:
            return FileType.TYPESCRIPT_UTIL

        # Default to component for TSX, util for TS
        if file_path.suffix.lower() == ".tsx":
            return FileType.TYPESCRIPT_COMPONENT

        return FileType.TYPESCRIPT_UTIL

    def _classify_markdown(self, file_path: Path) -> FileType:
        """Classify Markdown file."""
        name = file_path.name.lower()

        if name == "readme.md":
            return FileType.MARKDOWN_README

        return FileType.MARKDOWN_DOC

    def get_file_purpose(self, file_path: Path) -> Optional[str]:
        """
        Get a human-readable description of the file's purpose.

        Args:
            file_path: Path to the file

        Returns:
            Description string or None
        """
        file_type = self.classify(file_path)

        purposes = {
            FileType.PYTHON_MODULE: "Python module",
            FileType.PYTHON_INIT: "Package initializer",
            FileType.PYTHON_TEST: "Test file",
            FileType.PYTHON_CONFIG: "Configuration file",
            FileType.TYPESCRIPT_COMPONENT: "React component",
            FileType.TYPESCRIPT_HOOK: "React hook",
            FileType.TYPESCRIPT_UTIL: "Utility functions",
            FileType.TYPESCRIPT_TYPE: "Type definitions",
            FileType.MARKDOWN_README: "Package documentation",
            FileType.MARKDOWN_DOC: "Documentation",
            FileType.CONFIG_JSON: "JSON configuration",
            FileType.CONFIG_YAML: "YAML configuration",
            FileType.CONFIG_TOML: "TOML configuration",
            FileType.CONFIG_ENV: "Environment variables",
        }

        return purposes.get(file_type)

    def is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file."""
        return self.classify(file_path) == FileType.PYTHON_TEST

    def is_documentation(self, file_path: Path) -> bool:
        """Check if file is documentation."""
        file_type = self.classify(file_path)
        return file_type in (FileType.MARKDOWN_README, FileType.MARKDOWN_DOC)
