import warnings
import sys
import asyncio

# Filter warnings to ensure we see them
warnings.simplefilter("always", DeprecationWarning)

try:
    from core.fsm.hibernation_manager import HibernationManager, HibernationState

    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")

# Check for specific deprecated usages if known
import inspect

print(inspect.getsource(HibernationManager.enter_hibernate))
