"""
Trigger Evolution - Headless Script
Objective: Trigger a single evolution cycle to test the V7 architecture fixes.
"""
import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent))

from core.interface.repl import InteractiveNexusV7
from core.config import load_config

def trigger_evolution():
    print("🚀 Triggering Headless Evolution Cycle...")
    
    # Initialize with CORRECT workspace path structure
    # REPL expects workspace to be inside NEXUS_V7_CHRYSALIS usually, 
    # or at least lineage.py expects workspace.parent.parent to be the repo root.
    # Repo Root = C:\Code\NEXUS\20_NEXUS - Copie
    # Lineage expects: workspace.parent.parent = Repo Root
    # So workspace must be at: Repo Root / Something / workspace
    
    # Let's point to the real workspace inside NEXUS_V7_CHRYSALIS
    current_dir = Path.cwd() # 20_NEXUS - Copie
    workspace_path = current_dir / "NEXUS_V7_CHRYSALIS" / "workspace"
    
    print(f"DEBUG: Workspace path: {workspace_path}")
    print(f"DEBUG: Expected Lineage path: {workspace_path.parent.parent / 'LINEAGE.json'}")
    
    config = load_config()
    
    # Mock user info
    gemini_info = {"model": "gemini-3-pro-preview", "version": "headless"}
    claude_info = {"model": "claude-sonnet-4.5", "version": "headless"}
    
    # Create REPL instance
    try:
        repl = InteractiveNexusV7(workspace_path, gemini_info, claude_info)
        
        # Ensure workspace structure exists
        (workspace_path / "_IO_BUFFER").mkdir(parents=True, exist_ok=True)
        (workspace_path / ".nexus").mkdir(parents=True, exist_ok=True)
        
        # Inject command directly via handle_command
        print("-> Injecting command: /evolve 1")
        repl.handle_command("/evolve 1")
        print("✅ Evolution cycle completed (or timeout).")
        
    except Exception as e:
        print(f"❌ Evolution cycle failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trigger_evolution()
