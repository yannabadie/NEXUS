"""
Test Claude CLI subprocess with active stdout/stderr reading.

Hypothesis: Claude CLI may be blocking on full output buffers.
Solution: Read stdout/stderr in separate threads while process runs.
"""

import subprocess
import threading
import time
from pathlib import Path


def test_with_thread_reading():
    """Test Claude CLI with active stdout/stderr reading in threads."""

    print("="*70)
    print("Test: Active stdout/stderr reading (like driver does)")
    print("="*70)

    # Prepare context
    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in ONE word only.")

    command = f'claude -p @"{context_file}" --dangerously-skip-permissions'

    print(f"Command: {command}\n")

    start_time = time.time()
    stdout_lines = []
    stderr_lines = []

    def read_stdout(proc):
        """Read stdout line by line."""
        try:
            for line in iter(proc.stdout.readline, ''):
                if line:
                    stdout_lines.append(line)
                    print(f"[STDOUT] {line.strip()}")
        except Exception as e:
            print(f"[ERROR reading stdout] {e}")

    def read_stderr(proc):
        """Read stderr line by line."""
        try:
            for line in iter(proc.stderr.readline, ''):
                if line:
                    stderr_lines.append(line)
                    print(f"[STDERR] {line.strip()}")
        except Exception as e:
            print(f"[ERROR reading stderr] {e}")

    try:
        # Launch with stdin=DEVNULL
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        print(f"[{time.time() - start_time:.1f}s] Process started (PID: {proc.pid})")

        # Start reader threads
        stdout_thread = threading.Thread(target=read_stdout, args=(proc,), daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, args=(proc,), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        print(f"[{time.time() - start_time:.1f}s] Reader threads started")
        print(f"[{time.time() - start_time:.1f}s] Waiting for process to terminate...")
        print("")

        # Poll with timeout
        timeout = 60  # 60 seconds
        elapsed = 0

        while proc.poll() is None and elapsed < timeout:
            time.sleep(1)
            elapsed = time.time() - start_time

            if int(elapsed) % 10 == 0:
                print(f"[{elapsed:.1f}s] Still waiting (stdout: {len(stdout_lines)} lines, stderr: {len(stderr_lines)} lines)...")

        # Check result
        if proc.poll() is None:
            # Timeout
            print(f"\n[{elapsed:.1f}s] TIMEOUT - Process did not terminate")
            print(f"Killing process...")
            proc.kill()
            proc.wait(timeout=5)
            result = "TIMEOUT"
        else:
            # Success
            elapsed = time.time() - start_time
            print(f"\n[{elapsed:.1f}s] SUCCESS - Process terminated!")
            print(f"Exit code: {proc.returncode}")
            result = "SUCCESS"

        # Wait for threads
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

        # Summary
        print(f"\nCapture summary:")
        print(f"  Stdout: {len(stdout_lines)} lines")
        print(f"  Stderr: {len(stderr_lines)} lines")

        if stdout_lines:
            print(f"\nFirst 10 stdout lines:")
            for i, line in enumerate(stdout_lines[:10], 1):
                print(f"  {i}. {line.strip()}")

        return result

    except Exception as e:
        print(f"[ERROR] {e}")
        return "ERROR"
    finally:
        context_file.unlink(missing_ok=True)


def test_without_flags():
    """Test Claude CLI without --dangerously-skip-permissions flag."""

    print("\n" + "="*70)
    print("Test: Without --dangerously-skip-permissions flag")
    print("="*70)

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in ONE word only.")

    # Try without flags
    command = f'claude -p @"{context_file}"'

    print(f"Command: {command}\n")

    start_time = time.time()

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"[{time.time() - start_time:.1f}s] Process started (PID: {proc.pid})")

        # Wait with timeout
        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] SUCCESS - Process terminated!")
            print(f"Exit code: {proc.returncode}")
            print(f"Stdout length: {len(stdout)} chars")
            print(f"Stderr length: {len(stderr)} chars")

            if stdout:
                print(f"\nStdout preview:")
                print(stdout[:500])

            return "SUCCESS"

        except subprocess.TimeoutExpired:
            print(f"[{time.time() - start_time:.1f}s] TIMEOUT")
            proc.kill()
            return "TIMEOUT"

    except Exception as e:
        print(f"[ERROR] {e}")
        return "ERROR"
    finally:
        context_file.unlink(missing_ok=True)


def test_simple_command():
    """Test Claude CLI with simplest possible command."""

    print("\n" + "="*70)
    print("Test: Simplest command (direct prompt via -p)")
    print("="*70)

    command = 'claude -p "What is 2+2? Answer in one word." --dangerously-skip-permissions'

    print(f"Command: {command}\n")

    start_time = time.time()

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"[{time.time() - start_time:.1f}s] Process started (PID: {proc.pid})")

        # Use communicate with timeout
        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] SUCCESS - Process terminated!")
            print(f"Exit code: {proc.returncode}")
            print(f"Stdout: {stdout[:200]}")
            return "SUCCESS"
        except subprocess.TimeoutExpired:
            print(f"[{time.time() - start_time:.1f}s] TIMEOUT")
            proc.kill()
            return "TIMEOUT"

    except Exception as e:
        print(f"[ERROR] {e}")
        return "ERROR"


def main():
    """Run all tests."""

    print("="*70)
    print("Claude CLI Subprocess Investigation - V2")
    print("="*70)
    print("")

    results = {}

    # Test 1: With thread reading (like driver)
    results["1. Thread reading"] = test_with_thread_reading()

    # Test 2: Without skip-permissions flag
    results["2. No --dangerously-skip-permissions"] = test_without_flags()

    # Test 3: Simplest command
    results["3. Direct prompt (no file)"] = test_simple_command()

    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print("")

    for name, result in results.items():
        status = "SUCCESS" if result == "SUCCESS" else "TIMEOUT" if result == "TIMEOUT" else "ERROR"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
