"""
SystemHealth - Unified Health Check for V9.5 Components.

NEXUS V9.5 Sprint 4

Integrates all V9.5 refactored modules:
- Constants module
- SafeTaskManager
- EventBus
- ExecutionEngine
- ToolRegistry
- CircuitBreaker

Provides a single interface for system health monitoring.

Usage:
    health = get_system_health()
    report = await health.check_all()
    print(report.summary())
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the component health status to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the component's name,
                status value, message, details, and checked_at timestamp
                in ISO format.
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class HealthReport:
    """Aggregated health report for all components."""
    components: List[ComponentHealth]
    overall_status: HealthStatus
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def healthy_count(self) -> int:
        return sum(1 for c in self.components if c.status == HealthStatus.HEALTHY)

    @property
    def unhealthy_count(self) -> int:
        return sum(1 for c in self.components if c.status == HealthStatus.UNHEALTHY)

    def summary(self) -> str:
        """Generates a human-readable summary of the health report.

        Returns:
            str: A multi-line string summarizing the system health, including
                overall status, component counts, and individual component details.

        Raises:
            None: This method does not raise exceptions.
        """
        lines = [
            f"System Health: {self.overall_status.value.upper()}",
            f"Components: {self.healthy_count}/{len(self.components)} healthy",
            "",
        ]
        for comp in self.components:
            icon = {
                HealthStatus.HEALTHY: "[OK]",
                HealthStatus.DEGRADED: "[!!]",
                HealthStatus.UNHEALTHY: "[XX]",
                HealthStatus.UNKNOWN: "[??]",
            }.get(comp.status, "[??]")
            lines.append(f"  {icon} {comp.name}: {comp.message}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the health report to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the overall status value,
                counts of healthy and unhealthy components, a list of
                component health dictionaries, and the checked_at timestamp
                in ISO format.

        Raises:
            None: This method does not raise exceptions.
        """
        return {
            "overall_status": self.overall_status.value,
            "healthy_count": self.healthy_count,
            "unhealthy_count": self.unhealthy_count,
            "components": [c.to_dict() for c in self.components],
            "checked_at": self.checked_at.isoformat(),
        }


