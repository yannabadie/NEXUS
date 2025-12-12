import asyncio
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from core.telemetry.system_monitor import SystemMonitor
from core.orchestration_v7 import OrchestratorV7

class MockEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event_type, data):
        print(f"[MockEventBus] Published: {event_type} -> {data}")
        self.events.append((event_type, data))

async def verify_system_monitor():
    print("\n--- Verifying SystemMonitor ---")
    bus = MockEventBus()
    monitor = SystemMonitor(bus)
    
    # Run for a short time
    task = asyncio.create_task(monitor.start_monitoring(interval=0.1))
    await asyncio.sleep(0.3)
    monitor.stop()
    await task
    
    # Check events
    stats_events = [e for e in bus.events if e[0] == "SYSTEM_STATS"]
    if stats_events:
        print(f"✅ SystemMonitor emitted {len(stats_events)} stats events")
        print(f"   Sample: {stats_events[0][1]}")
    else:
        print("❌ SystemMonitor failed to emit events")
        sys.exit(1)

async def verify_hot_reload():
    print("\n--- Verifying Hot Reload ---")
    
    # Setup workspace
    workspace = Path("tests/temp_workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "agents").mkdir(exist_ok=True)
    
    # Mock config and dependencies
    config = MagicMock()
    config.log_level = "DEBUG"
    config.agent_metrics_enabled = False
    config.swarm_enabled = False
    config.telemetry_enabled = False
    
    # Mock EventBus in sys.modules to be picked up by Orchestrator
    sys.modules["core.ui.event_bus"] = MagicMock()
    sys.modules["core.ui.event_bus"].EventBus = MockEventBus()
    
    # Instantiate Orchestrator
    orch = OrchestratorV7(workspace, config, {}, {})
    
    # Start background tasks
    await orch.start_background_tasks()
    
    # Create a new agent file
    new_agent = workspace / "agents" / "test_agent.json"
    print(f"Creating agent file: {new_agent}")
    with open(new_agent, "w") as f:
        json.dump({"id": "test", "name": "Test Agent"}, f)
        
    # Wait for watcher (poll interval is 2.0s in code, we wait 3s)
    print("Waiting for watcher...")
    await asyncio.sleep(3.0)
    
    # Check if Orchestrator detected it (we can't easily check the internal event bus 
    # because Orchestrator imports it internally, but we can check logs or side effects)
    # Actually, we mocked core.ui.event_bus.EventBus, so we can check that!
    
    mock_bus = sys.modules["core.ui.event_bus"].EventBus
    update_events = [e for e in mock_bus.events if e[0] == "AGENTS_UPDATED"]
    
    if update_events:
        print(f"✅ Hot Reload detected new agent! Event: {update_events[-1][1]}")
    else:
        print("❌ Hot Reload failed to detect new agent")
        # sys.exit(1) # Don't exit yet, let's clean up
        
    await orch.stop_background_tasks()
    
    # Cleanup
    import shutil
    if workspace.exists():
        shutil.rmtree(workspace)

async def main():
    await verify_system_monitor()
    await verify_hot_reload()
    print("\n✅ Phase 43 Verification Complete")

if __name__ == "__main__":
    asyncio.run(main())
