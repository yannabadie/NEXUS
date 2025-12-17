import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.agents.unified_registry import UnifiedAgentRegistry, AgentDescriptor, AgentProvider
from core.bootstrap.agent_loader import discover_and_register_spawned_agents

def verify_standardization():
    print("Initializing V12 UnifiedAgentRegistry...")
    registry = UnifiedAgentRegistry()
    
    workspace_path = Path("workspace")
    print(f"Scanning workspace: {workspace_path.absolute()}")
    
    # NEW: Direct registration - no adapter needed!
    count = discover_and_register_spawned_agents(workspace_path, registry)
    print(f"Registered {count} agents directly into Registry.")
    
    # Verify QA Sentinel
    specialist = registry.get("qa_sentinel")
    if specialist:
        print(f"\nSUCCESS: Found {specialist.display_name}")
        print(f"Provider: {specialist.provider}")
        print(f"Capabilities: {specialist.capabilities}")
        print(f"Config Path: {specialist.config_path}")
        
        # Verify it's really an AgentDescriptor
        if isinstance(specialist, AgentDescriptor):
            print("Type Check: PASSED (is AgentDescriptor)")
            return True
        else:
            print(f"Type Check: FAILED (got {type(specialist)})")
            return False
    else:
        print("\nFAILURE: QA Sentinel not found in registry")
        return False

if __name__ == "__main__":
    try:
        if verify_standardization():
            print("VERIFICATION PASSED")
            sys.exit(0)
        else:
            print("VERIFICATION FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
