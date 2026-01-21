"""
NEXUS V9.5 Resilience Module

Provides circuit breaker, system health monitoring, and resilience patterns
for multi-agent orchestration.

Modules:
- circuit_breaker: Circuit breaker pattern for fault tolerance
- system_health: Unified health monitoring for V9.5 components
"""

from core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    get_circuit_breaker
)

from core.resilience.system_health import (
    SystemHealth,
    HealthStatus,
    ComponentHealth,
    HealthReport,
    get_system_health,
    reset_system_health,
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
]

__version__ = "9.5.0"
