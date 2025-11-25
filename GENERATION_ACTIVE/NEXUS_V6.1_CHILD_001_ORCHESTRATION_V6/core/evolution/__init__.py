"""
NEXUS Evolution Engine

Handles self-modification, lineage tracking, and child evaluation.

Modules:
- lineage.py: Manages LINEAGE.json and ancestry tree
- mutator.py: Creates child instances with modifications
- evaluator.py: Runs benchmarks and compares to parent
"""

from .lineage import *
from .mutator import *
from .evaluator import *

__all__ = [
    "load_lineage",
    "add_child",
    "get_ancestry",
    "sign_birth_certificate",
    "clone_parent",
    "apply_mutations",
    "generate_diff",
    "create_birth_certificate",
    "run_benchmarks",
    "compare_to_parent",
    "calculate_asi_proximity",
    "select_winner"
]
