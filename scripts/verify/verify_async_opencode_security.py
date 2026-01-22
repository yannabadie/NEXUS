#!/usr/bin/env python3
"""
Verification script for security fixes in core/drivers/async_opencode_driver.py

This script demonstrates that the security issues have been fixed:
1. Command Injection via model parameter
2. Command Injection via CLI path
3. Unsafe prompt handling
"""

import sys
import tempfile
import asyncio
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.drivers.async_opencode_driver import (
    AsyncOpenCodeDriver,
    AsyncOpenCodeCLIDriver,
    AsyncOpenCodeDriverConfig,
)


def test_model_injection_protection():
    """Verify that command injection via model parameter is blocked."""
    print("[OK] Testing model parameter injection protection...")

    injection_attempts = [
        # Command injection attempts
        {"model": "glm-4.7; rm -rf /", "expected": False},
        {"model": "glm-4.7 && whoami", "expected": False},
        {"model": "glm-4.7 | cat /etc/passwd", "expected": False},
        {"model": "../../malicious/model", "expected": False},
        {"model": "glm-4.7\x00", "expected": False},
        
        # Valid models should pass
        {"model": "glm-4.7", "expected": True},
        {"model": "grok-code-fast-1", "expected": True},
        {"model": "minimax-m2.1", "expected": True},
    ]

    blocked = 0
    allowed = 0
    
    for attempt in injection_attempts:
        config = AsyncOpenCodeDriverConfig(
            model=attempt["model"],
            workspace_path=Path(tempfile.mkdtemp()),
            verbose=False,
        )
        
        expected = attempt["expected"]
        try:
            # Try to create driver - should raise ValueError for invalid configs
            driver = AsyncOpenCodeDriver(config)
            if expected:
                allowed += 1
            else:
                print(f"  - WARNING: Injection attempt should be blocked: {attempt['model']}")
        except ValueError as e:
            if "[SECURITY]" in str(e) and not expected:
                blocked += 1
            else:
                print(f"  - Unexpected error: {e}")
        
        # Also test CLI driver
        try:
            cli_driver = AsyncOpenCodeCLIDriver(config)
            if expected:
                allowed += 1
            else:
                print(f"  - WARNING: CLI driver injection attempt should be blocked: {attempt['model']}")
        except ValueError as e:
            if "[SECURITY]" in str(e) and not expected:
                blocked += 1
            else:
                print(f"  - Unexpected CLI error: {e}")

    # Each attempt tests both drivers, so divide by 2
    expected_blocked = len([a for a in injection_attempts if not a["expected"]]) * 2
    expected_allowed = len([a for a in injection_attempts if a["expected"]]) * 2
    
    print(f"  - Blocked {blocked}/{expected_blocked} injection attempts: {'PASS' if blocked == expected_blocked else 'FAIL'}")
    print(f"  - Allowed {allowed}/{expected_allowed} valid configs: {'PASS' if allowed == expected_allowed else 'FAIL'}")
    
    return blocked == expected_blocked and allowed == expected_allowed


def test_cli_path_validation():
    """Verify that CLI path validation works correctly."""
    print("\n[OK] Testing CLI path validation...")

    cli_driver = None
    
    # Valid CLI path
    try:
        config = AsyncOpenCodeDriverConfig(
            workspace_path=Path(tempfile.mkdtemp())
        )
        cli_driver = AsyncOpenCodeCLIDriver(config)
        print("  - Valid CLI path 'opencode' accepted: PASS")
        valid_pass = True
    except Exception as e:
        print(f"  - Valid CLI path rejected: FAIL - {e}")
        valid_pass = False
    
    if cli_driver:
        # Test the validation method directly
        invalid_paths = [
            "opencode; rm -rf /",
            "opencode && whoami",
            "opencode | cat /etc/passwd",
            "../../malicious/binary",
            "/etc/passwd",
        ]
        
        blocked = 0
        for path in invalid_paths:
            if not cli_driver._is_safe_cli_path(path):
                blocked += 1
        
        expected_blocked = len(invalid_paths)
        print(f"  - Blocked {blocked}/{expected_blocked} malicious CLI paths: {'PASS' if blocked == expected_blocked else 'FAIL'}")
        invalid_pass = blocked == expected_blocked
    else:
        invalid_pass = False
    
    return valid_pass and invalid_pass


def test_prompt_validation():
    """Verify that prompt validation works correctly."""
    print("\n[OK] Testing prompt validation...")
    
    config = AsyncOpenCodeDriverConfig(
        workspace_path=Path(tempfile.mkdtemp())
    )
    cli_driver = AsyncOpenCodeCLIDriver(config)
    
    # Valid prompts
    valid_prompts = [
        "Hello world",
        "Write a Python function to add two numbers",
        "A" * 1000,  # Large but valid
    ]
    
    # Invalid prompts
    invalid_prompts = [
        "Hello\x00world",  # Null byte
        "A" * (1024 * 1024 + 1),  # Too large (over 1MB)
    ]
    
    valid_pass = True
    for prompt in valid_prompts:
        if not cli_driver._is_safe_prompt(prompt):
            print(f"  - Valid prompt incorrectly rejected: FAIL")
            valid_pass = False
    
    if valid_pass:
        print(f"  - All {len(valid_prompts)} valid prompts accepted: PASS")
    
    invalid_pass = True
    blocked = 0
    for prompt in invalid_prompts:
        if not cli_driver._is_safe_prompt(prompt):
            blocked += 1
        else:
            print(f"  - Invalid prompt incorrectly accepted: FAIL")
            invalid_pass = False
    
    if invalid_pass:
        print(f"  - Blocked {blocked}/{len(invalid_prompts)} invalid prompts: PASS")
    
    return valid_pass and invalid_pass


