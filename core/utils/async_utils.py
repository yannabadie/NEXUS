"""
NEXUS V8.3.2 - Async Utilities

Provides helpers for async/sync interoperability.

TD-001: Extracted from duplicated patterns in tool_manager.py and repl.py.
"""
import asyncio
from typing import TypeVar, Coroutine, Any

T = TypeVar('T')


def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    Execute an async coroutine from a synchronous context.

    Handles the case where an event loop may or may not be running.

    Args:
        coro: The coroutine to execute

    Returns:
        The result of the coroutine

    Example:
        >>> async def fetch_data():
        ...     return {"status": "ok"}
        >>> result = run_sync(fetch_data())
        >>> print(result)
        {'status': 'ok'}
    """
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use run_until_complete
        # Instead, create a new thread to run the coroutine
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running event loop - safe to create one
        return asyncio.run(coro)


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get the current event loop or create a new one if none exists.

    Returns:
        The current or newly created event loop
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


async def run_in_thread(func, *args, **kwargs):
    """
    Run a synchronous function in a thread pool.

    Useful for wrapping blocking I/O operations in async code.

    Args:
        func: The synchronous function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        The result of the function
    """
    import functools
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(func, *args, **kwargs)
    )
