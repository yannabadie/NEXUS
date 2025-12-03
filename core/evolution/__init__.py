"""
NEXUS V7 Evolution Engine

Handles self-modification, lineage tracking, child evaluation, and validation.

Modules:
- lineage.py: Manages LINEAGE.json and ancestry tree
- evaluator.py: Runs benchmarks and compares to parent
- validator.py: Validates children before promotion (syntax, import, smoke, benchmark, redteam)
- tiered_validator.py: V7 fast-fail validation with parallel benchmarks
- rate_limiter.py: Controls evolution frequency

Note: Child creation uses emergent JSON patches from Gemini+Claude symbiotic debate
in repl.py, not hardcoded mutation functions.
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

# V7: mutator.py removed - evolution uses emergent JSON patches from AI debate

__all__ = [
    # Lineage
    "load_lineage",
    "add_child",
    "get_ancestry",
    "sign_birth_certificate",
    # Evaluator (V7.5: Fitness-based, no ASI)
    "run_benchmarks",
    "compare_to_parent",
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
