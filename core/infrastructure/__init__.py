"""
NEXUS V12.4 - Infrastructure Package

Consolidated infrastructure components:
- context: Multi-tenant session management and audit trails
- db: Database engine, query tracking, and connection management
- session: Session analytics and lifecycle management
- resilience: Circuit breaker, retry logic, rate limiting
- bootstrap: Bootstrap analytics and startup diagnostics

P5.6 Phase 2: Package consolidation for reduced cognitive load.
"""

# Context exports
from core.infrastructure.context import (
    SessionContext,
    UserRole,
    current_session,
    get_current_session,
    get_current_session_or_none,
    has_active_session,
    use_context,
    use_context_async,
    require_context,
    get_default_context,
    ensure_context,
    DEFAULT_TENANT_ID,
    DEFAULT_USER_ID,
    DEFAULT_WORKSPACE_ID,
    ContextAuditTrail,
    AuditEntry,
    AuditStats,
    get_audit_trail,
    reset_audit_trail,
)

__all__ = [
    # Context
    "SessionContext",
    "UserRole",
    "current_session",
    "get_current_session",
    "get_current_session_or_none",
    "has_active_session",
    "use_context",
    "use_context_async",
    "require_context",
    "get_default_context",
    "ensure_context",
    "DEFAULT_TENANT_ID",
    "DEFAULT_USER_ID",
    "DEFAULT_WORKSPACE_ID",
    "ContextAuditTrail",
    "AuditEntry",
    "AuditStats",
    "get_audit_trail",
    "reset_audit_trail",
]

__version__ = "12.4.0"
