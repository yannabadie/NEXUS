"""
Test Claude CLI with --no-session-persistence flag.

This test validates if --no-session-persistence fixes the subprocess hang issue
where Claude CLI doesn't terminate after sending response in collaborative mode.
"""

import subprocess
import time
import sys

def test_no_session_persistence():
    """Test Claude CLI with --no-session-persistence flag."""

    test_prompt = "What is 2+2? Answer in one word only."

    # Write prompt to file (same as driver does)
    from pathlib import Path
    test_file = Path("_IO_BUFFER/test_prompt.md")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(test_prompt, encoding="utf-8")

    # Build command with --no-session-persistence (using @file syntax)
    cmd = f'claude -p @"{test_file}" --dangerously-skip-permissions --no-session-persistence'

    print(f"Testing: {cmd}")
    print(f"Expected: Process should terminate after response\n")

    start_time = time.time()

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait max 30 seconds
        stdout, stderr = proc.communicate(timeout=30)

        elapsed = time.time() - start_time

        print(f"[{elapsed:.1f}s] SUCCESS - Process terminated cleanly")
        print(f"Exit code: {proc.returncode}")
        print(f"\nStdout:\n{stdout[:200]}")
        if stderr:
            print(f"\nStderr:\n{stderr[:200]}")

        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] TIMEOUT - Process did not terminate")
        proc.kill()
        proc.wait()
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    result = test_no_session_persistence()
    sys.exit(0 if result else 1)
