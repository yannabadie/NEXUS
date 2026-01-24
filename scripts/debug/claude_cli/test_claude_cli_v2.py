#!/usr/bin/env python3
"""
Test Claude CLI v2.1.19 subprocess behavior
Tests if -p flag still hangs in subprocess mode
"""
import subprocess
import time
import sys
from pathlib import Path

def test_cli_simple_prompt():
    """Test 1: Simple prompt with -p flag"""
    print("\n" + "="*60)
    print("TEST 1: Simple prompt with -p flag")
    print("="*60)

    command = [
        "claude",
        "-p",
        "What is 2+2? Answer with just the number.",
        "--dangerously-skip-permissions",
        "--no-session-persistence"
    ]

    print(f"Command: {' '.join(command)}")
    print("Timeout: 30 seconds")
    print("Starting...")

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait with timeout
        stdout, stderr = proc.communicate(timeout=30)
        elapsed = time.time() - start_time

        print(f"\n[OK] COMPLETED in {elapsed:.2f}s")
        print(f"Exit code: {proc.returncode}")
        print(f"STDOUT length: {len(stdout)} chars")
        print(f"STDERR length: {len(stderr)} chars")

        if stdout:
            print(f"\nSTDOUT:\n{stdout[:500]}")
        if stderr:
            print(f"\nSTDERR:\n{stderr[:500]}")

        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] TIMEOUT after {elapsed:.2f}s")
        proc.kill()
        stdout, stderr = proc.communicate()
        print(f"Process had to be killed")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] ERROR after {elapsed:.2f}s: {e}")
        return False


def test_cli_file_input():
    """Test 2: File-based input with @file syntax"""
    print("\n" + "="*60)
    print("TEST 2: File-based input with @file")
    print("="*60)

    # Create temp file
    test_file = Path("_IO_BUFFER/cli_test_prompt.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("List 3 programming languages. Be concise.", encoding="utf-8")

    command = [
        "claude",
        "-p",
        f"@{test_file}",
        "--dangerously-skip-permissions",
        "--no-session-persistence"
    ]

    print(f"Command: {' '.join(command)}")
    print("Timeout: 30 seconds")
    print("Starting...")

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=30)
        elapsed = time.time() - start_time

        print(f"\n[OK] COMPLETED in {elapsed:.2f}s")
        print(f"Exit code: {proc.returncode}")
        print(f"STDOUT length: {len(stdout)} chars")

        if stdout:
            print(f"\nSTDOUT:\n{stdout[:500]}")

        # Cleanup
        test_file.unlink(missing_ok=True)
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] TIMEOUT after {elapsed:.2f}s")
        proc.kill()
        test_file.unlink(missing_ok=True)
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] ERROR after {elapsed:.2f}s: {e}")
        test_file.unlink(missing_ok=True)
        return False


def test_cli_allowed_tools():
    """Test 3: With --allowed-tools restriction"""
    print("\n" + "="*60)
    print("TEST 3: With --allowed-tools restriction")
    print("="*60)

    command = [
        "claude",
        "-p",
        "Echo hello using bash",
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        "--allowed-tools",
        "Bash"
    ]

    print(f"Command: {' '.join(command)}")
    print("Timeout: 30 seconds")
    print("Starting...")

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=30)
        elapsed = time.time() - start_time

        print(f"\n[OK] COMPLETED in {elapsed:.2f}s")
        print(f"Exit code: {proc.returncode}")

        if stdout:
            print(f"\nSTDOUT:\n{stdout[:500]}")

        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] TIMEOUT after {elapsed:.2f}s")
        proc.kill()
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] ERROR after {elapsed:.2f}s: {e}")
        return False


def main():
    print("="*60)
    print("Claude CLI v2.1.19 Subprocess Hang Test Suite")
    print("="*60)

    # Get version
    try:
        version = subprocess.check_output(["claude", "--version"], text=True).strip()
        print(f"Claude CLI version: {version}")
    except Exception as e:
        print(f"Failed to get version: {e}")
        return

    results = []

    # Run tests
    results.append(("Simple prompt", test_cli_simple_prompt()))
    results.append(("File input", test_cli_file_input()))
    results.append(("Allowed tools", test_cli_allowed_tools()))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Subprocess hang is FIXED in v2.1.19")
        sys.exit(0)
    else:
        print("\n[WARNING] Some tests failed. Subprocess hang still present.")
        sys.exit(1)


if __name__ == "__main__":
    main()
