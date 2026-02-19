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

# Logging exports
from core.observability.logging import (
    NexusLogger,
    LogLevel,
    EventType,
    init_logger,
    get_logger,
    cleanup_old_logs,
    get_driver_logger,
    configure_driver_logging,
    DriverLogger,
)

# Telemetry exports
from core.observability.telemetry import (
    TelemetryCollector,
    MetricType,
    TelemetryExporter,
    BudgetTracker,
    BudgetExceededError,
    BudgetWarning,
    get_budget_tracker,
    TelemetryService,
    BudgetService,
    ServiceResult,
    _get_telemetry_service,
    _get_budget_service,
    RedisLogHandler,
    create_redis_log_handler,
    init_otel,
    get_tracer,
    get_meter,
    trace_llm_call,
    trace_fsm_transition,
    HealthAggregator,
    HealthCheck,
    HealthReport,
    TelemetrySummary,
    AggregateStatus,
    PerformanceProfiler,
    TimingRecord,
    TimingStats,
    Bottleneck,
    ProfileReport,
    get_profiler,
    reset_profiler,
    ErrorPatternAnalyzer,
    ErrorRecord,
    ErrorCategoryMetrics,
    ErrorPattern,
    ErrorAnalyzerStats,
    get_error_analyzer,
    reset_error_analyzer,
)

# Events exports
from core.observability.events import (
    CerebroEvent,
    CerebroEventType,
    RedisEventBus,
    get_redis_bus,
    reset_redis_bus,
    TelemetryBridge,
    get_telemetry_bridge,
    reset_telemetry_bridge,
    EventAnalytics,
    EventRecord,
    EventTypeMetrics,
    EventAnalyticsStats,
    get_event_analytics,
    reset_event_analytics,
)

__all__ = [
    # Audit
    "AuditLogger",
    "AuditLog",
    "HITLRequest",
    "get_audit_logger",
    # Logging
    "NexusLogger",
    "LogLevel",
    "EventType",
    "init_logger",
    "get_logger",
    "cleanup_old_logs",
    "get_driver_logger",
    "configure_driver_logging",
    "DriverLogger",
    # Telemetry
    "TelemetryCollector",
    "MetricType",
    "TelemetryExporter",
    "BudgetTracker",
    "BudgetExceededError",
    "BudgetWarning",
    "get_budget_tracker",
    "TelemetryService",
    "BudgetService",
    "ServiceResult",
    "_get_telemetry_service",
    "_get_budget_service",
    "RedisLogHandler",
    "create_redis_log_handler",
    "init_otel",
    "get_tracer",
    "get_meter",
    "trace_llm_call",
    "trace_fsm_transition",
    "HealthAggregator",
    "HealthCheck",
    "HealthReport",
    "TelemetrySummary",
    "AggregateStatus",
    "PerformanceProfiler",
    "TimingRecord",
    "TimingStats",
    "Bottleneck",
    "ProfileReport",
    "get_profiler",
    "reset_profiler",
    "ErrorPatternAnalyzer",
    "ErrorRecord",
    "ErrorCategoryMetrics",
    "ErrorPattern",
    "ErrorAnalyzerStats",
    "get_error_analyzer",
    "reset_error_analyzer",
    # Events
    "CerebroEvent",
    "CerebroEventType",
    "RedisEventBus",
    "get_redis_bus",
    "reset_redis_bus",
    "TelemetryBridge",
    "get_telemetry_bridge",
    "reset_telemetry_bridge",
    "EventAnalytics",
    "EventRecord",
    "EventTypeMetrics",
    "EventAnalyticsStats",
    "get_event_analytics",
    "reset_event_analytics",
]

__version__ = "12.4.0"
