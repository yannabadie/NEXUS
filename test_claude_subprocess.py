"""
Test script to reproduce and fix Claude CLI subprocess hang on Windows.

This script tests different subprocess configurations to identify
which one allows Claude CLI to terminate cleanly.
"""

import subprocess
import time
import sys
from pathlib import Path

def test_subprocess_config(config_name: str, **popen_kwargs):
    """
    Test a subprocess configuration with Claude CLI.

    Args:
        config_name: Name of configuration for logging
        **popen_kwargs: Arguments to pass to subprocess.Popen
    """
    print(f"\n{'='*70}")
    print(f"Testing: {config_name}")
    print(f"{'='*70}")

    # Prepare simple context file
    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")

    # Build command
    command = f'claude -p @"{context_file}" --dangerously-skip-permissions'

    print(f"Command: {command}")
    print(f"Popen kwargs: {popen_kwargs}")
    print("")

    start_time = time.time()

    try:
        # Launch process
        proc = subprocess.Popen(
            command,
            shell=True,
            **popen_kwargs
        )

        print(f"[{time.time() - start_time:.1f}s] Process started (PID: {proc.pid})")

        # Wait for process with timeout
        timeout = 30  # 30 seconds max
        elapsed = 0

        while proc.poll() is None and elapsed < timeout:
            time.sleep(0.5)
            elapsed = time.time() - start_time

            if int(elapsed) % 5 == 0 and int((elapsed - 0.5)) % 5 != 0:
                print(f"[{elapsed:.1f}s] Process still running...")

        if proc.poll() is None:
            # Timeout - kill process
            print(f"[{elapsed:.1f}s] ❌ TIMEOUT - Process did not terminate")
            print(f"  → Killing process...")
            proc.kill()
            proc.wait(timeout=5)
            result = "TIMEOUT"
        else:
            # Process terminated
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] ✅ SUCCESS - Process terminated cleanly")
            print(f"  → Exit code: {proc.returncode}")
            result = "SUCCESS"

        # Get outputs if available
        if hasattr(proc, 'stdout') and proc.stdout:
            try:
                stdout = proc.stdout.read()
                if stdout:
                    print(f"  → Stdout length: {len(stdout)} chars")
            except:
                pass

        return result

    except Exception as e:
        print(f"[ERROR] {e}")
        return "ERROR"
    finally:
        # Cleanup
        context_file.unlink(missing_ok=True)


def main():
    """Run all test configurations."""

    print("="*70)
    print("Claude CLI Subprocess Termination Test")
    print("="*70)
    print("\nThis script tests different subprocess configurations to fix")
    print("the Windows hang issue where Claude CLI doesn't terminate cleanly.")
    print("")

    results = {}

    # Test 1: Current configuration (baseline)
    results["1. Current (no stdin)"] = test_subprocess_config(
        "Current Configuration (baseline)",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    # Test 2: stdin=DEVNULL
    results["2. stdin=DEVNULL"] = test_subprocess_config(
        "Fix 1: stdin=DEVNULL",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    # Test 3: stdin=PIPE (closed immediately)
    print(f"\n{'='*70}")
    print(f"Testing: Fix 2: stdin=PIPE + close()")
    print(f"{'='*70}")

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")
    command = f'claude -p @"{context_file}" --dangerously-skip-permissions'

    try:
        start_time = time.time()
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Close stdin immediately
        proc.stdin.close()
        print(f"[{time.time() - start_time:.1f}s] Process started, stdin closed")

        timeout = 30
        elapsed = 0

        while proc.poll() is None and elapsed < timeout:
            time.sleep(0.5)
            elapsed = time.time() - start_time

            if int(elapsed) % 5 == 0 and int((elapsed - 0.5)) % 5 != 0:
                print(f"[{elapsed:.1f}s] Process still running...")

        if proc.poll() is None:
            print(f"[{elapsed:.1f}s] ❌ TIMEOUT")
            proc.kill()
            proc.wait(timeout=5)
            results["3. stdin=PIPE+close"] = "TIMEOUT"
        else:
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] ✅ SUCCESS")
            results["3. stdin=PIPE+close"] = "SUCCESS"
    except Exception as e:
        print(f"[ERROR] {e}")
        results["3. stdin=PIPE+close"] = "ERROR"
    finally:
        context_file.unlink(missing_ok=True)

    # Test 4: creationflags (Windows-specific)
    if sys.platform == 'win32':
        try:
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008

            results["4. CREATE_NEW_PROCESS_GROUP"] = test_subprocess_config(
                "Fix 3: CREATE_NEW_PROCESS_GROUP (Windows)",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=CREATE_NEW_PROCESS_GROUP
            )
        except Exception as e:
            print(f"[ERROR] Windows-specific test failed: {e}")
            results["4. CREATE_NEW_PROCESS_GROUP"] = "ERROR"

    # Summary
    print(f"\n{'='*70}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*70}")
    print("")

    for test_name, result in results.items():
        emoji = "✅" if result == "SUCCESS" else "❌" if result == "TIMEOUT" else "⚠️"
        print(f"{emoji} {test_name}: {result}")

    print("")

    # Recommendation
    successes = [name for name, result in results.items() if result == "SUCCESS"]
    if successes:
        print(f"{'='*70}")
        print("RECOMMENDATION")
        print(f"{'='*70}")
        print("")
        print(f"Use configuration: {successes[0]}")
        print("")
    else:
        print("⚠️  No configuration succeeded - deeper investigation needed")


if __name__ == "__main__":
    main()
