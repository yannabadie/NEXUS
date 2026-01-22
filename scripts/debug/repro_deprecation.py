import warnings
import sys
import asyncio
from pathlib import Path

# Enable all warnings
warnings.simplefilter("always")

# Add project root to path
sys.path.insert(0, str(Path.cwd()))


async def main():
    print("Importing StoryShardEngine...")
    try:
        from core.ncm.story_shard import StoryShardEngine

        print("Imported.")

        # Mock audit report
        audit_path = Path("audit/ANALYSIS_EXHAUSTIVE_2026-01-21.md")
        # Ensure it exists or mock it
        if not audit_path.exists():
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text("Mock audit report")

        engine = StoryShardEngine(audit_report_path=audit_path)
        print("Initialized.")

        # Run sharding
        # await engine.shard_audit_report()
        # (This might fail if parsing logic is strict, but we just want to trigger deprecations)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
