# NEXUS Documentation Generator - Repository Scanner
"""
Scans repository for all folders and files with auto-discovery.
"""

import subprocess
from pathlib import Path
from typing import Iterator

from ..config import DocGeneratorConfig, FolderInfo


class RepoScanner:
    """Scans repository for all folders and files."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config
        self.repo_root = config.repo_root

    def scan(self) -> list[FolderInfo]:
        """
        Scan repository recursively, discovering all folders.

        Returns list of FolderInfo objects for each folder found.
        """
        folders = []

        # Scan from repo root, respecting ignore patterns
        for folder_path in self._walk_directories():
            folder_info = self._analyze_folder(folder_path)
            folders.append(folder_info)

        return folders

    def _walk_directories(self) -> Iterator[Path]:
        """Walk all directories in repository."""
        def should_ignore(path: Path) -> bool:
            """Check if path should be ignored."""
            name = path.name
            for pattern in self.config.ignore_patterns:
                if pattern.startswith("*"):
                    # Extension pattern
                    if name.endswith(pattern[1:]):
                        return True
                elif name == pattern or pattern in str(path):
                    return True
            return False

        def walk_recursive(directory: Path) -> Iterator[Path]:
            """Recursively walk directories."""
            if should_ignore(directory):
                return

            yield directory

            try:
                for item in directory.iterdir():
                    if item.is_dir() and not should_ignore(item):
                        yield from walk_recursive(item)
            except PermissionError:
                pass

        # Walk from repo root
        yield from walk_recursive(self.repo_root)

    def _analyze_folder(self, folder_path: Path) -> FolderInfo:
        """Analyze a single folder."""
        python_files = []
        typescript_files = []
        markdown_files = []
        config_files = []
        subfolders = []

        try:
            for item in folder_path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in self.config.python_extensions:
                        python_files.append(item)
                    elif ext in self.config.typescript_extensions:
                        typescript_files.append(item)
                    elif ext in self.config.markdown_extensions:
                        markdown_files.append(item)
                    elif ext in self.config.config_extensions:
                        config_files.append(item)
                elif item.is_dir():
                    # Check if should ignore
                    if not any(
                        p in item.name or item.name == p
                        for p in self.config.ignore_patterns
                    ):
                        subfolders.append(item)
        except PermissionError:
            pass

        # Check for __init__.py and README.md
        has_init = any(f.name == "__init__.py" for f in python_files)
        has_readme = any(f.name.lower() == "readme.md" for f in markdown_files)

        return FolderInfo(
            path=folder_path,
            name=folder_path.name or folder_path.as_posix(),
            python_files=sorted(python_files),
            typescript_files=sorted(typescript_files),
            markdown_files=sorted(markdown_files),
            config_files=sorted(config_files),
            subfolders=sorted(subfolders),
            has_init=has_init,
            has_readme=has_readme,
        )

    def detect_new_folders(self, since: str = "HEAD~1") -> list[Path]:
        """
        Detect new folders since a specific commit.

        Args:
            since: Git reference to compare against (default: HEAD~1)

        Returns:
            List of paths to new folders
        """
        try:
            # Get list of new files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=A", since],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            new_files = result.stdout.strip().split("\n")

            # Extract unique parent directories
            new_folders = set()
            for file_path in new_files:
                if file_path:
                    parent = Path(file_path).parent
                    if parent != Path("."):
                        new_folders.add(self.repo_root / parent)

            return sorted(new_folders)

        except subprocess.CalledProcessError:
            return []
        except FileNotFoundError:
            # Git not available
            return []

    def get_changed_files(self, since: str = "HEAD~1") -> list[Path]:
        """
        Get list of files changed since a specific commit.

        Args:
            since: Git reference to compare against

        Returns:
            List of paths to changed files
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", since],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            files = result.stdout.strip().split("\n")
            return [self.repo_root / f for f in files if f]

        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def get_all_python_files(self) -> list[Path]:
        """Get all Python files in repository."""
        python_files = []
        for folder in self.scan():
            python_files.extend(folder.python_files)
        return sorted(python_files)

    def get_statistics(self) -> dict:
        """Get repository statistics."""
        folders = self.scan()

        python_files = sum(len(f.python_files) for f in folders)
        typescript_files = sum(len(f.typescript_files) for f in folders)
        markdown_files = sum(len(f.markdown_files) for f in folders)
        packages = sum(1 for f in folders if f.is_python_package)

        return {
            "total_folders": len(folders),
            "python_packages": packages,
            "python_files": python_files,
            "typescript_files": typescript_files,
            "markdown_files": markdown_files,
        }
