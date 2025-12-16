# NEXUS Documentation Generator - Validators Module
"""
Code validation and issue detection.

Classes:
    ConsistencyChecker: Checks for dead imports, missing docs, etc.
    DeadCodeDetector: Detects unused code
    DocDriftDetector: Detects outdated documentation
    BugPatternDetector: Detects suspicious code patterns
"""

from .consistency_checker import ConsistencyChecker
from .dead_code_detector import DeadCodeDetector
from .doc_drift_detector import DocDriftDetector
from .bug_pattern_detector import BugPatternDetector

__all__ = [
    "ConsistencyChecker",
    "DeadCodeDetector",
    "DocDriftDetector",
    "BugPatternDetector",
]
