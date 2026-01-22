import warnings
import sys
import os

# Ensure we can import from core
sys.path.append(os.getcwd())

from core.telemetry.metrics import TelemetryCollector, MetricType

# Enable all warnings
warnings.simplefilter("always")

print("Initializing TelemetryCollector...")
telemetry = TelemetryCollector()
print("Initialized.")

print("Recording API call...")
telemetry.record_api_call("gemini", "gemini-pro", 100, 100)
print("Recorded.")

print("Recording Swarm Task...")
telemetry.record_swarm_task("ping_pong", 3, 5.0, True)

print("Getting summary...")
summary = telemetry.get_session_summary()
print("Summary got.")
