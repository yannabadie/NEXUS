"""
NEXUS V5.1 - Automated End-to-End Tests
Tests avec les CLIs Gemini et Claude réels.
"""
import sys
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Force UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class E2ETestRunner:
    """Automated end-to-end test runner."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
        self.results = []

        # Paths
        self.nexus_interactive = Path(__file__).parent.parent / "nexus_interactive.py"
        self.workspace = Path(__file__).parent.parent / "workspace"

    def log(self, message, status="INFO"):
        """Log avec timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "  [INFO]",
            "PASS": "  [PASS]",
            "FAIL": "  [FAIL]",
            "TEST": "\n[TEST]"
        }.get(status, "  [INFO]")

        print(f"{prefix} {message}")

    def run_command(self, cmd_input: str, timeout: int = 180) -> tuple:
        """
        Execute NEXUS with input and capture output.

        Returns: (stdout, stderr, returncode)
        """
        self.log(f"Running: {cmd_input}", "INFO")

        # Create input file
        input_file = self.workspace / "_test_input.txt"
        input_file.write_text(f"{cmd_input}\n/exit\n", encoding="utf-8")

        proc = None
        try:
            # Run nexus_interactive.py with input
            with open(input_file, 'r', encoding='utf-8') as f:
                proc = subprocess.Popen(
                    [sys.executable, str(self.nexus_interactive)],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )

                stdout, stderr = proc.communicate(timeout=timeout)
                return stdout, stderr, proc.returncode

        except subprocess.TimeoutExpired:
            self.log(f"TIMEOUT after {timeout}s (capturing partial output)", "INFO")
            if proc:
                proc.kill()
                stdout, stderr = proc.communicate()
                return stdout, stderr, -1
            return "", f"Timeout after {timeout}s", 1

        finally:
            # Cleanup
            if input_file.exists():
                try:
                    input_file.unlink()
                except PermissionError:
                    pass  # File still locked, ignore

    def test_conversation_greeting(self):
        """Test 1: Simple greeting should get instant response."""
        self.log("Simple greeting - should NOT trigger orchestration", "TEST")

        stdout, stderr, rc = self.run_command("hello")

        # Check for conversation response
        if "Hello! I'm NEXUS V5.1" in stdout:
            self.log("Got conversation response", "PASS")
            self.passed += 1
            success = True
        else:
            self.log("No conversation response found", "FAIL")
            self.failed += 1
            success = False

        # Check NO orchestration triggered
        if "[NEXUS CORE] Démarrage de l'orchestration" not in stdout:
            self.log("Orchestration NOT triggered (correct)", "PASS")
            self.passed += 1
        else:
            self.log("Orchestration WAS triggered (wrong!)", "FAIL")
            self.failed += 1
            success = False

        self.results.append({
            "test": "Conversation - Greeting",
            "passed": success,
            "output_sample": stdout[:200]
        })

    def test_conversation_capabilities(self):
        """Test 2: Question about NEXUS capabilities."""
        self.log("Question about NEXUS - should get direct response", "TEST")

        stdout, stderr, rc = self.run_command("Quel sont tes compétences?")

        # Check for capabilities response
        if "My capabilities" in stdout or "capacités" in stdout or "compétence" in stdout:
            self.log("Got capabilities response", "PASS")
            self.passed += 1
            success = True
        else:
            self.log("No capabilities response", "FAIL")
            self.failed += 1
            success = False

        # Check NO orchestration
        if "[NEXUS CORE] Démarrage de l'orchestration" not in stdout:
            self.log("Orchestration NOT triggered (correct)", "PASS")
            self.passed += 1
        else:
            self.log("Orchestration WAS triggered (wrong!)", "FAIL")
            self.failed += 1
            success = False

        self.results.append({
            "test": "Conversation - Capabilities",
            "passed": success,
            "output_sample": stdout[:200]
        })

    def test_technical_task(self):
        """Test 3: Technical task should trigger orchestration."""
        self.log("Technical task - SHOULD trigger orchestration", "TEST")
        self.log("NOTE: This test only verifies orchestration starts, not completion", "INFO")

        # Clean workspace
        test_file = self.workspace / "test_automated.txt"
        if test_file.exists():
            test_file.unlink()

        stdout, stderr, rc = self.run_command(
            'créé un fichier test_automated.txt avec le contenu "NEXUS V5.1.3 automated test"',
            timeout=30  # Only wait for orchestration to start
        )

        # Check orchestration started
        if "[NEXUS CORE] Démarrage de l'orchestration" in stdout or "NEXUS CORE" in stdout:
            self.log("Orchestration triggered (correct)", "PASS")
            self.passed += 1
            orch_started = True
        else:
            self.log("Orchestration NOT triggered (wrong!)", "FAIL")
            self.failed += 1
            orch_started = False

        # Check for critical errors (the 12 bugs we fixed)
        errors = []

        if "Expecting value: line 1 column 1" in stdout or "Expecting value: line 1 column 1" in stderr:
            errors.append("BUG #1: Claude responded in text (not JSON)")

        if "État corrompu" in stdout:
            errors.append("BUG #2: Blackboard.json missing")

        if "Input should be 'CONTINUE', 'FINISHED' or 'ERROR_REVIEW_NEEDED'" in stdout:
            errors.append("BUG #3: Invalid status enum value")

        if errors:
            self.log(f"CRITICAL BUGS FOUND: {', '.join(errors)}", "FAIL")
            for error in errors:
                self.log(f"  - {error}", "FAIL")
                self.failed += 1
            success = False
        else:
            self.log("No critical bug errors detected", "PASS")
            self.passed += 1
            success = True

        # Note: We don't check file creation since we timeout before completion
        # File creation would be verified in full manual E2E testing

        self.results.append({
            "test": "Technical Task - Orchestration Start",
            "passed": success and orch_started,
            "errors": errors,
            "output_sample": stdout[:500] if stdout else "No output (timeout)"
        })

    def test_greeting_plus_task(self):
        """Test 4: Greeting + task should be processed as task."""
        self.log("Greeting + task - should trigger orchestration", "TEST")

        # Shorter timeout since we only check if orchestration starts
        stdout, stderr, rc = self.run_command(
            'bonjour, créé un fichier greeting_task.txt avec "test"',
            timeout=30
        )

        # Should trigger orchestration (it's a task!)
        if "[NEXUS CORE] Démarrage de l'orchestration" in stdout or "NEXUS CORE" in stdout:
            self.log("Orchestration triggered (correct for task)", "PASS")
            self.passed += 1
            success = True
        else:
            self.log("Orchestration NOT triggered (wrong! It's a task)", "FAIL")
            self.failed += 1
            success = False

        self.results.append({
            "test": "Greeting + Task Detection",
            "passed": success,
            "output_sample": stdout[:200]
        })

    def summary(self):
        """Print test summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*70)
        print("NEXUS V5.1.3 - AUTOMATED E2E TEST RESULTS")
        print("="*70)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {self.passed} ({pass_rate:.1f}%)")
        print(f"Failed:       {self.failed}")
        print(f"Duration:     {duration:.1f}s")
        print("="*70)

        # Per-test results
        print("\nDetailed Results:")
        for i, result in enumerate(self.results, 1):
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"  {i}. {result['test']}: {status}")
            if not result['passed'] and 'errors' in result:
                for error in result['errors']:
                    print(f"     - {error}")

        print("\n" + "="*70)

        if self.failed == 0:
            print("✓ ALL TESTS PASSED - NEXUS V5.1.3 IS READY!")
        else:
            print(f"✗ {self.failed} TESTS FAILED - See errors above")

        print("="*70 + "\n")

        return self.failed == 0


def main():
    """Run all E2E tests."""
    print("\n" + "="*70)
    print("NEXUS V5.1.3 - AUTOMATED END-TO-END TESTS")
    print("Testing with real Gemini CLI + Claude Code CLI")
    print("="*70)

    runner = E2ETestRunner()

    # Run tests
    runner.test_conversation_greeting()
    runner.test_conversation_capabilities()
    runner.test_greeting_plus_task()
    runner.test_technical_task()  # Most critical test last

    # Summary
    all_passed = runner.summary()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
