"""
NEXUS V5.0 - Comprehensive Logging System
Logging exhaustif de tous les événements pour analyse post-mortem.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(Enum):
    """Niveaux de log NEXUS."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"  # Ultra-verbose pour debugging


class NexusLogger:
    """Logger centralisé avec multiple outputs."""

    def __init__(self, workspace_path: Path, session_id: str):
        self.workspace_path = workspace_path
        self.session_id = session_id
        self.log_dir = workspace_path / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Multiple log files
        self.main_log = self.log_dir / f"nexus_session_{session_id}.log"
        self.events_log = self.log_dir / f"events_{session_id}.jsonl"
        self.cfl_log = self.log_dir / f"cfl_{session_id}.jsonl"
        self.errors_log = self.log_dir / f"errors_{session_id}.log"
        self.trace_log = self.log_dir / f"trace_{session_id}.log"

        # Initialize Python logger
        self.logger = logging.getLogger(f"NEXUS_{session_id}")
        self.logger.setLevel(logging.DEBUG)

        # File handlers
        self._setup_handlers()

        # Event counter
        self.event_counter = 0

    def _setup_handlers(self):
        """Configure all log handlers."""
        # Main log: Everything
        main_handler = logging.FileHandler(self.main_log, encoding='utf-8')
        main_handler.setLevel(logging.DEBUG)
        main_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        main_handler.setFormatter(main_format)
        self.logger.addHandler(main_handler)

        # Errors log: Only errors and critical
        error_handler = logging.FileHandler(self.errors_log, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(main_format)
        self.logger.addHandler(error_handler)

        # Trace log: Ultra-verbose
        trace_handler = logging.FileHandler(self.trace_log, encoding='utf-8')
        trace_handler.setLevel(logging.DEBUG)
        trace_format = logging.Formatter(
            '%(asctime)s.%(msecs)03d | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trace_handler.setFormatter(trace_format)
        self.logger.addHandler(trace_handler)

        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """Log structured event to JSONL."""
        self.event_counter += 1
        event = {
            "event_id": self.event_counter,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "level": level,
            "data": data
        }

        with open(self.events_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Also log to main logger
        self.logger.log(
            getattr(logging, level),
            f"[EVENT:{event_type}] {json.dumps(data, ensure_ascii=False)}"
        )

    def log_cfl_cycle(self, turn: int, phase: str, data: Dict[str, Any]):
        """Log CFL-specific events."""
        cfl_event = {
            "turn": turn,
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        with open(self.cfl_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(cfl_event, ensure_ascii=False) + "\n")

        self.log_event(f"CFL_{phase}", {"turn": turn, **data}, level="DEBUG")

    def log_agent_invocation(self, turn: int, agent: str, context_size: int, timeout: int):
        """Log agent invocation details."""
        self.log_event("AGENT_INVOCATION", {
            "turn": turn,
            "agent": agent,
            "context_size_bytes": context_size,
            "timeout_seconds": timeout
        })

    def log_agent_response(self, turn: int, agent: str, response: Dict, duration: float):
        """Log agent response details."""
        self.log_event("AGENT_RESPONSE", {
            "turn": turn,
            "agent": agent,
            "response_size_bytes": len(json.dumps(response)),
            "duration_seconds": duration,
            "action_type": response.get("action_type"),
            "status": response.get("status")
        })

    def log_tool_execution(self, turn: int, tool_name: str, arguments: Dict, result: Dict):
        """Log tool execution details."""
        self.log_event("TOOL_EXECUTION", {
            "turn": turn,
            "tool_name": tool_name,
            "arguments": arguments,
            "status": result.get("status"),
            "returncode": result.get("returncode"),
            "stdout_length": len(result.get("stdout", "")),
            "stderr_length": len(result.get("stderr", ""))
        })

    def log_validation(self, turn: int, validation_type: str, result: str, details: Optional[Dict] = None):
        """Log validation results."""
        self.log_event("VALIDATION", {
            "turn": turn,
            "validation_type": validation_type,
            "result": result,
            "details": details or {}
        })

    def log_state_change(self, turn: int, change_type: str, old_value: Any, new_value: Any):
        """Log state changes."""
        self.log_event("STATE_CHANGE", {
            "turn": turn,
            "change_type": change_type,
            "old_value": str(old_value),
            "new_value": str(new_value)
        }, level="DEBUG")

    def log_error(self, turn: int, error_type: str, error_msg: str, stacktrace: Optional[str] = None):
        """Log errors."""
        self.log_event("ERROR", {
            "turn": turn,
            "error_type": error_type,
            "error_message": error_msg,
            "stacktrace": stacktrace
        }, level="ERROR")

        self.logger.error(f"Turn {turn} - {error_type}: {error_msg}")
        if stacktrace:
            self.logger.error(f"Stacktrace:\n{stacktrace}")

    def log_panic(self, reason: str, turn: int):
        """Log panic events."""
        self.log_event("PANIC", {
            "turn": turn,
            "reason": reason
        }, level="CRITICAL")

        self.logger.critical(f"PANIC TRIGGERED at turn {turn}: {reason}")

    def log_memory_operation(self, turn: int, operation: str, details: Dict):
        """Log memory operations (save, load, compress, rollback)."""
        self.log_event("MEMORY_OPERATION", {
            "turn": turn,
            "operation": operation,
            "details": details
        }, level="DEBUG")

    def log_plan_health(self, turn: int, health_data: Dict):
        """Log plan health assessment."""
        self.log_event("PLAN_HEALTH", {
            "turn": turn,
            **health_data
        }, level="INFO")

    def log_stalemate(self, turn: int, counter: int, action: str):
        """Log stalemate detection."""
        self.log_event("STALEMATE", {
            "turn": turn,
            "counter": counter,
            "action": action
        }, level="WARNING")

    def log_resource_check(self, turn: int, cpu_percent: float, ram_percent: float, overloaded: bool):
        """Log resource monitoring."""
        self.log_event("RESOURCE_CHECK", {
            "turn": turn,
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "overloaded": overloaded
        }, level="DEBUG")

    def log_io_operation(self, turn: int, operation: str, file_path: str, size_bytes: int):
        """Log I/O operations."""
        self.log_event("IO_OPERATION", {
            "turn": turn,
            "operation": operation,
            "file_path": file_path,
            "size_bytes": size_bytes
        }, level="DEBUG")

    def info(self, message: str):
        """Standard info log."""
        self.logger.info(message)

    def debug(self, message: str):
        """Standard debug log."""
        self.logger.debug(message)

    def warning(self, message: str):
        """Standard warning log."""
        self.logger.warning(message)

    def error(self, message: str):
        """Standard error log."""
        self.logger.error(message)

    def critical(self, message: str):
        """Standard critical log."""
        self.logger.critical(message)

    def generate_summary(self) -> Dict[str, Any]:
        """Generate session summary from logs."""
        summary = {
            "session_id": self.session_id,
            "total_events": self.event_counter,
            "log_files": {
                "main": str(self.main_log),
                "events": str(self.events_log),
                "cfl": str(self.cfl_log),
                "errors": str(self.errors_log),
                "trace": str(self.trace_log)
            }
        }

        # Count events by type
        event_counts = {}
        if self.events_log.exists():
            with open(self.events_log, "r", encoding="utf-8") as f:
                for line in f:
                    event = json.loads(line)
                    event_type = event["event_type"]
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1

        summary["event_counts"] = event_counts

        return summary
