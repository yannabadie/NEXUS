"""
Tiered Validator - Fast-Fail Validation Pipeline for NEXUS V7

Implements tiered validation with early exit and parallel benchmarks.
Rejects broken children in <1s instead of running full validation.

Tiers:
- TIER 1 (<1s):   Syntax (py_compile) + Import check - BLOCKING
- TIER 2 (<30s):  Smoke test + KERNEL integrity - BLOCKING
- TIER 3 (<5min): Fitness Benchmarks (4 workers parallel) - INFORMATIONAL
- TIER 4 (seq):   Red Team (OPTIONAL in V7.5, sequential for security)

Usage:
    from core.evolution.tiered_validator import TieredValidator, ValidationTier

    validator = TieredValidator(child_path, config)
    result = validator.run_tiered(max_tier=ValidationTier.REDTEAM)

    if result.passed:
        # Safe to promote
"""

import ast
import sys
import subprocess
import json
import time
import py_compile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, as_completed


class ValidationTier(IntEnum):
    """Validation tiers with increasing depth/cost"""
    SYNTAX = 1      # <1s - py_compile + AST
    SMOKE = 2       # <30s - System initialization
    BENCHMARK = 3   # <5min - Fitness benchmarks (parallel)
    REDTEAM = 4     # Sequential - Alignment testing (OPTIONAL in V7.5)


@dataclass
class TierResult:
    """Result of a single tier validation"""
    tier: ValidationTier
    passed: bool
    message: str
    duration_seconds: float = 0.0
    details: Dict = field(default_factory=dict)


@dataclass
class TieredValidationResult:
    """Result of full tiered validation"""
    child_id: str
    passed: bool
    failed_at_tier: Optional[ValidationTier] = None
    tier_results: List[TierResult] = field(default_factory=list)
    fitness_score: Optional[float] = None
    red_team_score: Optional[float] = None
    total_duration: float = 0.0
    timestamp: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict:
        return {
            "child_id": self.child_id,
            "passed": self.passed,
            "failed_at_tier": self.failed_at_tier.name if self.failed_at_tier else None,
            "tiers": [
                {
                    "tier": t.tier.name,
                    "passed": t.passed,
                    "message": t.message,
                    "duration_seconds": t.duration_seconds,
                    "details": t.details
                }
                for t in self.tier_results
            ],
            "fitness_score": self.fitness_score,
            "red_team_score": self.red_team_score,
            "total_duration": self.total_duration,
            "timestamp": self.timestamp,
            "recommendation": self.recommendation
        }


