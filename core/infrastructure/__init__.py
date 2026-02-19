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
    UserRole as SessionUserRole,  # Renamed to avoid conflict with db.UserRole
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

# Database exports
from core.infrastructure.db import (
    PlanTier,
    TenantStatus,
    Tenant,
    User,
    Workspace,
    Quota,
    DEFAULT_QUOTAS,
    create_quota_for_plan,
    get_engine,
    init_db,
    reset_engine,
    get_session,
    create_default_tenant,
    get_tenant_by_slug,
    get_tenant_quota,
    DEFAULT_DB_PATH,
    QueryPerformanceTracker,
    QueryRecord,
    TableProfile,
    QueryPerformanceStats,
    get_query_tracker,
    reset_query_tracker,
)

# Bootstrap exports
from core.infrastructure.bootstrap import (
    AutoBootstrap,
    ProjectAnalysis,
    SpawnedAgentLoader,
    SpawnedAgentConfig,
    discover_and_register_spawned_agents,
    BootstrapService,
    SpinoffService,
    _get_bootstrap_service,
    _get_spinoff_service,
    StartupAnalytics,
    BootStepRecord,
    ComponentProfile,
    StartupStats,
    get_startup_analytics,
    reset_startup_analytics,
)

__all__ = [
    # Context
    "SessionContext",
    "SessionUserRole",  # Renamed from UserRole to avoid conflict
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
    # Database
    "PlanTier",
    "TenantStatus",
    "Tenant",
    "User",
    "Workspace",
    "Quota",
    "DEFAULT_QUOTAS",
    "create_quota_for_plan",
    "get_engine",
    "init_db",
    "reset_engine",
    "get_session",
    "create_default_tenant",
    "get_tenant_by_slug",
    "get_tenant_quota",
    "DEFAULT_DB_PATH",
    "QueryPerformanceTracker",
    "QueryRecord",
    "TableProfile",
    "QueryPerformanceStats",
    "get_query_tracker",
    "reset_query_tracker",
    # Bootstrap
    "AutoBootstrap",
    "ProjectAnalysis",
    "SpawnedAgentLoader",
    "SpawnedAgentConfig",
    "discover_and_register_spawned_agents",
    "BootstrapService",
    "SpinoffService",
    "_get_bootstrap_service",
    "_get_spinoff_service",
    "StartupAnalytics",
    "BootStepRecord",
    "ComponentProfile",
    "StartupStats",
    "get_startup_analytics",
    "reset_startup_analytics",
]

__version__ = "12.4.0"
