"""
NEXUS Governance & Security

Handles GCP access control, red team testing, and sandboxing.

Modules:
- gcp_gatekeeper.py: GCP access validation and ROI checks
- red_team.py: Alignment testing with trap questions
- sandbox.py: Filesystem and network isolation
"""

from .gcp_gatekeeper import *
from .red_team import *
from .sandbox import *

__all__ = [
    "request_gcp_access",
    "is_approved",
    "log_gcp_usage",
    "revoke_access",
    "load_trap_questions",
    "ask_trap",
    "detect_deception",
    "terminate_lineage",
    "enforce_isolation",
    "can_connect"
]
