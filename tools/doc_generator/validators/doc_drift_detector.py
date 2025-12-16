# NEXUS Documentation Generator - Documentation Drift Detector
"""
Detects when documentation is out of sync with code.
"""

import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, Issue, Severity, IssueCategory


class DocDriftDetector:
    """Detects documentation drift (docs out of sync with code)."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def detect(self) -> list[Issue]:
        """
        Detect documentation that may be outdated.

        Returns:
            List of issues for outdated documentation
        """
        issues = []

        # Check READMEs against code changes
        issues.extend(self._check_readme_drift())

        # Check for stale version references
        issues.extend(self._check_version_drift())

        # Check for broken links
        issues.extend(self._check_broken_links())

        return issues

    def _check_readme_drift(self) -> list[Issue]:
        """Check if README files are older than their sibling code files."""
        issues = []

        for readme_path in self.config.repo_root.rglob("README.md"):
            # Get folder
            folder = readme_path.parent

            # Get latest code modification time
            latest_code_mtime = None
            for py_file in folder.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                mtime = py_file.stat().st_mtime
                if latest_code_mtime is None or mtime > latest_code_mtime:
                    latest_code_mtime = mtime

            if latest_code_mtime is None:
                continue

            # Compare with README modification time
            readme_mtime = readme_path.stat().st_mtime

            # If code is significantly newer (more than 7 days)
            code_time = datetime.fromtimestamp(latest_code_mtime)
            readme_time = datetime.fromtimestamp(readme_mtime)

            if code_time > readme_time + timedelta(days=7):
                try:
                    rel_path = readme_path.relative_to(self.config.repo_root)
                except ValueError:
                    rel_path = readme_path

                issues.append(Issue(
                    file=str(rel_path),
                    line=1,
                    category=IssueCategory.DOC_DRIFT,
                    severity=Severity.MEDIUM,
                    message=f"README may be outdated (code modified {code_time.strftime('%Y-%m-%d')})",
                    suggestion="Review and update README to reflect code changes",
                ))

        return issues

    def _check_version_drift(self) -> list[Issue]:
        """Check for stale version numbers in documentation."""
        issues = []

        # Common version patterns
        version_pattern = re.compile(r'[Vv]ersion[:\s]+(\d+\.\d+(?:\.\d+)?)')

        # Get current version from common locations
        current_version = self._get_current_version()

        if not current_version:
            return issues

        # Check markdown files
        for md_file in self.config.repo_root.rglob("*.md"):
            # Skip archives
            if "archive" in str(md_file).lower():
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for match in version_pattern.finditer(content):
                doc_version = match.group(1)
                if self._version_is_older(doc_version, current_version):
                    try:
                        rel_path = md_file.relative_to(self.config.repo_root)
                    except ValueError:
                        rel_path = md_file

                    # Find line number
                    line_num = content[:match.start()].count("\n") + 1

                    issues.append(Issue(
                        file=str(rel_path),
                        line=line_num,
                        category=IssueCategory.DOC_DRIFT,
                        severity=Severity.LOW,
                        message=f"Version {doc_version} may be outdated (current: {current_version})",
                        suggestion=f"Update version reference to {current_version}",
                    ))

        return issues

    def _get_current_version(self) -> Optional[str]:
        """Get current version from common locations."""
        # Try pyproject.toml
        pyproject = self.config.repo_root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except (OSError, UnicodeDecodeError):
                pass

        # Try __version__ in __init__.py
        for init_file in self.config.repo_root.rglob("__init__.py"):
            try:
                content = init_file.read_text(encoding="utf-8")
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except (OSError, UnicodeDecodeError):
                continue

        # Try ROADMAP.md for version info
        roadmap = self.config.repo_root / "ROADMAP.md"
        if roadmap.exists():
            try:
                content = roadmap.read_text(encoding="utf-8")
                match = re.search(r'Version[:\s]+(\d+\.\d+(?:\.\d+)?)', content)
                if match:
                    return match.group(1)
            except (OSError, UnicodeDecodeError):
                pass

        return None

    def _version_is_older(self, doc_version: str, current_version: str) -> bool:
        """Compare version strings."""
        try:
            doc_parts = [int(x) for x in doc_version.split(".")]
            curr_parts = [int(x) for x in current_version.split(".")]

            # Pad to same length
            while len(doc_parts) < len(curr_parts):
                doc_parts.append(0)
            while len(curr_parts) < len(doc_parts):
                curr_parts.append(0)

            return doc_parts < curr_parts
        except ValueError:
            return False

    def _check_broken_links(self) -> list[Issue]:
        """Check for broken internal links in documentation."""
        issues = []

        # Pattern for markdown links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        for md_file in self.config.repo_root.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for match in link_pattern.finditer(content):
                link_text = match.group(1)
                link_target = match.group(2)

                # Skip external links
                if link_target.startswith(("http://", "https://", "#", "mailto:")):
                    continue

                # Resolve relative path
                target_path = md_file.parent / link_target

                # Handle anchors
                if "#" in link_target:
                    target_path = md_file.parent / link_target.split("#")[0]

                if not target_path.exists() and link_target:
                    try:
                        rel_path = md_file.relative_to(self.config.repo_root)
                    except ValueError:
                        rel_path = md_file

                    line_num = content[:match.start()].count("\n") + 1

                    issues.append(Issue(
                        file=str(rel_path),
                        line=line_num,
                        category=IssueCategory.DOC_DRIFT,
                        severity=Severity.MEDIUM,
                        message=f"Broken link: '{link_target}'",
                        context=f"[{link_text}]({link_target})",
                        suggestion=f"Fix or remove broken link to '{link_target}'",
                    ))

        return issues

    def check_since_commit(self, commit: str) -> list[Issue]:
        """
        Check for documentation drift since a specific commit.

        Args:
            commit: Git commit reference

        Returns:
            List of issues for files needing doc updates
        """
        issues = []

        try:
            # Get changed Python files
            result = subprocess.run(
                ["git", "diff", "--name-only", commit, "--", "*.py"],
                cwd=self.config.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = result.stdout.strip().split("\n")

            for file_path in changed_files:
                if not file_path:
                    continue

                # Check if corresponding README exists and was updated
                folder = Path(file_path).parent
                readme = self.config.repo_root / folder / "README.md"

                if readme.exists():
                    # Check if README was also changed
                    readme_result = subprocess.run(
                        ["git", "diff", "--name-only", commit, "--", str(readme.relative_to(self.config.repo_root))],
                        cwd=self.config.repo_root,
                        capture_output=True,
                        text=True,
                    )

                    if not readme_result.stdout.strip():
                        issues.append(Issue(
                            file=str(folder / "README.md"),
                            line=1,
                            category=IssueCategory.DOC_DRIFT,
                            severity=Severity.LOW,
                            message=f"Code changed in {folder} but README not updated",
                            suggestion="Review if README needs updating",
                        ))

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return issues
