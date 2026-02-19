"""
NEXUS V9.5 Resilience Module

Provides circuit breaker, system health monitoring, and resilience patterns
for multi-agent orchestration.

Modules:
- circuit_breaker: Circuit breaker pattern for fault tolerance
- system_health: Unified health monitoring for V9.5 components
"""

from core.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    get_circuit_breaker
)

from core.infrastructure.resilience.system_health import (
    SystemHealth,
    HealthStatus,
    ComponentHealth,
    HealthReport,
    get_system_health,
    reset_system_health,
)

from core.infrastructure.resilience.rate_limiter import (
    RateLimiter,
    ProviderLimits,
    TokenBucket,
)

# V12.4: Checkpoint Manager
from core.infrastructure.resilience.checkpoint_manager import (
    CheckpointManager,
    Checkpoint,
    CheckpointInfo,
    RestoreResult,
    get_checkpoint_manager,
    reset_checkpoint_manager,
)

# V12.4: Request Deduplicator
from core.infrastructure.resilience.request_deduplicator import (
    RequestDeduplicator,
    DeduplicationEntry,
    CheckResult,
    DeduplicationStats,
    get_deduplicator,
    reset_deduplicator,
)

# V12.4 COGNITIVE BOOST: Resilience Event Tracker
from core.infrastructure.resilience.resilience_event_tracker import (
    ResilienceEventTracker,
    ResilienceEvent,
    EventTypeMetrics,
    TrackerStats as ResilienceTrackerStats,
    get_resilience_tracker,
    reset_resilience_tracker,
)

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitOpenError",
    "get_circuit_breaker",
    # System Health (V9.5)
    "SystemHealth",
    "HealthStatus",
    "ComponentHealth",
    "HealthReport",
    "get_system_health",
    "reset_system_health",
    # V12.4: Rate Limiter
    "RateLimiter",
    "ProviderLimits",
    "TokenBucket",
    # V12.4: Checkpoint Manager
    "CheckpointManager",
    "Checkpoint",
    "CheckpointInfo",
    "RestoreResult",
    "get_checkpoint_manager",
    "reset_checkpoint_manager",
    # V12.4: Request Deduplicator
    "RequestDeduplicator",
    "DeduplicationEntry",
    "CheckResult",
    "DeduplicationStats",
    "get_deduplicator",
    "reset_deduplicator",
    # V12.4 COGNITIVE BOOST: Resilience Event Tracker
    "ResilienceEventTracker",
    "ResilienceEvent",
    "EventTypeMetrics",
    "ResilienceTrackerStats",
    "get_resilience_tracker",
    "reset_resilience_tracker",
    # V12.4 COGNITIVE BOOST: Runtime Waste Filter (arxiv:2510.26585)
    "RuntimeWasteFilter",
    "ExchangeRecord",
    "Intervention",
    "InterventionType",
    "InterventionAction",
    "FilterStats",
    "get_runtime_waste_filter",
    "reset_runtime_waste_filter",
]

# V12.4 COGNITIVE BOOST: Runtime Waste Filter (arxiv:2510.26585)
from core.infrastructure.resilience.runtime_waste_filter import (
    RuntimeWasteFilter,
    ExchangeRecord,
    Intervention,
    InterventionType,
    InterventionAction,
    FilterStats,
    get_runtime_waste_filter,
    reset_runtime_waste_filter,
)

__version__ = "12.4.0"
