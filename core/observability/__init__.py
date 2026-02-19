"""
NEXUS V12.4 - Observability Package

Consolidated observability components:
- audit: Audit logging and models
- events: Event bus, analytics, and telemetry bridge
- logging: Structured logging (driver and system loggers)
- telemetry: Metrics, profiling, budget tracking, OTel

P5.6 Phase 1: Package consolidation for reduced cognitive load.
"""

# Audit exports
from core.observability.audit import (
    AuditLogger,
    AuditLog,
    HITLRequest,
    get_audit_logger,
)

__all__ = [
    # Audit
    "AuditLogger",
    "AuditLog",
    "HITLRequest",
    "get_audit_logger",
]

__version__ = "12.4.0"
