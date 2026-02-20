"""
NEXUS V12.4 - Security Package

Consolidated security components:
- security: Guards, encryption, execution policy
- governance: Alignment verification, decision logging
- interaction: HITL providers, quality tracking

P5.6 Phase 4: Package consolidation for reduced cognitive load.
"""

# Security exports
from core.security_pkg.security import (
    PathGuardian,
    MutationValidator,
    ExecutionPolicy,
    CommandType,
    get_execution_policy,
    InputGuard,
    ThreatLevel,
    ThreatType,
    InputValidationResult,
    get_input_guard,
    OutputGuard,
    LeakType,
    LeakSeverity,
    OutputValidationResult,
    get_output_guard,
    Spotlighter,
    get_spotlighter,
    SpotlightTechnique,
    SPOTLIGHTER_AVAILABLE,
    hash_password,
    verify_password,
    needs_rehash,
    FileEncryptor,
    EncryptionConfig,
    derive_key,
)

# Governance exports
from core.security_pkg.governance import (
    AlignmentVerifier,
    AlignmentConfig,
    AlignmentResult,
    AlignmentViolation,
    AlignmentPrinciple,
    ViolationSeverity,
    GovernanceDecisionLog,
    GovernanceDecision,
    DecisionPattern,
    DecisionLogStats,
    get_decision_logger,
    reset_decision_logger,
    AlignmentJournal,
    VerificationEntry,
    ViolationEntry,
    TrustScore,
    JournalStats,
    get_alignment_journal,
    reset_alignment_journal,
)

# Interaction exports
from core.security_pkg.interaction import (
    InteractionProvider,
    InteractionLevel,
    InteractionRequiredError,
    Choice,
    CLIProvider,
    HeadlessProvider,
    get_interaction_provider,
    set_interaction_provider,
    reset_interaction_provider,
    InteractionQualityTracker,
    InteractionRecord,
    InteractionTypeProfile,
    InteractionQualityStats,
    get_interaction_tracker,
    reset_interaction_tracker,
)

__all__ = [
    # Security
    "PathGuardian",
    "MutationValidator",
    "ExecutionPolicy",
    "CommandType",
    "get_execution_policy",
    "InputGuard",
    "ThreatLevel",
    "ThreatType",
    "InputValidationResult",
    "get_input_guard",
    "OutputGuard",
    "LeakType",
    "LeakSeverity",
    "OutputValidationResult",
    "get_output_guard",
    "Spotlighter",
    "get_spotlighter",
    "SpotlightTechnique",
    "SPOTLIGHTER_AVAILABLE",
    "hash_password",
    "verify_password",
    "needs_rehash",
    "FileEncryptor",
    "EncryptionConfig",
    "derive_key",
    # Governance
    "AlignmentVerifier",
    "AlignmentConfig",
    "AlignmentResult",
    "AlignmentViolation",
    "AlignmentPrinciple",
    "ViolationSeverity",
    "GovernanceDecisionLog",
    "GovernanceDecision",
    "DecisionPattern",
    "DecisionLogStats",
    "get_decision_logger",
    "reset_decision_logger",
    "AlignmentJournal",
    "VerificationEntry",
    "ViolationEntry",
    "TrustScore",
    "JournalStats",
    "get_alignment_journal",
    "reset_alignment_journal",
    # Interaction
    "InteractionProvider",
    "InteractionLevel",
    "InteractionRequiredError",
    "Choice",
    "CLIProvider",
    "HeadlessProvider",
    "get_interaction_provider",
    "set_interaction_provider",
    "reset_interaction_provider",
    "InteractionQualityTracker",
    "InteractionRecord",
    "InteractionTypeProfile",
    "InteractionQualityStats",
    "get_interaction_tracker",
    "reset_interaction_tracker",
]

__version__ = "12.4.0"
