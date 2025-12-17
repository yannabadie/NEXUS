"""
NEXUS V7.5 Evolution Engine

Handles self-modification, lineage tracking, child evaluation, and validation.

Modules:
- manager.py: Central orchestrator (V7.5 Phase 0a - extracted from repl.py)
- models.py: Dataclasses for evolution operations (V7.5 Phase 0a)
- phases/: Individual phase implementations
- lineage.py: Manages LINEAGE.json and ancestry tree
- evaluator.py: Runs benchmarks and compares to parent
- validator.py: Validates children before promotion (syntax, import, smoke, benchmark, redteam)
- tiered_validator.py: V7 fast-fail validation with parallel benchmarks
- rate_limiter.py: Controls evolution frequency

Note: Child creation uses emergent JSON patches from Gemini+Claude symbiotic debate.
V7.5: Evolution logic is being extracted from repl.py to manager.py for better separation.
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

# V7.5 Phase 0a: Evolution Manager and Models
from .models import (
    MutationProposal,
    BrainstormResult,
    ChildCreationResult,
    EvaluationResult,
    PromotionResult,
    ArchiveResult,
    EvolutionResult,
    SpecializationResult,
    EvolutionStatus,
    EvolutionContext,
    EvolutionPhaseStatus,
)
from .manager import EvolutionManager

# V9.1: Service Layer
from .service import (
    EvolutionService,
    EvolutionServiceResult,
    _get_evolution_service,
)

# V7: mutator.py removed - evolution uses emergent JSON patches from AI debate

__all__ = [
    # V7.5 Phase 0a: Evolution Manager
    "EvolutionManager",
    # V9.1: Service Layer
    "EvolutionService",
    "EvolutionServiceResult",
    "_get_evolution_service",
    # V7.5 Phase 0a: Models
    "MutationProposal",
    "BrainstormResult",
    "ChildCreationResult",
    "EvaluationResult",
    "PromotionResult",
    "ArchiveResult",
    "EvolutionResult",
    "SpecializationResult",
    "EvolutionStatus",
    "EvolutionContext",
    "EvolutionPhaseStatus",
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
