#!/usr/bin/env python3
"""
Test different flag combinations for Claude CLI v2.1.19
"""
import subprocess
import time

def test_variation(name: str, command: list[str], timeout: int = 15) -> bool:
    """Test a specific flag variation"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    print(f"Timeout: {timeout}s")

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(timeout=timeout)
        elapsed = time.time() - start_time

        print(f"[OK] Completed in {elapsed:.2f}s")
        print(f"Exit code: {proc.returncode}")
        if stdout:
            print(f"STDOUT: {stdout[:200]}")
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[FAIL] TIMEOUT after {elapsed:.2f}s")
        proc.kill()
        proc.communicate()
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[FAIL] ERROR after {elapsed:.2f}s: {e}")
        return False


def main():
    print("Claude CLI Flag Variations Test")
    print("Version:", subprocess.check_output(["claude", "--version"], text=True).strip())

    variations = [
        # Original (used in previous tests)
        ("Original order", [
            "claude", "-p", "2+2",
            "--dangerously-skip-permissions",
            "--no-session-persistence"
        ]),

        # Minimal (only -p)
        ("Minimal (-p only)", [
            "claude", "-p", "2+2"
        ]),

        # Only skip permissions
        ("Only skip permissions", [
            "claude", "-p", "2+2",
            "--dangerously-skip-permissions"
        ]),

        # Only no-session
        ("Only no-session", [
            "claude", "-p", "2+2",
            "--no-session-persistence"
        ]),

        # Flags BEFORE -p
        ("Flags before -p", [
            "claude",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            "-p", "2+2"
        ]),

        # With --model
        ("With --model", [
            "claude", "-p", "2+2",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            "--model", "sonnet"
        ]),

        # With explicit allowed-tools
        ("With Read tool only", [
            "claude", "-p", "2+2",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            "--allowed-tools", "Read"
        ]),

        # With --max-turns 1
        ("Max turns 1", [
            "claude", "-p", "2+2",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            "--max-turns", "1"
        ]),
    ]

    results = []
    for name, cmd in variations:
        passed = test_variation(name, cmd, timeout=15)
        results.append((name, passed))
        time.sleep(1)  # Pause entre tests

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{total} tests passed")

    if passed_count > 0:
        print("\n[INFO] Found working flag combination(s)!")
    else:
        print("\n[WARNING] No working combinations found.")


if __name__ == "__main__":
    main()
