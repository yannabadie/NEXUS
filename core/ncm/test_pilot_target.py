"""
Test file for NCM Pilot - contains intentional dead imports for testing.

This file exists solely to validate NCM pilot execution with SimpleExecutor.
"""

from typing import Optional, Dict, List, Set, Tuple, Union, cast
from pathlib import Path
import sys


def hello_world():
    """Test function with minimal imports used."""
    message: str = "Hello from NCM Pilot test"
    path: Path = Path(__file__)
    print(f"{message}: {path}")
    return True


if __name__ == "__main__":
    hello_world()