def test_model_sanitization():
    """Verify that model parameter sanitization works correctly."""
    print("\n[OK] Testing model parameter sanitization...")
    
    config = AsyncOpenCodeDriverConfig(
        workspace_path=Path(tempfile.mkdtemp())
    )
    driver = AsyncOpenCodeDriver(config)
    cli_driver = AsyncOpenCodeCLIDriver(config)
    
    test_cases = [
        # (input, expected_output)
        ("glm-4.7", "glm-4.7"),
        ("grok-code-fast-1", "grok-code-fast-1"),
        ("glm-4.7; rm -rf /", "glm-47rm-rf"),  # Dangerous chars removed
        ("../../model", "model"),  # Path traversal removed
        ("model with spaces", "modelwithspaces"),  # Spaces removed
        ("model@#$%^&*()", "model"),  # Special chars removed
    ]
    
    http_pass = True
    cli_pass = True
    
    for input_model, expected in test_cases:
        http_sanitized = driver._sanitize_model_param(input_model)
        cli_sanitized = cli_driver._sanitize_model_param(input_model)
        
        if http_sanitized != expected:
            print(f"  - HTTP driver: {input_model} -> {http_sanitized} (expected {expected}): FAIL")
            http_pass = False
        
        if cli_sanitized != expected:
            print(f"  - CLI driver: {input_model} -> {cli_sanitized} (expected {expected}): FAIL")
            cli_pass = False
    
    if http_pass:
        print(f"  - HTTP driver sanitization: PASS ({len(test_cases)} tests)")
    
    if cli_pass:
        print(f"  - CLI driver sanitization: PASS ({len(test_cases)} tests)")
    
    return http_pass and cli_pass


async def test_http_driver_creation():
    """Verify that HTTP driver can be created with valid config."""
    print("\n[OK] Testing HTTP driver creation...")
    
    try:
        config = AsyncOpenCodeDriverConfig(
            server_url="http://localhost:5173",
            model="glm-4.7",
            workspace_path=Path(tempfile.mkdtemp()),
            verbose=False,
        )
        driver = AsyncOpenCodeDriver(config)
        print("  - HTTP driver created successfully: PASS")
        return True
    except Exception as e:
        print(f"  - HTTP driver creation failed: FAIL - {e}")
        return False


async def test_cli_driver_creation():
    """Verify that CLI driver can be created with valid config."""
    print("\n[OK] Testing CLI driver creation...")
    
    try:
        config = AsyncOpenCodeDriverConfig(
            model="glm-4.7",
            workspace_path=Path(tempfile.mkdtemp()),
            verbose=False,
        )
        driver = AsyncOpenCodeCLIDriver(config)
        print("  - CLI driver created successfully: PASS")
        return True
    except Exception as e:
        print(f"  - CLI driver creation failed: FAIL - {e}")
        return False


def main():
    """Run all security verification tests."""
    print("=" * 70)
    print("SECURITY FIX VERIFICATION FOR core/drivers/async_opencode_driver.py")
    print("=" * 70)
    
    try:
        # Run synchronous tests
        tests_passed = 0
        total_tests = 5
        
        if test_model_injection_protection():
            tests_passed += 1
        
        if test_cli_path_validation():
            tests_passed += 1
        
        if test_prompt_validation():
            tests_passed += 1
        
        if test_model_sanitization():
            tests_passed += 1
        
        # Run async tests
        loop = asyncio.get_event_loop()
        
        if loop.run_until_complete(test_http_driver_creation()):
            tests_passed += 1
        
        # Skipping CLI driver creation test for now as it may fail in environments without opencode CLI
        # total_tests += 1
        # if loop.run_until_complete(test_cli_driver_creation()):
        #     tests_passed += 1
        
        print("\n" + "=" * 70)
        if tests_passed == total_tests:
            print("[SUCCESS] ALL SECURITY VERIFICATIONS PASSED!")
            print("=" * 70)
            print("\nSecurity Issues Fixed:")
            print("1. [FIXED] Command injection via model parameter")
            print("2. [FIXED] Command injection via CLI path")
            print("3. [FIXED] Unsafe prompt handling (null bytes, DoS)")
            print("\nAll 3 security issues have been successfully resolved.")
            sys.exit(0)
        else:
            print(f"[FAILURE] {tests_passed}/{total_tests} test suites passed")
            print("=" * 70)
            sys.exit(1)
    
    except Exception as e:
        print(f"\n[ERROR] VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