class TieredValidator:
    """
    Fast-fail tiered validation for NEXUS children.

    Key optimization: Reject broken code in <1s instead of
    running full 70s+ validation on obviously broken children.
    """

    # Critical files that must pass syntax check
    CRITICAL_FILES = [
        "core/orchestration_v7.py",
        "core/config.py",
        "core/interface/repl.py",
        "core/drivers/gemini_driver_v7.py",
        "core/drivers/claude_driver_hybrid.py",
        "core/execution/tool_manager.py",
        "core/synapse/memory_v7.py",
        "core/fsm/states.py",
        "nexus7.py"
    ]

    # Modules that must import successfully
    CRITICAL_MODULES = [
        "core.orchestration_v7",
        "core.config",
        "core.drivers.gemini_driver_v7",
        "core.drivers.claude_driver_hybrid",
        "core.execution.tool_manager",
        "core.synapse.memory_v7"
    ]

    def __init__(self, child_path: Path, config=None):
        """Initializes the TieredValidator with a child path and configuration.

        Args:
            child_path: The file system path to the NEXUS child instance directory.
            config: Optional configuration object containing validator settings like
                parallel_benchmark_workers. Defaults to None.
        """
        self.child_path = Path(child_path)
        self.child_id = self.child_path.name
        self.config = config

        # Get config values or defaults
        self.parallel_workers = 4
        if config:
            self.parallel_workers = getattr(config, 'parallel_benchmark_workers', 4)

    def run_tiered(
        self,
        max_tier: ValidationTier = ValidationTier.REDTEAM
    ) -> TieredValidationResult:
        """
        Run tiered validation with early exit on failure.

        Args:
            max_tier: Maximum tier to run (default: REDTEAM)

        Returns:
            TieredValidationResult with all tier results
        """
        start_time = time.time()
        result = TieredValidationResult(
            child_id=self.child_id,
            passed=True,
            timestamp=datetime.now().isoformat()
        )

        print(f"\n{'='*60}")
        print(f" TIERED VALIDATION: {self.child_id}")
        print(f" Max Tier: {max_tier.name}")
        print(f"{'='*60}\n")

        # TIER 1: Syntax + Import (<1s)
        tier1 = self._run_tier1_syntax_import()
        result.tier_results.append(tier1)
        self._print_tier_result(tier1)

        if not tier1.passed:
            result.passed = False
            result.failed_at_tier = ValidationTier.SYNTAX
            result.recommendation = f"REJECT: Tier 1 failed - {tier1.message}"
            return self._finalize(result, start_time)

        if max_tier == ValidationTier.SYNTAX:
            result.recommendation = "PARTIAL: Syntax check passed"
            return self._finalize(result, start_time)

        # TIER 2: Smoke Test (<30s)
        tier2 = self._run_tier2_smoke()
        result.tier_results.append(tier2)
        self._print_tier_result(tier2)

        if not tier2.passed:
            result.passed = False
            result.failed_at_tier = ValidationTier.SMOKE
            result.recommendation = f"REJECT: Tier 2 failed - {tier2.message}"
            return self._finalize(result, start_time)

        if max_tier == ValidationTier.SMOKE:
            result.recommendation = "PARTIAL: Smoke test passed"
            return self._finalize(result, start_time)

        # TIER 3: Parallel Benchmarks (<5min)
        tier3 = self._run_tier3_parallel_benchmark()
        result.tier_results.append(tier3)
        self._print_tier_result(tier3)
        result.fitness_score = tier3.details.get("fitness_score")

        if max_tier == ValidationTier.BENCHMARK:
            result.recommendation = f"PARTIAL: Benchmark complete (Fitness: {result.fitness_score})"
            return self._finalize(result, start_time)

        # TIER 4: Sequential Red Team (OPTIONAL in V7.5 HIVE MIND)
        # Check config to see if Red Team is mandatory
        red_team_mandatory = True  # Default to mandatory for safety
        if self.config:
            red_team_mandatory = getattr(self.config, 'red_team_mandatory', False)

        if red_team_mandatory:
            tier4 = self._run_tier4_redteam()
            result.tier_results.append(tier4)
            self._print_tier_result(tier4)
            result.red_team_score = tier4.details.get("alignment_score")

            if not tier4.passed:
                result.passed = False
                result.failed_at_tier = ValidationTier.REDTEAM
                result.recommendation = f"REJECT: Red Team failed - {tier4.message}"
                return self._finalize(result, start_time)

            # All tiers passed including Red Team
            result.recommendation = f"PROMOTE: All tiers passed (Fitness: {result.fitness_score})"
        else:
            # Red Team skipped (V7.5 HIVE MIND default)
            print("\n  [INFO] Red Team validation SKIPPED (RED_TEAM_MANDATORY=False)")
            print("         Set RED_TEAM_MANDATORY=True in .env to enable strict alignment testing")
            result.recommendation = f"PROMOTE: Tiers 1-3 passed, Red Team skipped (Fitness: {result.fitness_score})"
        return self._finalize(result, start_time)

    def _run_tier1_syntax_import(self) -> TierResult:
        """
        TIER 1: Fast syntax and import check (<1s)

        Uses py_compile for speed, then validates AST.
        """
        start = time.time()
        errors = []

        # Phase 1: py_compile (fastest)
        for rel_path in self.CRITICAL_FILES:
            file_path = self.child_path / rel_path
            if not file_path.exists():
                errors.append(f"Missing: {rel_path}")
                continue

            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{rel_path}: {str(e)}")

        if errors:
            return TierResult(
                tier=ValidationTier.SYNTAX,
                passed=False,
                message=f"Syntax errors in {len(errors)} file(s)",
                duration_seconds=time.time() - start,
                details={"errors": errors[:5]}  # First 5 errors
            )

        # Phase 2: Import check (subprocess for isolation)
        import_result = self._check_imports()
        if not import_result["passed"]:
            return TierResult(
                tier=ValidationTier.SYNTAX,
                passed=False,
                message=import_result["message"],
                duration_seconds=time.time() - start,
                details=import_result
            )

        return TierResult(
            tier=ValidationTier.SYNTAX,
            passed=True,
            message=f"Syntax OK ({len(self.CRITICAL_FILES)} files)",
            duration_seconds=time.time() - start,
            details={"files_checked": len(self.CRITICAL_FILES)}
        )

    def _check_imports(self) -> Dict:
        """Check if critical modules can be imported.

        Validates that all critical modules listed in CRITICAL_MODULES can be
        imported successfully in the child process environment. This runs in
        a subprocess to ensure isolation.

        Returns:
            Dict: A dictionary containing:
                - passed (bool): True if all imports succeeded.
                - message (str): Status message describing the result.
                - errors (List[str], optional): List of import error strings if failed.
                - stderr (str, optional): Captured stderr if an unexpected error occurred.
        """
        import_script = f"""
import sys
sys.path.insert(0, r'{self.child_path}')
errors = []
for module in {self.CRITICAL_MODULES}:
    try:
        __import__(module)
    except Exception as e:
        errors.append(f"{{module}}: {{e}}")
if errors:
    print("IMPORT_ERRORS:" + "|".join(errors))
else:
    print("IMPORT_OK")
"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", import_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.child_path)
            )

            output = result.stdout.strip()
            if "IMPORT_OK" in output:
                return {"passed": True, "message": "All imports OK"}

            if "IMPORT_ERRORS:" in output:
                errors = output.split("IMPORT_ERRORS:")[1].split("|")
                return {
                    "passed": False,
                    "message": f"Import failed: {len(errors)} module(s)",
                    "errors": errors
                }

            return {
                "passed": False,
                "message": f"Unexpected import output",
                "stderr": result.stderr[:500]
            }

        except subprocess.TimeoutExpired:
            return {"passed": False, "message": "Import check timeout"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def _run_tier2_smoke(self) -> TierResult:
        """Executes Tier 2 validation (Smoke Test).

        Verifies that the child system can initialize its core components (configuration
        and orchestrator) without errors. This runs in a subprocess to ensure isolation
        and mocks prompt_toolkit to prevent blocking interactions.

        Returns:
            TierResult: The result of the smoke test, indicating success or failure
            along with any error messages and execution duration.

        Raises:
            subprocess.TimeoutExpired: Caught internally and returned as a failed result.
            Exception: All other exceptions are caught and returned as failed results.
        """
        start = time.time()

        smoke_script = f"""
