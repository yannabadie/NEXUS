
import warnings
import sys
import logging
import asyncio

# Enable all warnings
warnings.simplefilter("always")

# Capture warnings
logging.basicConfig(level=logging.DEBUG)

async def main():
    print("Importing core.workflow.redis_registry")
    try:
        from core.workflow.redis_registry import RedisWorkflowRegistry, WorkflowStatus
        print("Imported.")
        
        registry = RedisWorkflowRegistry()
        print("Instantiated.")
        
        # Trigger some methods
        registry.configure(use_redis=False)
        await registry.connect()
        
        wf = await registry.create_workflow("wf1", "tenant1", "task1")
        print(f"Created: {wf}")
        
        await registry.update_status("wf1", "tenant1", "running")
        
        await registry.cleanup_expired()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
