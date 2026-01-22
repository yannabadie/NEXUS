import warnings
import sys
import asyncio
from datetime import datetime, timezone
import logging

# Enable all warnings
warnings.simplefilter("always")
logging.basicConfig(level=logging.DEBUG)

# Mocking redis to avoid connection errors if not running
try:
    import redis
    import redis.asyncio as redis_async
except ImportError:
    print("redis not installed")
    sys.exit(0)


async def main():
    print(f"Python {sys.version}")
    print(f"Redis version: {redis.__version__}")

    # Check redis from_url
    print("Checking redis commands...")

    try:
        r = redis_async.from_url("redis://localhost:6379", decode_responses=True)
        # We don't need real connection to check for client-side deprecations usually
        # But for commands we might need it.
        # However, checking if functions exist or are wrapped with warnings

        print("Checking srem...")
        # r.srem is a partial or bound method

        await r.close()
        print("Redis closed")
    except Exception as e:
        print(f"Redis error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
