"""
Test Claude CLI with --no-session-persistence to disable hooks and session state.

Hypothesis: Session hooks or persistence may prevent clean exit.
"""

import subprocess
import time
from pathlib import Path


def test_no_session_persistence():
    """Test with --no-session-persistence flag."""

    print("="*70)
    print("Test: --no-session-persistence + -p")
    print("="*70)

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")

    command = (
        f'claude -p @"{context_file}" '
        f'--dangerously-skip-permissions '
        f'--no-session-persistence'
    )

    print(f"Command: {command}\n")

    start_time = time.time()

    try:
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

        # Use communicate with timeout
        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time

            print(f"[{elapsed:.1f}s] SUCCESS - Process terminated!")
            print(f"Exit code: {proc.returncode}")
            print(f"\nStdout ({len(stdout)} chars):")
            print(stdout)

            if stderr:
                print(f"\nStderr ({len(stderr)} chars):")
                print(stderr[:500])

            return "SUCCESS"

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] TIMEOUT")

            # Try to get partial output
            proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=5)
                print(f"\nPartial stdout:")
                print(stdout[:500])
            except:
                pass

            return "TIMEOUT"

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return "ERROR"
    finally:
        context_file.unlink(missing_ok=True)


def test_output_format_json():
    """Test with --output-format json."""

    print("\n" + "="*70)
    print("Test: --output-format json")
    print("="*70)

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")

    command = (
        f'claude -p @"{context_file}" '
        f'--dangerously-skip-permissions '
        f'--no-session-persistence '
        f'--output-format json'
    )

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

        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time

            print(f"[{elapsed:.1f}s] SUCCESS!")
            print(f"Exit code: {proc.returncode}")
            print(f"\nJSON output:")
            print(stdout)

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


def test_fallback_model():
    """Test with --fallback-model to ensure single-shot execution."""

    print("\n" + "="*70)
    print("Test: --fallback-model (forces single-shot mode)")
    print("="*70)

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")

    command = (
        f'claude -p @"{context_file}" '
        f'--dangerously-skip-permissions '
        f'--no-session-persistence '
        f'--fallback-model sonnet'
    )

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

        print(f"[{time.time() - start_time:.1f}s] Process started")

        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time

            print(f"[{elapsed:.1f}s] SUCCESS!")
            print(f"Exit code: {proc.returncode}")
            print(f"\nOutput:")
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


def test_minimal_flags():
    """Test with absolutely minimal flags."""

    print("\n" + "="*70)
    print("Test: Minimal flags (-p only)")
    print("="*70)

    io_buffer = Path("_IO_BUFFER")
    io_buffer.mkdir(exist_ok=True)
    context_file = io_buffer / "test_context.md"
    context_file.write_text("What is 2+2? Answer in one sentence.")

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

        print(f"[{time.time() - start_time:.1f}s] Process started")

        try:
            stdout, stderr = proc.communicate(timeout=30)
            elapsed = time.time() - start_time

            print(f"[{elapsed:.1f}s] SUCCESS!")
            print(f"Exit code: {proc.returncode}")
            print(f"\nOutput ({len(stdout)} chars):")
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


def main():
    """Run all tests."""

    print("="*70)
    print("Claude CLI Subprocess Investigation - V3")
    print("Testing session persistence and output format flags")
    print("="*70)
    print("")

    results = {}

    results["1. --no-session-persistence"] = test_no_session_persistence()
    results["2. --output-format json"] = test_output_format_json()
    results["3. --fallback-model"] = test_fallback_model()
    results["4. Minimal (-p only)"] = test_minimal_flags()

    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print("")

    for name, result in results.items():
        print(f"  {name}: {result}")

    print("")

    successes = [name for name, result in results.items() if result == "SUCCESS"]
    if successes:
        print(f"SUCCESS COUNT: {len(successes)}/{len(results)}")
        print(f"First successful configuration: {successes[0]}")
    else:
        print("NO CONFIGURATIONS SUCCEEDED")


if __name__ == "__main__":
    main()
