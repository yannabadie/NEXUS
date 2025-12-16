# NEXUS Documentation Generator - Bug Pattern Detector
"""
Detects suspicious code patterns that may indicate bugs.
"""

import re
from typing import Optional

from ..config import DocGeneratorConfig, Issue, Severity, IssueCategory


class BugPatternDetector:
    """Detects suspicious code patterns."""

    # Pattern definitions: (name, regex, severity, message, suggestion)
    PATTERNS = [
        (
            "bare_except",
            r'except\s*:',
            Severity.HIGH,
            "Bare except clause catches all exceptions",
            "Specify exception type: except Exception: or except SpecificError:",
        ),
        (
            "todo_fixme",
            r'#\s*(TODO|FIXME|XXX|HACK|BUG)\s*[:\s](.{0,60})',
            Severity.INFO,
            "TODO/FIXME comment found",
            None,  # Will be set dynamically
        ),
        (
            "debug_print",
            r'^\s*print\s*\([^)]*\)\s*$',
            Severity.LOW,
            "Debug print statement",
            "Remove debug print or use logging module",
        ),
        (
            "hardcoded_path_windows",
            r'["\'][A-Z]:\\[^"\']+["\']',
            Severity.MEDIUM,
            "Hardcoded Windows path",
            "Use pathlib or os.path for cross-platform paths",
        ),
        (
            "hardcoded_path_unix",
            r'["\'](/home/|/Users/|/var/|/tmp/)[^"\']+["\']',
            Severity.MEDIUM,
            "Hardcoded Unix path",
            "Use pathlib or environment variables",
        ),
        (
            "magic_number",
            r'(?<![a-zA-Z_0-9])([3-9]\d{2}|[1-9]\d{3,})(?![a-zA-Z_0-9])',
            Severity.LOW,
            "Magic number (large literal)",
            "Consider extracting to a named constant",
        ),
        (
            "commented_code",
            r'#\s*(def |class |import |from |if |for |while |return |yield )',
            Severity.LOW,
            "Commented-out code",
            "Remove commented code or explain why it's kept",
        ),
        (
            "mutable_default",
            r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})\s*[,)]',
            Severity.HIGH,
            "Mutable default argument (list or dict)",
            "Use None as default: def func(x=None): x = x or []",
        ),
        (
            "pass_in_except",
            r'except[^:]*:\s*\n\s*pass\s*$',
            Severity.MEDIUM,
            "Silent exception handling (pass in except)",
            "Log the error or re-raise with context",
        ),
        (
            "star_import",
            r'^from\s+\S+\s+import\s+\*',
            Severity.MEDIUM,
            "Star import pollutes namespace",
            "Import specific names: from module import name1, name2",
        ),
        (
            "string_format_sql",
            r'(execute|query)\s*\(\s*f["\']|["\'].*%s.*["\'].*%',
            Severity.CRITICAL,
            "Possible SQL injection (string formatting in query)",
            "Use parameterized queries: execute(query, (param,))",
        ),
        (
            "eval_exec",
            r'\b(eval|exec)\s*\(',
            Severity.HIGH,
            "Use of eval/exec can be dangerous",
            "Consider safer alternatives like ast.literal_eval",
        ),
        (
            "pickle_load",
            r'pickle\.loads?\s*\(',
            Severity.MEDIUM,
            "Pickle can execute arbitrary code on untrusted data",
            "Use json or other safe serialization for untrusted data",
        ),
        (
            "assert_in_prod",
            r'^(\s*)assert\s+',
            Severity.LOW,
            "Assert statements are removed with -O flag",
            "Use explicit conditionals for production checks",
        ),
        (
            "sleep_in_code",
            r'time\.sleep\s*\(\s*\d+\s*\)',
            Severity.LOW,
            "Hardcoded sleep duration",
            "Consider making sleep duration configurable",
        ),
        (
            "credentials_in_code",
            r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            Severity.CRITICAL,
            "Possible hardcoded credentials",
            "Use environment variables or secrets manager",
        ),
    ]

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

    def scan(self, file_path: str, code: str) -> list[Issue]:
        """
        Scan code for bug patterns.

        Args:
            file_path: Path to the file
            code: Source code content

        Returns:
            List of issues found
        """
        issues = []
        lines = code.split("\n")

        for pattern_name, pattern, severity, message, suggestion in self.PATTERNS:
            issues.extend(self._scan_pattern(
                file_path, lines, pattern_name, pattern, severity, message, suggestion
            ))

        return issues

    def _scan_pattern(
        self,
        file_path: str,
        lines: list[str],
        pattern_name: str,
        pattern: str,
        severity: str,
        message: str,
        suggestion: Optional[str]
    ) -> list[Issue]:
        """Scan for a specific pattern."""
        issues = []
        regex = re.compile(pattern, re.IGNORECASE if pattern_name in ("todo_fixme",) else 0)

        for line_num, line in enumerate(lines, 1):
            # Skip comments for most patterns (except those looking for comments)
            if pattern_name not in ("todo_fixme", "commented_code"):
                # Strip string literals to avoid false positives
                stripped = self._strip_strings(line)
                match = regex.search(stripped)
            else:
                match = regex.search(line)

            if match:
                # Get context
                context = line.strip()
                if len(context) > 80:
                    context = context[:77] + "..."

                # Special handling for TODO/FIXME
                if pattern_name == "todo_fixme":
                    tag = match.group(1)
                    content = match.group(2).strip() if match.lastindex >= 2 else ""
                    message = f"{tag} comment: {content}" if content else f"{tag} found"
                    suggestion = f"Address this {tag}"

                issues.append(Issue(
                    file=file_path,
                    line=line_num,
                    category=IssueCategory.BUG_PATTERN,
                    severity=severity,
                    message=message,
                    context=context,
                    suggestion=suggestion,
                ))

        return issues

    def _strip_strings(self, line: str) -> str:
        """Remove string literals from line to avoid false positives."""
        # Simple approach: replace quoted strings with placeholders
        result = re.sub(r'""".*?"""', '""', line)
        result = re.sub(r"'''.*?'''", "''", result)
        result = re.sub(r'"[^"]*"', '""', result)
        result = re.sub(r"'[^']*'", "''", result)
        return result

    def get_severity_counts(self, issues: list[Issue]) -> dict[str, int]:
        """Get counts by severity."""
        counts = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
            Severity.INFO: 0,
        }

        for issue in issues:
            if issue.severity in counts:
                counts[issue.severity] += 1

        return counts

    def scan_file(self, file_path: str) -> list[Issue]:
        """Scan a file for bug patterns."""
        try:
            path = self.config.repo_root / file_path
            code = path.read_text(encoding="utf-8")
            return self.scan(file_path, code)
        except (OSError, UnicodeDecodeError) as e:
            return [Issue(
                file=file_path,
                line=0,
                category=IssueCategory.BUG_PATTERN,
                severity=Severity.INFO,
                message=f"Could not read file: {e}",
            )]
