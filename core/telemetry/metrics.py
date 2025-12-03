"""
NEXUS Telemetry Metrics Collector

Simple file-based telemetry that logs events to JSONL format.
Designed for future integration with Langfuse, OTLP, etc.

Usage:
    telemetry = TelemetryCollector(config)
    telemetry.record_api_call("gemini", "gemini-3-pro", 1500, 0.8, True)
    telemetry.record_swarm_task("ping_pong", 3, 5.2, True)

    # Get session summary
    summary = telemetry.get_session_summary()
"""

import json
import time
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from threading import Lock


class MetricType(Enum):
    """Types of metrics tracked"""
    API_CALL = "api_call"
    SWARM_TASK = "swarm_task"
    TOOL_EXECUTION = "tool_execution"
    ERROR = "error"
    SESSION = "session"
    EVOLUTION = "evolution"


@dataclass
class APICallMetric:
    """Metrics for a single API call"""
    timestamp: str
    provider: str  # gemini, claude
    model: str
    tokens_in: int
    tokens_out: int
    latency_seconds: float
    success: bool
    task_type: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SwarmTaskMetric:
    """Metrics for a Swarm task"""
    timestamp: str
    mode: str  # ping_pong, parallel, lead_support, etc.
    rounds: int
    duration_seconds: float
    success: bool
    agents_used: List[str] = None
    negotiation_turns: int = 0


@dataclass
class SessionMetric:
    """Metrics for a session"""
    session_id: str
    start_time: str
    total_api_calls: int
    total_tokens: int
    total_errors: int
    swarm_tasks: int
    tool_executions: int
    duration_seconds: float


class TelemetryCollector:
    """
    Collects and persists telemetry metrics.

    Thread-safe and designed for minimal overhead.
    """

    def __init__(self, config=None, output_file: Optional[Path] = None):
        """
        Initialize TelemetryCollector.

        Args:
            config: NEXUS config (uses telemetry_file if available)
            output_file: Override output file path
        """
        self.enabled = True
        if config:
            self.enabled = getattr(config, 'telemetry_enabled', True)
            default_file = getattr(config, 'telemetry_file', 'workspace/telemetry.jsonl')
            self.output_file = output_file or Path(default_file)
        else:
            self.output_file = output_file or Path("workspace/telemetry.jsonl")

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = time.time()
        self._lock = Lock()

        # In-memory counters for session summary
        self._api_calls = 0
        self._total_tokens = 0
        self._errors = 0
        self._swarm_tasks = 0
        self._tool_executions = 0

        # Ensure output directory exists
        if self.enabled:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def _write_event(self, event_type: MetricType, data: Dict[str, Any]):
        """Write an event to the telemetry file (thread-safe)"""
        if not self.enabled:
            return

        event = {
            "type": event_type.value,
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        with self._lock:
            try:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"[Telemetry] Write error: {e}")

    def record_api_call(
        self,
        provider: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_seconds: float = 0.0,
        success: bool = True,
        task_type: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Record an API call metric.

        Args:
            provider: "gemini" or "claude"
            model: Model name (e.g., "gemini-3-pro-preview")
            tokens_in: Input tokens
            tokens_out: Output tokens
            latency_seconds: Call duration
            success: Whether call succeeded
            task_type: Optional task type (brainstorm, tool, etc.)
            error: Error message if failed
        """
        self._api_calls += 1
        self._total_tokens += tokens_in + tokens_out
        if not success:
            self._errors += 1

        metric = APICallMetric(
            timestamp=datetime.utcnow().isoformat() + "Z",
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_seconds=latency_seconds,
            success=success,
            task_type=task_type,
            error=error
        )

        self._write_event(MetricType.API_CALL, asdict(metric))

    def record_swarm_task(
        self,
        mode: str,
        rounds: int,
        duration_seconds: float,
        success: bool,
        agents_used: Optional[List[str]] = None,
        negotiation_turns: int = 0
    ):
        """
        Record a Swarm task metric.

        Args:
            mode: Collaboration mode used
            rounds: Number of execution rounds
            duration_seconds: Total duration
            success: Whether task completed successfully
            agents_used: List of agent IDs that participated
            negotiation_turns: Turns spent in negotiation
        """
        self._swarm_tasks += 1
        if not success:
            self._errors += 1

        metric = SwarmTaskMetric(
            timestamp=datetime.utcnow().isoformat() + "Z",
            mode=mode,
            rounds=rounds,
            duration_seconds=duration_seconds,
            success=success,
            agents_used=agents_used or [],
            negotiation_turns=negotiation_turns
        )

        self._write_event(MetricType.SWARM_TASK, asdict(metric))

    def record_tool_execution(
        self,
        tool_name: str,
        duration_seconds: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record a tool execution metric"""
        self._tool_executions += 1
        if not success:
            self._errors += 1

        self._write_event(MetricType.TOOL_EXECUTION, {
            "tool_name": tool_name,
            "duration_seconds": duration_seconds,
            "success": success,
            "error": error
        })

    def record_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """Record an error event"""
        self._errors += 1

        self._write_event(MetricType.ERROR, {
            "error_type": error_type,
            "message": message,
            "context": context or {}
        })

    def record_evolution(
        self,
        generation: int,
        child_id: str,
        parent_score: float,
        child_score: float,
        promoted: bool,
        mutations: List[str]
    ):
        """Record an evolution cycle metric"""
        self._write_event(MetricType.EVOLUTION, {
            "generation": generation,
            "child_id": child_id,
            "parent_score": parent_score,
            "child_score": child_score,
            "improvement_pct": ((child_score - parent_score) / parent_score * 100) if parent_score > 0 else 0,
            "promoted": promoted,
            "mutations": mutations
        })

    def get_session_summary(self) -> SessionMetric:
        """Get summary metrics for the current session"""
        duration = time.time() - self.session_start

        return SessionMetric(
            session_id=self.session_id,
            start_time=datetime.fromtimestamp(self.session_start).isoformat(),
            total_api_calls=self._api_calls,
            total_tokens=self._total_tokens,
            total_errors=self._errors,
            swarm_tasks=self._swarm_tasks,
            tool_executions=self._tool_executions,
            duration_seconds=round(duration, 2)
        )

    def write_session_summary(self):
        """Write session summary to telemetry file"""
        summary = self.get_session_summary()
        self._write_event(MetricType.SESSION, asdict(summary))

    def print_summary(self):
        """Print session summary to console"""
        summary = self.get_session_summary()
        print(f"\n{'='*50}")
        print(f"TELEMETRY SESSION SUMMARY")
        print(f"{'='*50}")
        print(f"Session ID: {summary.session_id}")
        print(f"Duration: {summary.duration_seconds:.1f}s")
        print(f"API Calls: {summary.total_api_calls}")
        print(f"Total Tokens: {summary.total_tokens:,}")
        print(f"Swarm Tasks: {summary.swarm_tasks}")
        print(f"Tool Executions: {summary.tool_executions}")
        print(f"Errors: {summary.total_errors}")
        print(f"{'='*50}\n")


# Singleton instance for easy access
_collector: Optional[TelemetryCollector] = None


def get_telemetry(config=None) -> TelemetryCollector:
    """Get or create the global telemetry collector"""
    global _collector
    if _collector is None:
        _collector = TelemetryCollector(config)
    return _collector
