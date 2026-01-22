
import sys
import os
import warnings

# Add the current directory to sys.path
sys.path.append(os.getcwd())

# Enable all warnings
warnings.simplefilter("always")

print("Importing core.ncm.story_shard...")
try:
    from pathlib import Path
    import core.logging
    
    # Initialize logger
    workspace_path = Path(os.getcwd()) / "workspace"
    workspace_path.mkdir(exist_ok=True)
    core.logging.init_logger(workspace_path)
    
    import core.ncm.story_shard
    print("Import successful.")
    
    print("Instantiating StoryShardEngine...")
    engine = core.ncm.story_shard.StoryShardEngine(Path("audit/ANALYSIS_EXHAUSTIVE_2026-01-21.md"))
    print("Instantiation successful.")
except Exception as e:
    print(f"Import failed: {e}")