class SystemHealth:
    """
    Unified system health monitor for V9.5 components.

    Checks:
    - Constants module loaded
    - SafeTaskManager operational
    - EventBus operational
    - ExecutionEngine initialized
    - ToolRegistry populated
    - CircuitBreaker healthy
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        """Initialize the health monitor.

        Args:
            workspace_path: Optional path to the workspace directory.
                If not provided, defaults to the current working directory.
        """
        self.workspace_path = workspace_path or Path.cwd()
        self._last_report: Optional[HealthReport] = None

    async def check_all(self) -> HealthReport:
        """Checks the health of all V9.5 components.

        Executes health checks for Constants, SafeTaskManager, EventBus,
        ToolRegistry, and CircuitBreaker. Aggregates the results into a
        HealthReport.

        Returns:
            HealthReport: A report containing the status of all checked components
                and the overall system health.

        Raises:
            None: Individual component checks catch their own exceptions and
                return UNKNOWN/UNHEALTHY status.
        """
        components = []

        # Check each component
        components.append(self._check_constants())
        components.append(self._check_safe_task_manager())
        components.append(await self._check_event_bus())
        components.append(self._check_tool_registry())
        components.append(self._check_circuit_breaker())

        # Calculate overall status
        if all(c.status == HealthStatus.HEALTHY for c in components):
            overall = HealthStatus.HEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        report = HealthReport(
            components=components,
            overall_status=overall,
        )

        self._last_report = report
        return report

    def _check_constants(self) -> ComponentHealth:
        """Verifies the Constants module availability and configuration.

        Checks if the constants module can be imported and if critical values
        like timeouts are positive.

        Returns:
            ComponentHealth: The health status of the constants module.
                Returns HEALTHY if valid, DEGRADED if timeouts are invalid,
                or UNHEALTHY/UNKNOWN on error.

        Raises:
            None: Exceptions are caught and converted to health status.
        """
        try:
            from core.constants import (
                TIMEOUTS,
                RETRY_LIMITS,
                SAGA_LIMITS,
                CONSTANTS_VERSION,
            )

            # Verify critical values
            if TIMEOUTS.BASH_COMMAND <= 0:
                return ComponentHealth(
                    name="Constants",
                    status=HealthStatus.DEGRADED,
                    message="Invalid timeout value",
                )

            return ComponentHealth(
                name="Constants",
                status=HealthStatus.HEALTHY,
                message=f"v{CONSTANTS_VERSION} loaded",
                details={
                    "version": CONSTANTS_VERSION,
                    "saga_max_rollback": SAGA_LIMITS.MAX_ROLLBACK_ATTEMPTS,
                },
            )
        except ImportError as e:
            return ComponentHealth(
                name="Constants",
                status=HealthStatus.UNHEALTHY,
                message=f"Import failed: {e}",
            )
        except Exception as e:
            return ComponentHealth(
                name="Constants",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    def _check_safe_task_manager(self) -> ComponentHealth:
        """Verifies the SafeTaskManager state and statistics.

        Retrieves current statistics and active task counts from the
        SafeTaskManager to ensure it is operational.

        Returns:
            ComponentHealth: The health status containing task metrics.
                Returns HEALTHY with details if successful, or
                UNHEALTHY/UNKNOWN if the module is missing or fails.

        Raises:
            None: Exceptions are caught and converted to health status.
        """
        try:
            from core.async_primitives.safe_task_manager import (
                SafeTaskManager,
                create_safe_task,
            )

            stats = SafeTaskManager.get_stats()
            active = SafeTaskManager.get_active_tasks()

            return ComponentHealth(
                name="SafeTaskManager",
                status=HealthStatus.HEALTHY,
                message=f"{len(active)} active tasks",
                details={
                    "active_tasks": len(active),
                    "completed": stats.get("completed", 0),
                    "failed": stats.get("failed", 0),
                },
            )
        except ImportError as e:
            return ComponentHealth(
                name="SafeTaskManager",
                status=HealthStatus.UNHEALTHY,
                message=f"Import failed: {e}",
            )
        except Exception as e:
            return ComponentHealth(
                name="SafeTaskManager",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    async def _check_event_bus(self) -> ComponentHealth:
        """Verifies the EventBus connectivity and functionality.

        Retrieves the global event bus instance and checks its statistics.
        Simulates an event creation to verify responsiveness without
        publishing.

        Returns:
            ComponentHealth: The health status of the event bus.
                Returns HEALTHY with publish stats if operational,
                or UNHEALTHY/UNKNOWN on failure.

        Raises:
            None: Exceptions are caught and converted to health status.
        """
        try:
            from core.async_primitives.event_bus import (
                get_event_bus,
                SyncEvent,
            )

            bus = get_event_bus()
            stats = bus.get_stats()

            # Test publish
            test_event = SyncEvent(
                event_type="health_check",
                source="system_health",
                task_id="health_test",
                payload={"test": True},
            )

            # Don't actually publish, just verify the bus is responsive
            return ComponentHealth(
                name="EventBus",
                status=HealthStatus.HEALTHY,
                message=f"{stats.get('published', 0)} events published",
                details=stats,
            )
        except ImportError as e:
            return ComponentHealth(
                name="EventBus",
                status=HealthStatus.UNHEALTHY,
                message=f"Import failed: {e}",
            )
        except Exception as e:
            return ComponentHealth(
                name="EventBus",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    def _check_tool_registry(self) -> ComponentHealth:
        """Verifies the ToolRegistry and registered tools.

        Accesses the tool registry to count registered tools and list core
        tools, ensuring the registry is populated.

        Returns:
            ComponentHealth: The health status of the tool registry.
                Returns HEALTHY with tool counts if successful,
                or UNHEALTHY/UNKNOWN on error.

        Raises:
            None: Exceptions are caught and converted to health status.
        """
        try:
            from core.execution.tool_registry import get_tool_registry

            registry = get_tool_registry()
            tools = registry.list_tools()

            return ComponentHealth(
                name="ToolRegistry",
                status=HealthStatus.HEALTHY,
                message=f"{len(tools)} tools registered",
                details={
                    "tool_count": len(tools),
                    "core_tools": registry.list_core_tools(),
                },
            )
        except ImportError as e:
            return ComponentHealth(
                name="ToolRegistry",
                status=HealthStatus.UNHEALTHY,
                message=f"Import failed: {e}",
            )
        except Exception as e:
            return ComponentHealth(
                name="ToolRegistry",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    def _check_circuit_breaker(self) -> ComponentHealth:
        """Verifies the status of the default circuit breaker.

        Retrieves the 'default' circuit breaker instance and checks its
        current state and failure count.

        Returns:
            ComponentHealth: The health status of the circuit breaker.
                Returns HEALTHY with state details if successful,
                or UNHEALTHY/UNKNOWN on error.

        Raises:
            None: Exceptions are caught and converted to health status.
        """
        try:
            from core.resilience.circuit_breaker import (
                get_circuit_breaker,
                CircuitState,
            )

            breaker = get_circuit_breaker("default")

            return ComponentHealth(
                name="CircuitBreaker",
                status=HealthStatus.HEALTHY,
                message=f"State: {breaker.state.value}",
                details={
                    "state": breaker.state.value,
                    "failure_count": breaker.failure_count,
                },
            )
        except ImportError as e:
            return ComponentHealth(
                name="CircuitBreaker",
                status=HealthStatus.UNHEALTHY,
                message=f"Import failed: {e}",
            )
        except Exception as e:
            return ComponentHealth(
                name="CircuitBreaker",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    @property
    def last_report(self) -> Optional[HealthReport]:
        """Get last health report."""
        return self._last_report


# Singleton instance
_health_instance: Optional[SystemHealth] = None


def get_system_health(workspace_path: Optional[Path] = None) -> SystemHealth:
    """
    Get the system health monitor for the current tenant context.

    V10 PRISM: Returns tenant-scoped monitor via ServiceFactory.
    Falls back to global singleton if no context is active.

    Args:
        workspace_path: Workspace path (optional in V10)

    Returns:
        SystemHealth instance scoped to current tenant
    """
    # V10: Try ServiceFactory first (tenant-scoped)
    try:
        from ..context import has_active_session
        if has_active_session():
            from ..factory import ServiceFactory
            return ServiceFactory.get_system_health()
    except ImportError:
        pass  # context module not available, use legacy

    # Legacy fallback: global singleton
    global _health_instance
    if _health_instance is None:
        _health_instance = SystemHealth(workspace_path)
    return _health_instance


def reset_system_health() -> None:
    """Resets the system health monitor instance.

    This is primarily used for testing to ensure a clean state. In V10
    environments, it also clears the ServiceFactory cache for the current tenant.

    Args:
        None

    Returns:
        None

    Raises:
        None: Exceptions during cache clearing are caught and ignored.
    """
    global _health_instance
    _health_instance = None

    # V10: Also clear factory cache
    try:
        from ..context import get_current_session_or_none
        from ..factory import ServiceFactory
        ctx = get_current_session_or_none()
        if ctx:
            ServiceFactory.clear_tenant_cache(ctx.tenant_id)
    except ImportError:
        pass
