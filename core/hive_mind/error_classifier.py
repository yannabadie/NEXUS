"""
NEXUS V10 - Error Classifier for HiveMind Recovery

Provides structured error classification and remediation patterns
for Phase 5/6 error recovery in the HiveMind pipeline.

Addresses Gems critique: "Phase 5/6 retry logic depends on textual LLM recommendations"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List
import re
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Structured error categories for HiveMind."""
    # Recoverable errors
    TOOL_FAILURE = "tool_failure"          # Tool execution failed
    RESOURCE_NOT_FOUND = "resource_not_found"  # File/resource missing
    PERMISSION_DENIED = "permission_denied"    # Access denied
    TIMEOUT = "timeout"                    # Operation timed out
    RATE_LIMIT = "rate_limit"              # API rate limited
    
    # Partially recoverable
    PARSE_ERROR = "parse_error"            # JSON/response parse failed
    CONTEXT_OVERFLOW = "context_overflow"   # Too much context
    AGENT_DISAGREEMENT = "agent_disagreement"  # Agents can't agree
    
    # Non-recoverable
    INVALID_REQUEST = "invalid_request"     # Bad task input
    SECURITY_VIOLATION = "security_violation"  # Security check failed
    KERNEL_VIOLATION = "kernel_violation"   # KERNEL integrity failed
    UNKNOWN = "unknown"                    # Unclassified error


@dataclass
class ErrorClassification:
    """Classified error with remediation suggestion."""
    category: ErrorCategory
    severity: int  # 1-10, 10 = critical
    retryable: bool
    max_retries: int
    backoff_seconds: float
    remediation: str
    original_error: str


class ErrorClassifier:
    """
    Classify errors and suggest remediation without relying on LLM.
    
    V10: Replaces textual LLM-dependent error recovery with
    pattern-matching and structured responses.
    """
    
    # Pattern -> (category, severity, retryable, max_retries, backoff)
    ERROR_PATTERNS: Dict[str, tuple] = {
        # Tool failures
        r"file.*(not found|doesn't exist)": 
            (ErrorCategory.RESOURCE_NOT_FOUND, 5, True, 2, 1.0),
        r"permission denied|access denied":
            (ErrorCategory.PERMISSION_DENIED, 6, False, 0, 0),
        r"timeout|timed out":
            (ErrorCategory.TIMEOUT, 4, True, 3, 2.0),
        r"rate limit|too many requests":
            (ErrorCategory.RATE_LIMIT, 3, True, 3, 5.0),
            
        # Parse errors
        r"json.*error|parse.*error|expecting.*property":
            (ErrorCategory.PARSE_ERROR, 4, True, 2, 1.0),
        r"context.*overflow|token.*limit|too (long|large)":
            (ErrorCategory.CONTEXT_OVERFLOW, 6, True, 1, 0),
            
        # Agent issues
        r"consensus.*failed|agreement.*failed|disagree":
            (ErrorCategory.AGENT_DISAGREEMENT, 5, True, 1, 2.0),
            
        # Security
        r"security.*violation|kernel.*violation":
            (ErrorCategory.SECURITY_VIOLATION, 10, False, 0, 0),
        r"kernel.*integrity|immutability.*violated":
            (ErrorCategory.KERNEL_VIOLATION, 10, False, 0, 0),
    }
    
    REMEDIATION_STRATEGIES: Dict[ErrorCategory, str] = {
        ErrorCategory.TOOL_FAILURE: "Retry with simpler tool command",
        ErrorCategory.RESOURCE_NOT_FOUND: "Verify path exists before operation",
        ErrorCategory.PERMISSION_DENIED: "Skip operation or request user permission",
        ErrorCategory.TIMEOUT: "Retry with increased timeout or simpler request",
        ErrorCategory.RATE_LIMIT: "Wait and retry with exponential backoff",
        ErrorCategory.PARSE_ERROR: "Request structured JSON output explicitly",
        ErrorCategory.CONTEXT_OVERFLOW: "Summarize context and reduce scope",
        ErrorCategory.AGENT_DISAGREEMENT: "Use forced vote or single-agent fallback",
        ErrorCategory.INVALID_REQUEST: "Clarify task requirements with user",
        ErrorCategory.SECURITY_VIOLATION: "Abort - security constraint violated",
        ErrorCategory.KERNEL_VIOLATION: "FATAL - terminate immediately",
        ErrorCategory.UNKNOWN: "Log error and proceed with fallback approach",
    }
    
    def classify(self, error: Exception) -> ErrorClassification:
        """
        Classify an error and return remediation guidance.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorClassification with category, severity, and remediation
        """
        error_str = str(error).lower()
        
        # Match against patterns
        for pattern, (category, severity, retryable, max_retries, backoff) in self.ERROR_PATTERNS.items():
            if re.search(pattern, error_str, re.IGNORECASE):
                return ErrorClassification(
                    category=category,
                    severity=severity,
                    retryable=retryable,
                    max_retries=max_retries,
                    backoff_seconds=backoff,
                    remediation=self.REMEDIATION_STRATEGIES.get(category, "Unknown remediation"),
                    original_error=str(error)
                )
        
        # Default: unknown error
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            severity=5,
            retryable=True,
            max_retries=1,
            backoff_seconds=1.0,
            remediation=self.REMEDIATION_STRATEGIES[ErrorCategory.UNKNOWN],
            original_error=str(error)
        )
    
    def should_retry(self, classification: ErrorClassification, attempt: int) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            classification: The error classification
            attempt: Current attempt number (1-indexed)
            
        Returns:
            True if retry is recommended
        """
        if not classification.retryable:
            return False
        return attempt <= classification.max_retries
    
    def get_backoff(self, classification: ErrorClassification, attempt: int) -> float:
        """
        Get exponential backoff seconds for retry.
        
        Args:
            classification: The error classification
            attempt: Current attempt number
            
        Returns:
            Seconds to wait before retry
        """
        return classification.backoff_seconds * (2 ** (attempt - 1))


# Singleton instance
_error_classifier: Optional[ErrorClassifier] = None


def get_error_classifier() -> ErrorClassifier:
    """Get or create the error classifier singleton."""
    global _error_classifier
    if _error_classifier is None:
        _error_classifier = ErrorClassifier()
    return _error_classifier
