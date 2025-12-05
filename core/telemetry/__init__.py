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

__all__ = [
    "TelemetryCollector",
    "MetricType",
    "TelemetryExporter",
    "BudgetTracker",
    "BudgetExceededError",
    "BudgetWarning",
    "get_budget_tracker",
]
