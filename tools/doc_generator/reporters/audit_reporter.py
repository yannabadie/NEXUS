# NEXUS Documentation Generator - Audit Reporter
"""
Generates audit reports in Markdown format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import DocGeneratorConfig, Issue, Severity

# Try to import jinja2
try:
    from jinja2 import Environment, FileSystemLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


class AuditReporter:
    """Generates audit reports."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config

        if HAS_JINJA2 and config.templates_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(config.templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.env = None

    def generate(
        self,
        issues: list[Issue],
        output_dir: Optional[Path] = None
    ) -> None:
        """
        Generate audit report.

        Args:
            issues: List of issues to report
            output_dir: Output directory (default: config.audit_output_dir)
        """
        output_dir = output_dir or self.config.audit_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Categorize issues
        critical = [i for i in issues if i.severity == Severity.CRITICAL]
        high = [i for i in issues if i.severity == Severity.HIGH]
        medium = [i for i in issues if i.severity == Severity.MEDIUM]
        low = [i for i in issues if i.severity == Severity.LOW]
        info = [i for i in issues if i.severity == Severity.INFO]

        # Generate markdown report
        report = self._generate_markdown(
            issues, critical, high, medium, low, info
        )

        (output_dir / "AUTO_DETECTED_ISSUES.md").write_text(report, encoding="utf-8")

        # Generate JSON for machine processing
        json_data = [issue.to_dict() for issue in issues]
        (output_dir / "issues.json").write_text(
            json.dumps(json_data, indent=2),
            encoding="utf-8"
        )

        # Generate summary
        summary = self._generate_summary(issues, critical, high, medium, low, info)
        (output_dir / "AUDIT_SUMMARY.md").write_text(summary, encoding="utf-8")

    def _generate_markdown(
        self,
        issues: list[Issue],
        critical: list[Issue],
        high: list[Issue],
        medium: list[Issue],
        low: list[Issue],
        info: list[Issue]
    ) -> str:
        """Generate markdown report."""
        if self.env:
            try:
                template = self.env.get_template("audit_report.md.j2")
                return template.render(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    scope="Full Repository",
                    total_issues=len(issues),
                    critical_count=len(critical),
                    high_count=len(high),
                    medium_count=len(medium),
                    low_count=len(low),
                    info_count=len(info),
                    critical_issues=critical,
                    high_issues=high,
                    medium_issues=medium,
                    low_issues=low,
                    info_issues=info,
                    version="1.0.0",
                )
            except Exception:
                pass  # Fall through to simple generation

        return self._generate_simple_markdown(
            issues, critical, high, medium, low, info
        )

    def _generate_simple_markdown(
        self,
        issues: list[Issue],
        critical: list[Issue],
        high: list[Issue],
        medium: list[Issue],
        low: list[Issue],
        info: list[Issue]
    ) -> str:
        """Generate markdown without Jinja2."""
        lines = [
            "# NEXUS Auto-Detected Issues",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Total Issues**: {len(issues)}",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| 🔴 Critical | {len(critical)} |",
            f"| 🟠 High | {len(high)} |",
            f"| 🟡 Medium | {len(medium)} |",
            f"| 🔵 Low | {len(low)} |",
            f"| ⚪ Info | {len(info)} |",
            "",
            "---",
            "",
        ]

        # Critical issues
        if critical:
            lines.extend([
                "## 🔴 Critical Issues",
                "",
                "These issues must be fixed immediately.",
                "",
            ])
            for issue in critical:
                lines.extend(self._format_issue(issue))

        # High issues
        if high:
            lines.extend([
                "## 🟠 High Priority Issues",
                "",
            ])
            for issue in high:
                lines.extend(self._format_issue(issue))

        # Medium issues
        if medium:
            lines.extend([
                "## 🟡 Medium Priority Issues",
                "",
            ])
            for issue in medium:
                lines.append(f"- **{issue.file}:{issue.line}** ({issue.category}): {issue.message}")
            lines.append("")

        # Low issues
        if low:
            lines.extend([
                "## 🔵 Low Priority Issues",
                "",
            ])
            for issue in low:
                lines.append(f"- **{issue.file}:{issue.line}** ({issue.category}): {issue.message}")
            lines.append("")

        # Info
        if info:
            lines.extend([
                "## ⚪ Informational",
                "",
            ])
            for issue in info[:20]:  # Limit to 20
                lines.append(f"- **{issue.file}:{issue.line}** ({issue.category}): {issue.message}")
            if len(info) > 20:
                lines.append(f"- ... and {len(info) - 20} more")
            lines.append("")

        lines.extend([
            "---",
            "*Auto-generated by nexus-doc-generator*",
        ])

        return "\n".join(lines)

    def _format_issue(self, issue: Issue) -> list[str]:
        """Format a single issue for markdown."""
        lines = [
            f"### {issue.file}:{issue.line}",
            "",
            f"**Category**: {issue.category}",
            "",
            issue.message,
            "",
        ]

        if issue.context:
            lines.extend([
                "```python",
                issue.context,
                "```",
                "",
            ])

        if issue.suggestion:
            lines.extend([
                f"**Suggestion**: {issue.suggestion}",
                "",
            ])

        lines.append("---")
        lines.append("")

        return lines

    def _generate_summary(
        self,
        issues: list[Issue],
        critical: list[Issue],
        high: list[Issue],
        medium: list[Issue],
        low: list[Issue],
        info: list[Issue]
    ) -> str:
        """Generate summary report."""
        # Group by category
        by_category = {}
        for issue in issues:
            cat = issue.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)

        # Group by file
        by_file = {}
        for issue in issues:
            file = issue.file.split("/")[0] if "/" in issue.file else issue.file.split("\\")[0]
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(issue)

        lines = [
            "# Audit Summary",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Overview",
            "",
            f"- **Total Issues**: {len(issues)}",
            f"- **Critical**: {len(critical)}",
            f"- **High**: {len(high)}",
            f"- **Action Required**: {'Yes' if critical or high else 'No'}",
            "",
            "## By Category",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ]

        for cat, cat_issues in sorted(by_category.items(), key=lambda x: -len(x[1])):
            lines.append(f"| {cat} | {len(cat_issues)} |")

        lines.extend([
            "",
            "## By Location",
            "",
            "| Location | Issues |",
            "|----------|--------|",
        ])

        for loc, loc_issues in sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]:
            lines.append(f"| {loc}/ | {len(loc_issues)} |")

        lines.extend([
            "",
            "---",
            "*Auto-generated by nexus-doc-generator*",
        ])

        return "\n".join(lines)

    def generate_pr_comment(self, issues: list[Issue]) -> str:
        """
        Generate a comment for GitHub PR.

        Returns markdown suitable for PR comment.
        """
        critical = [i for i in issues if i.severity == Severity.CRITICAL]
        high = [i for i in issues if i.severity == Severity.HIGH]

        lines = ["## 📋 Documentation Audit", ""]

        if critical:
            lines.append(f"### ❌ {len(critical)} Critical Issues")
            lines.append("")
            for issue in critical[:5]:
                lines.append(f"- `{issue.file}:{issue.line}`: {issue.message}")
            if len(critical) > 5:
                lines.append(f"- ... and {len(critical) - 5} more")
            lines.append("")

        if high:
            lines.append(f"### ⚠️ {len(high)} High Priority Issues")
            lines.append("")
            for issue in high[:5]:
                lines.append(f"- `{issue.file}:{issue.line}`: {issue.message}")
            if len(high) > 5:
                lines.append(f"- ... and {len(high) - 5} more")
            lines.append("")

        if not critical and not high:
            lines.append("### ✅ No critical issues found")
            lines.append("")

        return "\n".join(lines)
