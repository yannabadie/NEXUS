"""
NEXUS Governance & Security - "Le Tribunal"

Handles security policies, alignment verification, and access control.

## Modules

### Active
- `red_team/`: Alignment testing with trap questions (blocks unsafe evolutions)
- `sandbox_policy.py`: Tool execution permissions and security policies

### Planned (TODO)
- `gcp_gatekeeper.py`: GCP access control with ROI validation
- `ethics.py`: Alignment verification to Creator (Yann Abadie)

## Architecture

```
governance/
├── __init__.py          # This file
├── red_team/            # Alignment testing (migrated from BENCHMARKS/)
│   ├── __init__.py
│   ├── alignment_tests.py
│   └── validator.py
├── sandbox_policy.py    # Tool execution permissions and security policies
├── gcp_gatekeeper.py    # TODO: ROI-based cloud access
└── ethics.py            # TODO: Alignment verification to Creator
```

## Usage

```python
from core.governance.red_team import RedTeamValidator

validator = RedTeamValidator(child_path, child_id)
results = validator.run_alignment_tests()
```
"""

# V12.4: Ethics & Alignment Verification
from .ethics import (
    AlignmentVerifier,
    AlignmentConfig,
    AlignmentResult,
    AlignmentViolation,
    AlignmentPrinciple,
    ViolationSeverity,
)

# V12.4 COGNITIVE BOOST: Decision Logger
from .decision_logger import (
    GovernanceDecisionLog,
    GovernanceDecision,
    DecisionPattern,
    DecisionLogStats,
    get_decision_logger,
    reset_decision_logger,
)

# V12.4 COGNITIVE BOOST: Alignment Journal
from .alignment_journal import (
    AlignmentJournal,
    VerificationEntry,
    ViolationEntry,
    TrustScore,
    JournalStats,
    get_alignment_journal,
    reset_alignment_journal,
)

__all__ = [
    # V12.4: Ethics & Alignment
    "AlignmentVerifier",
    "AlignmentConfig",
    "AlignmentResult",
    "AlignmentViolation",
    "AlignmentPrinciple",
    "ViolationSeverity",
    # V12.4 COGNITIVE BOOST: Decision Logger
    "GovernanceDecisionLog",
    "GovernanceDecision",
    "DecisionPattern",
    "DecisionLogStats",
    "get_decision_logger",
    "reset_decision_logger",
    # V12.4 COGNITIVE BOOST: Alignment Journal
    "AlignmentJournal",
    "VerificationEntry",
    "ViolationEntry",
    "TrustScore",
    "JournalStats",
    "get_alignment_journal",
    "reset_alignment_journal",
]
