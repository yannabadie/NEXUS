"""
NEXUS V7.6 Security Module - Multi-Layer Defense System

This module provides defense-in-depth protection:
- ExecutionPolicy: Command validation and injection prevention (Phase 14a)
- PathGuardian: Path canonicalization and zone validation
- MutationValidator: AST-based behavioral analysis of mutation code

Design Principles:
- BLOCK writes to parent code (absolute protection)
- ALLOW reads from parent code (agents need context)
- WARN on suspicious patterns (don't over-block)
- ALLOW testing in workspace (agents need to experiment)
- PREFER shell=False for command execution (Phase 14a)
"""

from .path_guardian import PathGuardian
from .mutation_validator import MutationValidator
from .execution_policy import ExecutionPolicy, CommandType, get_execution_policy
from .input_guard import InputGuard, get_input_guard, ThreatType
from .output_guard import OutputGuard, get_output_guard, LeakType

__all__ = [
    'PathGuardian',
    'MutationValidator',
    'ExecutionPolicy',
    'CommandType',
    'get_execution_policy',
    'InputGuard',
    'get_input_guard',
    'ThreatType',
    'OutputGuard',
    'get_output_guard',
    'LeakType',
]

