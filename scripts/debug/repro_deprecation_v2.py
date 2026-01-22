import warnings
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

# Enable all warnings
warnings.simplefilter("always")

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

# Mock core.logging before importing story_shard
sys.modules["core.logging"] = MagicMock()
mock_logger = MagicMock()
sys.modules["core.logging"].get_logger.return_value = mock_logger


async def main():
    print("Importing StoryShardEngine...")
    try:
        from core.ncm.story_shard import StoryShardEngine

        print("Imported.")

        # Create a dummy audit file
        audit_path = Path("test_audit.md")
        # Using utf-8 explicitly
        audit_path.write_text(
            """
## 6.2 God Classes
| File | LOC | Issue | Priority |
|---|---|---|---|
| core/orchestration/fsm_handlers.py | 1838 | Monolithe | HIGH |

## Evolution TODOs
- core/evolution/manager.py:177
- core/evolution/manager.py:512
- core/evolution/manager.py:552

## Issue Counts
- bug_pattern: 6303
- type_error: 2913
- dead_code: 852
- dead_import: 410
- missing_doc: 124
- deprecation: 398

## Deprecation Patterns
- datetime.utcnow() -> datetime.now(timezone.utc)
""",
            encoding="utf-8",
        )

        engine = StoryShardEngine(audit_report_path=audit_path)
        print("Initialized.")

        # Run sharding
        stories = await engine.shard_audit_report()
        print(f"Generated {len(stories)} stories.")

        # Clean up
        audit_path.unlink()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
