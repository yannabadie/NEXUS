"""
NEXUS V7 Security Module - Multi-Layer Parent Protection System

This module provides defense-in-depth against any attempt to modify parent code:
- PathGuardian: Path canonicalization and zone validation
- MutationValidator: AST-based behavioral analysis of mutation code

Design Principles:
- BLOCK writes to parent code (absolute protection)
- ALLOW reads from parent code (agents need context)
- WARN on suspicious patterns (don't over-block)
- ALLOW testing in workspace (agents need to experiment)
"""

from .path_guardian import PathGuardian
from .mutation_validator import MutationValidator

__all__ = ['PathGuardian', 'MutationValidator']

