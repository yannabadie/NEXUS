"""
NEXUS V5.0 - Comprehensive Test Suite
Scenarios de test exigeants pour validation en environnement reel.
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import io

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path (now that we're in tests/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.orchestration_logged import LoggedOrchestrator


class TestScenario:
    """Définition d'un scénario de test."""

    def __init__(self, name: str, objective: str, mode: str = "Normal",
                 expected_turns_min: int = 1, expected_turns_max: int = 100,
                 expected_tools: List[str] = None, critical: bool = False,
                 description: str = ""):
        self.name = name
        self.objective = objective
        self.mode = mode
        self.expected_turns_min = expected_turns_min
        self.expected_turns_max = expected_turns_max
        self.expected_tools = expected_tools or []
        self.critical = critical
        self.description = description
        self.result = None
        self.session_id = None
        self.start_time = None
        self.end_time = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Export scenario as dict."""
        return {
            "name": self.name,
            "objective": self.objective,
            "mode": self.mode,
            "expected_turns_min": self.expected_turns_min,
            "expected_turns_max": self.expected_turns_max,
            "expected_tools": self.expected_tools,
            "critical": self.critical,
            "description": self.description,
            "result": self.result,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": (
                (datetime.fromisoformat(self.end_time) - datetime.fromisoformat(self.start_time)).total_seconds()
                if self.start_time and self.end_time else None
            ),
            "error": self.error
        }


# SCÉNARIOS DE TEST CRITIQUES
CRITICAL_SCENARIOS = [
    TestScenario(
        name="CFL_BASIC_WRITE_READ",
        objective="Create a file named test_cfl.txt with content 'NEXUS V5.0 CFL Test'. Then read the file and confirm the content is exactly 'NEXUS V5.0 CFL Test'. Provide detailed post_action_review after each tool use.",
        mode="Normal",
        expected_turns_min=3,
        expected_turns_max=10,
        expected_tools=["write", "read"],
        critical=True,
        description="Valide le cycle CFL complet: Tool → Execution → Validation"
    ),

    TestScenario(
        name="DUAL_SCHEMA_ENFORCEMENT",
        objective="Execute 3 bash commands in sequence: 'echo Step1', 'echo Step2', 'echo Step3'. After EACH command, you MUST provide post_action_review with validation_status.",
        mode="Normal",
        expected_turns_min=6,
        expected_turns_max=15,
        expected_tools=["bash"],
        critical=True,
        description="Force Dual Schema: HeavyMessage obligatoire après chaque TOOL_USE"
    ),

    TestScenario(
        name="TOOL_EXECUTOR_ALL_TOOLS",
        objective="Test all available tools: 1) Use bash to run 'echo test', 2) Write file tools_test.txt, 3) Read tools_test.txt, 4) Edit tools_test.txt to replace 'test' with 'validated', 5) List files in current directory, 6) Run git status. Validate each step.",
        mode="Normal",
        expected_turns_min=12,
        expected_turns_max=30,
        expected_tools=["bash", "write", "read", "edit", "list_dir", "git"],
        critical=True,
        description="Valide que tous les outils fonctionnent correctement"
    ),

    TestScenario(
        name="STRATEGIC_PLAN_TRACKING",
        objective="Create a comprehensive plan to: 1) Create 3 text files (alpha.txt, beta.txt, gamma.txt) with different content, 2) Read all 3 files, 3) Create a summary report. Track progress in strategic_plan with status updates (PENDING → IN_PROGRESS → COMPLETED).",
        mode="Normal",
        expected_turns_min=10,
        expected_turns_max=25,
        expected_tools=["write", "read"],
        critical=True,
        description="Valide planification stratégique et suivi de progression"
    ),
]


# SCÉNARIOS DE TEST AVANCÉS
ADVANCED_SCENARIOS = [
    TestScenario(
        name="ERROR_RECOVERY",
        objective="Execute bash command 'invalidcommand12345' which will fail. Analyze the error in post_action_review, then execute a valid command 'echo Recovery successful' to demonstrate error recovery.",
        mode="Normal",
        expected_turns_min=4,
        expected_turns_max=15,
        expected_tools=["bash"],
        critical=False,
        description="Valide gestion d'erreur et récupération"
    ),

    TestScenario(
        name="MULTI_STEP_ANALYSIS",
        objective="Analyze all Python files in the 'core/' directory: 1) List all .py files, 2) Read each file, 3) Identify files without module docstrings, 4) Create a report file 'docstring_audit.md' with findings.",
        mode="Normal",
        expected_turns_min=15,
        expected_turns_max=50,
        expected_tools=["list_dir", "read", "write"],
        critical=False,
        description="Test capacité d'analyse multi-étapes sur vrai code"
    ),

    TestScenario(
        name="AGENT_COLLABORATION",
        objective="This task requires strategic thinking AND execution. Gemini: Create a strategic plan for analyzing test results. Claude: Execute the plan by reading log files and creating a summary report.",
        mode="Normal",
        expected_turns_min=8,
        expected_turns_max=20,
        expected_tools=["read", "write", "list_dir"],
        critical=False,
        description="Valide collaboration Gemini (stratégie) ↔ Claude (exécution)"
    ),

    TestScenario(
        name="GIT_OPERATIONS",
        objective="Perform Git operations: 1) Run git status, 2) Create file git_test.txt, 3) Run git add git_test.txt, 4) Run git status again to confirm staging. Report all outputs.",
        mode="Normal",
        expected_turns_min=8,
        expected_turns_max=20,
        expected_tools=["git", "write"],
        critical=False,
        description="Valide opérations Git complètes"
    ),

    TestScenario(
        name="LONG_SESSION_STABILITY",
        objective="Execute a long sequence of operations: Create 10 files named file_1.txt through file_10.txt, each with unique content. Then read each file back. Then create a summary file 'sequence_summary.txt' listing all files and their content. Maintain strategic plan throughout.",
        mode="Normal",
        expected_turns_min=30,
        expected_turns_max=60,
        expected_tools=["write", "read"],
        critical=False,
        description="Test stabilité sur session longue (30+ tours)"
    ),
]


# SCÉNARIOS DE STRESS TEST
STRESS_SCENARIOS = [
    TestScenario(
        name="STRESS_RAPID_TOOL_SWITCHING",
        objective="Rapidly switch between tools: bash → write → read → edit → bash → git → list_dir, then repeat. Ensure CFL validation for each. Create 'stress_test_report.txt' with results.",
        mode="Normal",
        expected_turns_min=20,
        expected_turns_max=40,
        expected_tools=["bash", "write", "read", "edit", "git", "list_dir"],
        critical=False,
        description="Stress test: changement rapide d'outils"
    ),

    TestScenario(
        name="STRESS_LARGE_FILE_OPERATIONS",
        objective="Create a large file 'large_data.txt' with 1000 lines of data (use bash echo in loop or write tool). Then read it back. Then edit specific lines. Report performance.",
        mode="Normal",
        expected_turns_min=10,
        expected_turns_max=30,
        expected_tools=["write", "bash", "read", "edit"],
        critical=False,
        description="Stress test: opérations sur fichiers volumineux"
    ),

    TestScenario(
        name="STRESS_PLAN_COMPLEXITY",
        objective="Create a highly complex strategic plan with 20 detailed steps for building a complete Python project structure (folders, files, tests, docs). Execute first 5 steps only. Track plan health and drift.",
        mode="Normal",
        expected_turns_min=15,
        expected_turns_max=40,
        expected_tools=["write", "bash", "list_dir"],
        critical=False,
        description="Stress test: plans complexes avec 20+ étapes"
    ),
]


class TestRunner:
    """Exécute les scénarios de test et génère des rapports."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.results = []
        self.start_time = None
        self.end_time = None

    def run_scenario(self, scenario: TestScenario) -> bool:
        """Execute un scénario de test."""
        print(f"\n{'='*80}")
        print(f"RUNNING TEST: {scenario.name}")
        print(f"{'='*80}")
        print(f"Description: {scenario.description}")
        print(f"Objective: {scenario.objective}")
        print(f"Critical: {'YES' if scenario.critical else 'NO'}")
        print(f"{'='*80}\n")

        # Workspace dédié pour ce test
        test_workspace = self.workspace_root / f"test_{scenario.name.lower()}"
        test_workspace.mkdir(exist_ok=True)

        scenario.start_time = datetime.now().isoformat()

        try:
            # Load config
            config = Config()

            # Create orchestrator
            orchestrator = LoggedOrchestrator(
                test_workspace,
                config,
                scenario.objective,
                scenario.mode
            )

            scenario.session_id = orchestrator.session_id

            # Run
            orchestrator.run()

            scenario.end_time = datetime.now().isoformat()
            scenario.result = "SUCCESS"

            print(f"\n✅ TEST PASSED: {scenario.name}")
            return True

        except KeyboardInterrupt:
            print(f"\n⚠️  TEST INTERRUPTED: {scenario.name}")
            scenario.end_time = datetime.now().isoformat()
            scenario.result = "INTERRUPTED"
            scenario.error = "User interrupted"
            return False

        except Exception as e:
            print(f"\n❌ TEST FAILED: {scenario.name}")
            print(f"Error: {str(e)}")

            scenario.end_time = datetime.now().isoformat()
            scenario.result = "FAILED"
            scenario.error = str(e)
            return False

    def run_suite(self, scenarios: List[TestScenario], suite_name: str):
        """Execute une suite de tests."""
        print(f"\n{'#'*80}")
        print(f"# TEST SUITE: {suite_name}")
        print(f"# Total scenarios: {len(scenarios)}")
        print(f"# Critical: {sum(1 for s in scenarios if s.critical)}")
        print(f"{'#'*80}\n")

        self.start_time = datetime.now().isoformat()

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}] Starting scenario: {scenario.name}")

            success = self.run_scenario(scenario)
            self.results.append(scenario)

            if not success and scenario.critical:
                print(f"\n⛔ CRITICAL TEST FAILED: {scenario.name}")
                print("Stopping suite execution.")
                break

            # Small pause between tests
            if i < len(scenarios):
                print("\nWaiting 5 seconds before next test...")
                time.sleep(5)

        self.end_time = datetime.now().isoformat()

        # Generate report
        self.generate_report(suite_name)

    def generate_report(self, suite_name: str):
        """Génère un rapport de test complet."""
        report_path = self.workspace_root / f"TEST_REPORT_{suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        total = len(self.results)
        passed = sum(1 for r in self.results if r.result == "SUCCESS")
        failed = sum(1 for r in self.results if r.result == "FAILED")
        interrupted = sum(1 for r in self.results if r.result == "INTERRUPTED")

        report = [
            f"# NEXUS V5.0 - TEST REPORT: {suite_name}",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Suite:** {suite_name}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Tests:** {total}",
            f"- **Passed:** {passed} ({100*passed//total if total else 0}%)",
            f"- **Failed:** {failed}",
            f"- **Interrupted:** {interrupted}",
            "",
            f"**Overall Result:** {'✅ PASS' if failed == 0 else '❌ FAIL'}",
            "",
            "## Test Results",
            ""
        ]

        for scenario in self.results:
            status_emoji = {
                "SUCCESS": "✅",
                "FAILED": "❌",
                "INTERRUPTED": "⚠️"
            }.get(scenario.result, "❓")

            report.append(f"### {status_emoji} {scenario.name}")
            report.append("")
            report.append(f"**Status:** {scenario.result}")
            report.append(f"**Critical:** {'Yes' if scenario.critical else 'No'}")
            report.append(f"**Description:** {scenario.description}")
            report.append(f"**Objective:** {scenario.objective}")

            if scenario.session_id:
                report.append(f"**Session ID:** {scenario.session_id}")

            if scenario.start_time and scenario.end_time:
                duration = (
                    datetime.fromisoformat(scenario.end_time) -
                    datetime.fromisoformat(scenario.start_time)
                ).total_seconds()
                report.append(f"**Duration:** {duration:.2f} seconds")

            if scenario.error:
                report.append(f"**Error:** {scenario.error}")

            # Link to logs
            if scenario.session_id:
                test_workspace = self.workspace_root / f"test_{scenario.name.lower()}"
                logs_dir = test_workspace / "logs"
                if logs_dir.exists():
                    report.append("")
                    report.append("**Log Files:**")
                    report.append(f"- Main: `{logs_dir / f'nexus_session_{scenario.session_id}.log'}`")
                    report.append(f"- Events: `{logs_dir / f'events_{scenario.session_id}.jsonl'}`")
                    report.append(f"- CFL: `{logs_dir / f'cfl_{scenario.session_id}.jsonl'}`")
                    report.append(f"- Errors: `{logs_dir / f'errors_{scenario.session_id}.log'}`")
                    report.append(f"- Trace: `{logs_dir / f'trace_{scenario.session_id}.log'}`")

            report.append("")
            report.append("---")
            report.append("")

        # Detailed Analysis
        report.extend([
            "## Detailed Analysis",
            "",
            "### Critical Tests",
            ""
        ])

        critical_tests = [r for r in self.results if r.critical]
        if critical_tests:
            for test in critical_tests:
                status = "✅ PASSED" if test.result == "SUCCESS" else "❌ FAILED"
                report.append(f"- {test.name}: {status}")
        else:
            report.append("No critical tests in this suite.")

        report.extend([
            "",
            "### Performance Metrics",
            ""
        ])

        for test in self.results:
            if test.start_time and test.end_time:
                duration = (
                    datetime.fromisoformat(test.end_time) -
                    datetime.fromisoformat(test.start_time)
                ).total_seconds()
                report.append(f"- {test.name}: {duration:.2f}s")

        # Save report
        report_content = "\n".join(report)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # Also save JSON
        json_path = report_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "suite_name": suite_name,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total": total,
                "passed": passed,
                "failed": failed,
                "interrupted": interrupted,
                "results": [r.to_dict() for r in self.results]
            }, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*80}")
        print(f"REPORT GENERATED")
        print(f"{'='*80}")
        print(f"Markdown: {report_path}")
        print(f"JSON: {json_path}")
        print(f"{'='*80}\n")


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description="NEXUS V5.0 Test Suite")
    parser.add_argument(
        "--suite",
        choices=["critical", "advanced", "stress", "all"],
        default="critical",
        help="Test suite to run"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("test_workspaces"),
        help="Root directory for test workspaces"
    )

    args = parser.parse_args()

    # Create workspace
    args.workspace.mkdir(exist_ok=True)

    # Select scenarios
    if args.suite == "critical":
        scenarios = CRITICAL_SCENARIOS
        suite_name = "CRITICAL"
    elif args.suite == "advanced":
        scenarios = ADVANCED_SCENARIOS
        suite_name = "ADVANCED"
    elif args.suite == "stress":
        scenarios = STRESS_SCENARIOS
        suite_name = "STRESS"
    else:  # all
        scenarios = CRITICAL_SCENARIOS + ADVANCED_SCENARIOS + STRESS_SCENARIOS
        suite_name = "FULL"

    # Run tests
    runner = TestRunner(args.workspace)
    runner.run_suite(scenarios, suite_name)


if __name__ == "__main__":
    main()