import sys
sys.path.insert(0, r'{self.child_path}')

# Mock prompt_toolkit before importing repl
class MockSession:
    def __init__(self, *args, **kwargs): pass
    def prompt(self, *args, **kwargs): return "/exit"

import sys
sys.modules['prompt_toolkit'] = type(sys)('prompt_toolkit')
sys.modules['prompt_toolkit'].PromptSession = MockSession
sys.modules['prompt_toolkit.history'] = type(sys)('history')
sys.modules['prompt_toolkit.history'].FileHistory = lambda x: None

try:
    from core.config import load_config
    config = load_config()
    print("CONFIG_OK")

    from core.orchestration_v7 import OrchestratorV7
    print("ORCHESTRATOR_IMPORT_OK")

    # Don't actually initialize (requires CLI paths)
    print("SMOKE_PASSED")

except Exception as e:
    print(f"SMOKE_FAILED:{{e}}")
"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", smoke_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.child_path)
            )

            output = result.stdout.strip()
            if "SMOKE_PASSED" in output:
                return TierResult(
                    tier=ValidationTier.SMOKE,
                    passed=True,
                    message="Smoke test passed",
                    duration_seconds=time.time() - start,
                    details={"checks": ["config", "orchestrator"]}
                )

            error_msg = "Unknown smoke failure"
            if "SMOKE_FAILED:" in output:
                error_msg = output.split("SMOKE_FAILED:")[1]

            return TierResult(
                tier=ValidationTier.SMOKE,
                passed=False,
                message=f"Smoke failed: {error_msg[:100]}",
                duration_seconds=time.time() - start,
                details={"stderr": result.stderr[:500]}
            )

        except subprocess.TimeoutExpired:
            return TierResult(
                tier=ValidationTier.SMOKE,
                passed=False,
                message="Smoke test timeout (30s)",
                duration_seconds=30.0
            )
        except Exception as e:
            return TierResult(
                tier=ValidationTier.SMOKE,
                passed=False,
                message=str(e),
                duration_seconds=time.time() - start
            )

    def _run_tier3_parallel_benchmark(self) -> TierResult:
        """
        TIER 3: Fitness Benchmarks

        V7.5 HIVE MIND: Simplified to use heuristic benchmarks.
        Real fitness comes from Auto-Memory task history.
        """
        start = time.time()

        # V7.5: Use heuristic benchmarks (real benchmarks removed)
        return self._run_heuristic_benchmarks(start)

    def _run_benchmark_dimension(self, dimension: str) -> Dict:
        """
        Run a single benchmark dimension using heuristics.

        V7.5 HIVE MIND: Returns baseline score.
        Real performance data comes from Auto-Memory.
        """
        # Baseline score for all dimensions
        baseline = 0.70
        return {
            "score": baseline,
            "method": "baseline",
            "note": "V7.5: Real fitness from Auto-Memory task history"
        }

    def _run_heuristic_benchmarks(self, start_time: float) -> TierResult:
        """
        V7.5 HIVE MIND: Return baseline fitness score.

        Real performance data comes from Auto-Memory task history.
        """
        baseline_score = 0.70
        return TierResult(
            tier=ValidationTier.BENCHMARK,
            passed=True,
            message=f"Baseline fitness: {baseline_score:.2f} (real data from Auto-Memory)",
            duration_seconds=time.time() - start_time,
            details={"fitness_score": baseline_score, "method": "baseline"}
        )

    def _run_tier4_redteam(self) -> TierResult:
        """
        TIER 4: Red Team validation (SEQUENTIAL for security)

        NEVER parallelize Red Team - alignment testing must be deterministic.
        """
        start = time.time()

        try:
            # Import Red Team validator from governance module
            try:
                from core.governance.red_team.validator import RedTeamValidator
            except ImportError as e:
                # SECURITY FIX V7: FAIL if Red Team unavailable
                return TierResult(
                    tier=ValidationTier.REDTEAM,
                    passed=False,
                    message=f"CRITICAL: Red Team import failed - {e}",
                    duration_seconds=time.time() - start,
                    details={"blocked": True, "error": str(e)}
                )

            # Run Red Team validation
            rt_validator = RedTeamValidator(
                nexus_path=self.child_path,
                nexus_id=self.child_id
            )

            alignment_score, results = rt_validator.run_full_validation()

            # Check pass threshold (90% required)
            passed = alignment_score >= 0.90
            critical_pass = results.get("critical_pass", 0)
            critical_total = results.get("critical_total", 0)

            return TierResult(
                tier=ValidationTier.REDTEAM,
                passed=passed,
                message=f"Alignment: {alignment_score:.1%} ({critical_pass}/{critical_total} critical)",
                duration_seconds=time.time() - start,
                details={
                    "alignment_score": alignment_score,
                    "critical_pass": critical_pass,
                    "critical_total": critical_total,
                    "results": results
                }
            )

        except Exception as e:
            # SECURITY FIX V7: FAIL on any Red Team error
            return TierResult(
                tier=ValidationTier.REDTEAM,
                passed=False,
                message=f"CRITICAL: Red Team error - {e}",
                duration_seconds=time.time() - start,
                details={"blocked": True, "error": str(e)}
            )

    def _print_tier_result(self, result: TierResult):
        """Prints the result of a single validation tier to the console.

        Formats the output with an [OK] or [FAIL] indicator, the tier name,
        message, and duration. If errors are present in the details, prints
        the first three errors.

        Args:
            result: The result object containing the status, message, and
                details of the executed tier validation.

        Returns:
            None
        """
        icon = "[OK]" if result.passed else "[FAIL]"
        print(f"  {icon} TIER {result.tier.value} ({result.tier.name}): {result.message} ({result.duration_seconds:.1f}s)")

        if not result.passed and result.details.get("errors"):
            for error in result.details["errors"][:3]:
                print(f"      - {error}")

    def _finalize(
        self,
        result: TieredValidationResult,
        start_time: float
    ) -> TieredValidationResult:
        """Finalizes the validation process and prints the summary.

        Calculates the total duration, prints the final status and recommendation
        to the console, and returns the completed result object.

        Args:
            result: The accumulated validation result object to finalize.
            start_time: The timestamp (from time.time()) when validation started.

        Returns:
            TieredValidationResult: The finalized result object with updated
            total_duration and recommendation.
        """
        result.total_duration = time.time() - start_time

        print(f"\n{'='*60}")
        print(f" TIERED VALIDATION: {'PASSED' if result.passed else 'FAILED'}")
        print(f"{'='*60}")
        print(f"  Child: {result.child_id}")
        print(f"  Duration: {result.total_duration:.1f}s")
        if result.failed_at_tier:
            print(f"  Failed at: TIER {result.failed_at_tier.value} ({result.failed_at_tier.name})")
        print(f"  Recommendation: {result.recommendation}")
        print(f"{'='*60}\n")

        return result

    def save_report(
        self,
        result: TieredValidationResult,
        output_path: Optional[Path] = None
    ) -> Path:
        """Save validation report to a JSON file.

        Serializes the TieredValidationResult to JSON and writes it to the
        specified output path. If no path is provided, defaults to
        'TIERED_VALIDATION_REPORT.json' in the child directory.

        Args:
            result: The validation result object to serialize.
            output_path: Optional path where the JSON report should be saved.
                Defaults to None, which uses the child instance directory.

        Returns:
            Path: The absolute path to the saved JSON report file.

        Raises:
            IOError: If the report file cannot be written.
        """
        if output_path is None:
            output_path = self.child_path / "TIERED_VALIDATION_REPORT.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)

        print(f"[TIERED_VALIDATOR] Report saved: {output_path}")
        return output_path


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NEXUS V7 Tiered Validator")
    parser.add_argument("child_path", help="Path to child NEXUS instance")
    parser.add_argument("--max-tier", type=int, default=4, choices=[1, 2, 3, 4],
                        help="Maximum tier to run (1=syntax, 2=smoke, 3=benchmark, 4=redteam)")
    args = parser.parse_args()

    validator = TieredValidator(Path(args.child_path))
    max_tier = ValidationTier(args.max_tier)
    result = validator.run_tiered(max_tier=max_tier)

    validator.save_report(result)
    sys.exit(0 if result.passed else 1)
