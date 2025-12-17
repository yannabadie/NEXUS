import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from core.agents.unified_registry import UnifiedAgentRegistry, AgentProvider, AgentDescriptor, AgentCapability
from core.bootstrap.agent_loader import SpawnedAgentLoader

def verify_spawn():
    print("Initializing registry...")
    registry = UnifiedAgentRegistry()
    
    workspace_path = Path("workspace")
    print(f"Scanning workspace: {workspace_path.absolute()}")
    
    loader = SpawnedAgentLoader(workspace_path)
    profiles = loader.discover_spawned_agents()
    
    print(f"Loader found {len(profiles)} profiles")
    
    for profile in profiles:
        print(f"Converting profile: {profile.agent_id}")
        
        # Map capabilities string to Enum
        caps = []
        for c in profile.capabilities:
            try:
                # Simple mapping based on string
                if "coding" in c: caps.append(AgentCapability.CODING)
                elif "research" in c: caps.append(AgentCapability.RESEARCH)
                elif "analysis" in c: caps.append(AgentCapability.ANALYSIS)
                elif "creative" in c: caps.append(AgentCapability.CREATIVE)
                else: caps.append(AgentCapability.GENERAL)
            except:
                caps.append(AgentCapability.GENERAL)
        
        descriptor = AgentDescriptor(
            id=profile.agent_id,
            provider=AgentProvider.SPAWNED,
            display_name=profile.agent_id.replace('_', ' ').title(),
            capabilities=caps,
            is_available=True
        )
        registry.register(descriptor)
    
    specialist = registry.get("python_specialist")
    if specialist:
        print(f"\nSUCCESS: Found {specialist.display_name}")
        print(f"Provider: {specialist.provider}")
        print(f"Capabilities: {specialist.capabilities}")
        return True
    else:
        print("\nFAILURE: Python Specialist not found in registry")
        return False

if __name__ == "__main__":
    try:
        if verify_spawn():
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
