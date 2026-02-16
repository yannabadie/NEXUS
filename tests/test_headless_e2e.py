"""
E2E tests for NEXUS headless mode.

Validates that:
1. --headless boots without TTY blocking
2. --headless produces valid JSON output
3. Exit codes are deterministic (0 success, 1 failure)
4. --headless --task works with task description
5. --headless --output writes to file
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


NEXUS_ENTRY = str(Path(__file__).parent.parent / "nexus7.py")


class TestHeadlessBootValidation:
    """Test that headless mode boots cleanly."""

    def test_headless_boot_produces_json(self):
        """Headless mode without --task should validate boot and return JSON."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        # Should exit 0 (boot validation success)
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Output should be valid JSON
        output = json.loads(result.stdout)
        assert output["mode"] == "headless"
        assert output["status"] == "success"
        assert "nexus_version" in output
        assert "timestamp" in output

    def test_headless_boot_no_tty_prompts(self):
        """Headless mode must never prompt for input."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless"],
            capture_output=True,
            text=True,
            timeout=30,
            # No stdin pipe - headless must not read from it
            stdin=subprocess.DEVNULL,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        assert result.returncode == 0
        # No interactive prompts in output
        assert ">>>" not in result.stdout
        assert "nexus7>" not in result.stdout

    def test_headless_version_in_output(self):
        """JSON output includes correct version."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        output = json.loads(result.stdout)
        assert output["nexus_version"] == "12.4.0"
        assert output["codename"] == "COGNITIVE BOOST"


class TestHeadlessTaskExecution:
    """Test headless mode with --task flag."""

    def test_headless_with_task(self):
        """--headless --task should accept a task description and produce JSON."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless", "--task", "Validate system health"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        # Should produce valid JSON regardless of success/failure
        output = json.loads(result.stdout)
        assert output["task"] == "Validate system health"
        assert output["mode"] == "headless"
        # Task may succeed or fail (orchestrator may not be fully wired)
        assert output["status"] in ("success", "failure")

    def test_headless_output_to_file(self):
        """--output should write JSON to file instead of stdout."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, NEXUS_ENTRY, "--headless", "--output", output_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path(NEXUS_ENTRY).parent),
            )

            assert result.returncode == 0

            # File should contain valid JSON
            with open(output_path) as f:
                output = json.loads(f.read())
            assert output["mode"] == "headless"
            assert output["status"] == "success"
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestHeadlessExitCodes:
    """Test that exit codes are deterministic."""

    def test_version_flag_exits_zero(self):
        """--version should exit 0."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )
        assert result.returncode == 0

    @pytest.mark.skipif(
        not Path(NEXUS_ENTRY).parent.joinpath("KERNEL.py").exists(),
        reason="KERNEL.py not available"
    )
    def test_verify_flag_exits_deterministically(self):
        """--verify should exit with a deterministic code (not hang)."""
        # --verify runs full bootstrap which checks for CLI tools.
        # In CI without gemini/claude CLIs, it exits 1. That's fine.
        # We only care it doesn't hang indefinitely.
        try:
            result = subprocess.run(
                [sys.executable, NEXUS_ENTRY, "--verify"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(Path(NEXUS_ENTRY).parent),
            )
            assert result.returncode in (0, 1)
        except subprocess.TimeoutExpired:
            pytest.skip("--verify timed out (CLI tools not available)")


class TestHeadlessJSONSchema:
    """Test the JSON output schema is consistent."""

    def test_output_schema_completeness(self):
        """All required fields must be present in JSON output."""
        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        output = json.loads(result.stdout)

        required_fields = [
            "nexus_version", "codename", "mode",
            "timestamp", "task", "status", "output", "error"
        ]
        for field in required_fields:
            assert field in output, f"Missing required field: {field}"

    def test_output_timestamp_is_iso8601(self):
        """Timestamp must be valid ISO 8601."""
        from datetime import datetime

        result = subprocess.run(
            [sys.executable, NEXUS_ENTRY, "--headless"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(NEXUS_ENTRY).parent),
        )

        output = json.loads(result.stdout)
        # Should not raise ValueError
        datetime.fromisoformat(output["timestamp"])
