# NEXUS Documentation Generator - Reporters Module
"""
Report generation for audits and coverage.

Classes:
    AuditReporter: Generates audit reports in Markdown
    CoverageReporter: Generates documentation coverage reports
    DiffReporter: Generates diff reports since last run
"""

from .audit_reporter import AuditReporter

__all__ = ["AuditReporter"]
