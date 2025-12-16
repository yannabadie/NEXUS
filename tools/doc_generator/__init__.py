# NEXUS Documentation Generator
"""
Automated documentation generator for NEXUS.

Features:
    - AST-based code analysis (Python, TypeScript)
    - Mermaid diagram generation
    - README generation with Jinja2 templates
    - Hierarchical aggregation (child -> parent -> workflows)
    - Consistency checking and bug pattern detection
    - CI/CD integration with drift detection

Usage:
    python -m tools.doc_generator generate --all
    python -m tools.doc_generator audit --output audit/
    python -m tools.doc_generator check --fail-on critical
"""

__version__ = "1.0.0"
__author__ = "NEXUS Team"

from .config import DocGeneratorConfig

__all__ = ["DocGeneratorConfig", "__version__"]
