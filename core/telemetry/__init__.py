"""
NEXUS Telemetry Module

Simple file-based telemetry for tracking:
- API calls (tokens, latency, model)
- Session metrics
- Swarm collaboration metrics
- Error rates
- Budget/cost tracking (Phase 14d)

V7 Sprint 10: Basic telemetry foundation
V7.6 Phase 13c: Telemetry Export (CSV, reports)
V7.6 Phase 14d: Budget Cap & Cost Tracking
V9.1: Service Layer (TelemetryService, BudgetService)
Future: Export to Langfuse, OTLP, or other backends
"""

from .metrics import TelemetryCollector, MetricType
from .exporter import TelemetryExporter
from .budget_tracker import (
    BudgetTracker,
    BudgetExceededError,
    BudgetWarning,
    get_budget_tracker,
)

# V9.1: Service Layer
from .service import (
    TelemetryService,
    BudgetService,
    ServiceResult,
    _get_telemetry_service,
    _get_budget_service,
)

# V10 CEREBRO: Redis Log Bridge
from .redis_bridge import RedisLogHandler, create_redis_log_handler

# V12.4: OpenTelemetry Provider
from .otel_provider import (
    init_otel,
    get_tracer,
    get_meter,
    trace_llm_call,
    trace_fsm_transition,
)

# V12.4: Health Aggregator
from .health_aggregator import (
    HealthAggregator,
    HealthCheck,
    HealthReport,
    TelemetrySummary,
    AggregateStatus,
)

# V12.4: Performance Profiler
from .performance_profiler import (
    PerformanceProfiler,
    TimingRecord,
    TimingStats,
    Bottleneck,
    ProfileReport,
    get_profiler,
    reset_profiler,
)

# V12.4 COGNITIVE BOOST: Error Pattern Analyzer
from .error_pattern_analyzer import (
    ErrorPatternAnalyzer,
    ErrorRecord,
    ErrorCategoryMetrics,
    ErrorPattern,
    AnalyzerStats as ErrorAnalyzerStats,
    get_error_analyzer,
    reset_error_analyzer,
)

__all__ = [
    "TelemetryCollector",
    "MetricType",
    "TelemetryExporter",
    "BudgetTracker",
    "BudgetExceededError",
    "BudgetWarning",
    "get_budget_tracker",
    # V9.1: Service Layer
    "TelemetryService",
    "BudgetService",
    "ServiceResult",
    "_get_telemetry_service",
    "_get_budget_service",
    # V10 CEREBRO: Redis Log Bridge
    "RedisLogHandler",
    "create_redis_log_handler",
    # V12.4: OpenTelemetry
    "init_otel",
    "get_tracer",
    "get_meter",
    "trace_llm_call",
    "trace_fsm_transition",
    # V12.4: Health Aggregator
    "HealthAggregator",
    "HealthCheck",
    "HealthReport",
    "TelemetrySummary",
    "AggregateStatus",
    # V12.4: Performance Profiler
    "PerformanceProfiler",
    "TimingRecord",
    "TimingStats",
    "Bottleneck",
    "ProfileReport",
    "get_profiler",
    "reset_profiler",
    # V12.4 COGNITIVE BOOST: Error Pattern Analyzer
    "ErrorPatternAnalyzer",
    "ErrorRecord",
    "ErrorCategoryMetrics",
    "ErrorPattern",
    "ErrorAnalyzerStats",
    "get_error_analyzer",
    "reset_error_analyzer",
]
