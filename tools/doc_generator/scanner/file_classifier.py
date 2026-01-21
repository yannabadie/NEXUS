"""
File classifier module.

This module provides functionality to classify files within the codebase
into different categories such as source code, tests, documentation, etc.
"""

from enum import Enum, auto
from pathlib import Path


class FileCategory(Enum):
    """Enumeration of file categories."""
    SOURCE = auto()
    TEST = auto()
    DOCUMENTATION = auto()
    CONFIGURATION = auto()
    SCRIPT = auto()
    UNKNOWN = auto()


class FileClassifier:
    """
    Classifies files into specific categories based on their path and extension.
    """

    def classify(self, file_path: Path) -> FileCategory:
        """
        Classifies a given file into a category.

        Args:
            file_path: The path to the file to classify.

        Returns:
            The determined FileCategory for the file.
        """
        if not file_path.exists():
            return FileCategory.UNKNOWN

        name = file_path.name
        suffix = file_path.suffix

        if name.startswith("test_") or "_test" in name or "tests" in file_path.parts:
            return FileCategory.TEST
        
        if suffix == ".py":
            if "scripts" in file_path.parts:
                return FileCategory.SCRIPT
            return FileCategory.SOURCE
            
        if suffix in [".md", ".txt", ".rst"]:
            return FileCategory.DOCUMENTATION
            
        if suffix in [".json", ".yaml", ".yml", ".toml", ".ini", ".env"]:
            return FileCategory.CONFIGURATION

        return FileCategory.UNKNOWN
