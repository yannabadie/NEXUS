#!/usr/bin/env python3
"""Quick test for async_opencode_driver security fixes"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Test 1: Import the modules
print("Test 1: Importing modules...")
try:
    from core.drivers.async_opencode_driver import (
        AsyncOpenCodeDriver,
        AsyncOpenCodeCLIDriver,
        AsyncOpenCodeDriverConfig,
    )
    print("  ✓ Import successful")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Create driver with valid config
print("\nTest 2: Creating driver with valid config...")
try:
    config = AsyncOpenCodeDriverConfig(
        model="glm-4.7",
        workspace_path=Path(tempfile.mkdtemp())
    )
    driver = AsyncOpenCodeCLIDriver(config)
    print("  ✓ Valid config accepted")
except Exception as e:
    print(f"  ✗ Valid config rejected: {e}")
    sys.exit(1)

# Test 3: Block malicious model parameter
print("\nTest 3: Blocking malicious model parameter...")
try:
    config = AsyncOpenCodeDriverConfig(
        model="glm-4.7; rm -rf /",
        workspace_path=Path(tempfile.mkdtemp())
    )
    driver = AsyncOpenCodeCLIDriver(config)
    print("  ✗ Malicious config was accepted (FAIL)")
    sys.exit(1)
except ValueError as e:
    if "[SECURITY]" in str(e):
        print(f"  ✓ Malicious config blocked: {e}")
    else:
        print(f"  ✗ Wrong error type: {e}")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Unexpected error: {e}")
    sys.exit(1)

# Test 4: Test model sanitization
print("\nTest 4: Testing model sanitization...")
config = AsyncOpenCodeDriverConfig(
    model="glm-4.7",
    workspace_path=Path(tempfile.mkdtemp())
)
driver = AsyncOpenCodeCLIDriver(config)

test_cases = [
    ("glm-4.7", "glm-4.7"),
    ("glm-4.7; rm -rf /", "glm-47rm-rf"),
    ("../../model", "model"),
]

all_passed = True
for input_model, expected in test_cases:
    result = driver._sanitize_model_param(input_model)
    if result == expected:
        print(f"  ✓ {input_model} -> {result}")
    else:
        print(f"  ✗ {input_model} -> {result} (expected {expected})")
        all_passed = False

if not all_passed:
    sys.exit(1)

# Test 5: Test CLI path validation
print("\nTest 5: Testing CLI path validation...")
valid_paths = ["opencode", "glm-4.7"]
invalid_paths = ["opencode; rm -rf /", "../../malicious"]

for path in valid_paths:
    if driver._is_safe_cli_path(path):
        print(f"  ✓ Valid path accepted: {path}")
    else:
        print(f"  ✗ Valid path rejected: {path}")
        sys.exit(1)

for path in invalid_paths:
    if not driver._is_safe_cli_path(path):
        print(f"  ✓ Invalid path blocked: {path}")
    else:
        print(f"  ✗ Invalid path accepted: {path}")
        sys.exit(1)

print("\n" + "="*60)
print("All security tests PASSED! ✓")
print("="*60)
