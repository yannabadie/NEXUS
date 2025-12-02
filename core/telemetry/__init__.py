"""
NEXUS Telemetry Module

Simple file-based telemetry for tracking:
- API calls (tokens, latency, model)
- Session metrics
- Swarm collaboration metrics
- Error rates

V7 Sprint 10: Basic telemetry foundation
Future: Export to Langfuse, OTLP, or other backends
"""

from .metrics import TelemetryCollector, MetricType

__all__ = ["TelemetryCollector", "MetricType"]
