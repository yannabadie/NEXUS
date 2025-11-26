"""
NEXUS Evolution Engine

Handles self-modification, lineage tracking, child evaluation, and validation.

Modules:
- lineage.py: Manages LINEAGE.json and ancestry tree
- evaluator.py: Runs benchmarks and compares to parent
- validator.py: Validates children before promotion (syntax, import, smoke, benchmark, redteam)
- rate_limiter.py: Controls evolution frequency
- mutator.py: DEPRECATED - kept for reference only

Note: Child creation is now handled directly in repl.py using emergent JSON patches
from Gemini+Claude symbiotic debate, not the hardcoded functions in mutator.py.
"""

from .lineage import *
from .evaluator import *
from .validator import (
    ChildValidator,
    ValidationResult,
    FullValidationResult,
    SafetyGate,
    AutoPromotionDecision
)
from .tiered_validator import (
    TieredValidator,
    ValidationTier,
    TieredValidationResult,
    TierResult
)

# NOTE: mutator.py is DEPRECATED and no longer exported by default
# If needed for legacy code, import directly: from core.evolution.mutator import ...

__all__ = [
    # Lineage
    "load_lineage",
    "add_child",
    "get_ancestry",
    "sign_birth_certificate",
    # Evaluator
    "run_benchmarks",
    "compare_to_parent",
    "calculate_asi_proximity",
    "select_winner",
    # Validator (Legacy)
    "ChildValidator",
    "ValidationResult",
    "FullValidationResult",
    # V7: Auto-Promotion
    "SafetyGate",
    "AutoPromotionDecision",
    # V7 Sprint 2: Tiered Validator
    "TieredValidator",
    "ValidationTier",
    "TieredValidationResult",
    "TierResult",
]
