"""
NEXUS V12.4 COGNITIVE BOOST - MetagraphRAG POC

Proof-of-concept knowledge graph for precise codebase understanding.

POC Scope:
- AST parsing of Python codebase
- In-memory dependency graph
- 3 core queries: dependencies, impact analysis, semantic search
- No Neo4j/LanceDB (full implementation later)

Usage:
    from core.metagraph import CodeGraph, scan_codebase, query_dependencies

    # Build graph from codebase
    graph = scan_codebase("core/")

    # Query dependencies
    deps = query_dependencies(graph, "DriverProtocol")

    # Impact analysis
    impact = analyze_impact(graph, "core/orchestration_v7.py")

Author: Claude (NEXUS V12.4 COGNITIVE BOOST)
Date: 2025-02-18
"""

from .code_graph import CodeGraph, Symbol, Dependency, DependencyType, SymbolType
from .ast_parser import parse_python_file, extract_symbols
from .scanner import scan_codebase, ScanStats
from .query_engine import (
    query_dependencies,
    analyze_impact,
    semantic_search,
)

__all__ = [
    # Core structures
    "CodeGraph",
    "Symbol",
    "Dependency",
    "DependencyType",
    "SymbolType",
    # Parsing
    "parse_python_file",
    "extract_symbols",
    # Scanning
    "scan_codebase",
    "ScanStats",
    # Queries
    "query_dependencies",
    "analyze_impact",
    "semantic_search",
]
