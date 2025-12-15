"""
V9.3 ISSUE-007: Circuit Breaker Pattern for NEXUS

Prevents cascading failures when agent invocations repeatedly fail.
Implements exponential backoff with three states: CLOSED, OPEN, HALF_OPEN.

Research Sources:
- aiobreaker: https://github.com/arlyon/aiobreaker
- Python backoff: https://github.com/litl/backoff
- Microsoft AI Agent Patterns: Failure isolation best practices

Usage:
    breaker = get_circuit_breaker("gemini")

    try:
        result = await breaker.call(agent.invoke, prompt)
    except CircuitOpenError as e:
        # Circuit is open - don't retry, use fallback
        logger.warning(f"Circuit open: {e.time_until_retry}s until retry")
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Callable, Any, Optional, Dict
import asyncio
import logging
import time


logger = logging.getLogger("nexus.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation - requests pass through
    OPEN = "open"          # Failures exceeded threshold - requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and call is rejected."""

    def __init__(self, name: str, time_until_retry: float, failure_count: int):
        self.name = name
        self.time_until_retry = time_until_retry
        self.failure_count = failure_count
        super().__init__(
            f"Circuit '{name}' is OPEN. {failure_count} consecutive failures. "
            f"Retry in {time_until_retry:.1f}s"
        )


@dataclass
class CircuitBreaker:
    """
    Circuit breaker with exponential backoff for agent invocations.

    V9.3: Prevents cascading failures between FSM → HiveMind → Swarm layers.

    States:
        CLOSED: Normal operation. Failures increment counter.
        OPEN: Too many failures. Requests rejected with CircuitOpenError.
        HALF_OPEN: After recovery_timeout, allow ONE request through.
                   Success → CLOSED, Failure → OPEN (with longer timeout)

    Attributes:
        name: Identifier for this circuit (e.g., "gemini", "claude", "swarm")
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery (HALF_OPEN)
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff (default 2.0)
    """
    name: str
    failure_threshold: int = 3
    recovery_timeout: float = 30.0
    max_backoff: float = 300.0
    backoff_multiplier: float = 2.0

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _last_failure_time: Optional[float] = field(default=None, repr=False)
    _current_backoff: float = field(default=30.0, repr=False)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def __post_init__(self):
        self._current_backoff = self.recovery_timeout

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self._current_backoff

    def _get_time_until_retry(self) -> float:
        """Get seconds until next retry attempt is allowed."""
        if self._last_failure_time is None:
            return 0.0

        elapsed = time.time() - self._last_failure_time
        remaining = self._current_backoff - elapsed
        return max(0.0, remaining)

    def _on_success(self):
        """Handle successful call - reset circuit to CLOSED."""
        with self._lock:
            logger.info(f"Circuit '{self.name}': Success - resetting to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._current_backoff = self.recovery_timeout
            self._last_failure_time = None

    def _on_failure(self, error: Exception):
        """Handle failed call - increment counter, potentially open circuit."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery attempt - increase backoff
                self._current_backoff = min(
                    self._current_backoff * self.backoff_multiplier,
                    self.max_backoff
                )
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit '{self.name}': Recovery failed - OPEN "
                    f"(backoff: {self._current_backoff:.1f}s)"
                )

            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit '{self.name}': Threshold reached ({self._failure_count}) - OPEN"
                )

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async or sync function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result if successful

        Raises:
            CircuitOpenError: If circuit is OPEN and retry time not elapsed
            Exception: Original exception from function (also trips circuit)
        """
        # Check if circuit allows the call
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    logger.info(f"Circuit '{self.name}': Attempting recovery (HALF_OPEN)")
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(
                        name=self.name,
                        time_until_retry=self._get_time_until_retry(),
                        failure_count=self._failure_count
                    )

        # Execute the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def call_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Synchronous version of call() for non-async contexts.

        Args:
            func: Sync function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result if successful

        Raises:
            CircuitOpenError: If circuit is OPEN
            Exception: Original exception from function
        """
        # Check if circuit allows the call
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    logger.info(f"Circuit '{self.name}': Attempting recovery (HALF_OPEN)")
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(
                        name=self.name,
                        time_until_retry=self._get_time_until_retry(),
                        failure_count=self._failure_count
                    )

        # Execute the call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def reset(self):
        """Manually reset circuit to CLOSED state."""
        with self._lock:
            logger.info(f"Circuit '{self.name}': Manual reset to CLOSED")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._current_backoff = self.recovery_timeout
            self._last_failure_time = None

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "current_backoff": self._current_backoff,
            "time_until_retry": self._get_time_until_retry(),
            "last_failure": self._last_failure_time
        }


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: float = 30.0,
    max_backoff: float = 300.0
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.

    Args:
        name: Identifier for the circuit (e.g., "gemini", "claude", "hivemind")
        failure_threshold: Failures before opening (default 3)
        recovery_timeout: Initial recovery wait time in seconds (default 30)
        max_backoff: Maximum backoff time (default 300s = 5 minutes)

    Returns:
        CircuitBreaker instance (shared by name)
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                max_backoff=max_backoff
            )
            logger.debug(f"Created circuit breaker '{name}'")

        return _circuit_breakers[name]


def reset_all_circuits():
    """Reset all circuit breakers (for testing or emergency recovery)."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()
        logger.info(f"Reset all {len(_circuit_breakers)} circuit breakers")


def get_all_circuit_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    with _registry_lock:
        return {
            name: breaker.get_status()
            for name, breaker in _circuit_breakers.items()
        }
