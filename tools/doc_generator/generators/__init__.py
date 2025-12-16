# NEXUS Documentation Generator - Generators Module
"""
Documentation generation using Jinja2 templates.

Classes:
    ReadmeGenerator: Generates README.md files for folders
    MermaidGenerator: Generates Mermaid diagrams
    DocumentAggregator: Aggregates child docs to parent docs
    GlobalViewGenerator: Generates global architecture views
"""

from .readme_generator import ReadmeGenerator
from .mermaid_generator import MermaidGenerator
from .aggregator import DocumentAggregator
from .global_views import GlobalViewGenerator

__all__ = [
    "ReadmeGenerator",
    "MermaidGenerator",
    "DocumentAggregator",
    "GlobalViewGenerator",
]
