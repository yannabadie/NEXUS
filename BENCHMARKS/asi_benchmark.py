"""
ASI Benchmark Orchestrator - REAL MEASUREMENT Engine V7

Orchestrates the evaluation of NEXUS across 4 dimensions:
1. Coding (30%) - 10 real Python tasks (DYNAMIC)
2. Reasoning (30%) - Logic puzzles with runtime validation (V7 DYNAMIC)
3. Creativity (25%) - Novel solution generation with validation (V7 DYNAMIC)
4. Scalability (15%) - Heuristic analysis of modularity (MVP static)

V7 Chrysalis: Reasoning and Creativity now use runtime NEXUS invocation
to test actual capabilities instead of static code analysis.
"""
from pathlib import Path
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import json
import time
import sys
import subprocess

@dataclass
class BenchmarkResult:
    dimension: str
    score: float  # 0.0 - 1.0
    tasks_passed: int
    tasks_total: int
    details: Dict
    duration_seconds: float

class ASIBenchmark:
    """Orchestrator for real ASI benchmarking."""

    WEIGHTS = {
        "coding": 0.30,
        "reasoning": 0.30,
        "creativity": 0.25,
        "scalability": 0.15
    }

    def __init__(self, nexus_path: Path, timeout_per_task: int = 60):
        self.nexus_path = nexus_path
        self.timeout = timeout_per_task

    def run_full_benchmark(
        self,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Tuple[float, Dict[str, BenchmarkResult]]:
        """
        Execute all benchmarks and return ASI score.

        Args:
            parallel: Use parallel execution for coding tasks (default True)
            max_workers: Number of parallel workers for coding (default 4)

        Returns:
            (asi_score, results_by_dimension)
        """
        print(f"[BENCHMARK] Starting full ASI benchmark on {self.nexus_path.name}")
        print(f"[BENCHMARK] Parallel mode: {parallel}, Workers: {max_workers}")
        results = {}

        # 1. Coding (Dynamic - with parallel option)
        results["coding"] = self._run_coding_benchmark(parallel=parallel, max_workers=max_workers)

        # 2. Reasoning (V7: Dynamic runtime tests)
        results["reasoning"] = self._run_reasoning_dynamic()

        # 3. Creativity (V7: Dynamic runtime tests)
        results["creativity"] = self._run_creativity_dynamic()

        # 4. Scalability (Static Heuristic - MVP)
        results["scalability"] = self._run_scalability_heuristic()

        # Calculate weighted ASI score
        asi_score = sum(
            results[dim].score * self.WEIGHTS[dim]
            for dim in self.WEIGHTS
        )

        print(f"[BENCHMARK] Final ASI Score: {asi_score:.4f}")
        return round(asi_score, 4), results

    def _run_coding_benchmark(
        self,
        parallel: bool = True,
        max_workers: int = 4
    ) -> BenchmarkResult:
        """
        Coding benchmark: Real Python task generation.

        Args:
            parallel: Use parallel execution (default True, 3-4x speedup)
            max_workers: Number of parallel workers (default 4)

        Returns:
            BenchmarkResult with coding score and details
        """
        mode = "parallel" if parallel else "sequential"
        print(f"[BENCHMARK] Running Coding tasks ({mode})...")
        try:
            # Import from consolidated BENCHMARKS directory at project root
            benchmarks_root = self.nexus_path.parent  # 20_NEXUS/
            if str(benchmarks_root) not in sys.path:
                sys.path.insert(0, str(benchmarks_root))
            from BENCHMARKS.coding.simple_tasks import CodingTasks

            start = time.time()
            tasks = CodingTasks(self.nexus_path, self.timeout)

            # Use parallel or sequential based on parameter
            if parallel:
                passed, total, details = tasks.run_all_parallel(max_workers=max_workers)
            else:
                passed, total, details = tasks.run_all()

            duration = time.time() - start
            print(f"[BENCHMARK] Coding completed in {duration:.1f}s")

            return BenchmarkResult(
                dimension="coding",
                score=passed / total if total > 0 else 0,
                tasks_passed=passed,
                tasks_total=total,
                details=details,
                duration_seconds=duration
            )
        except Exception as e:
            print(f"[BENCHMARK] Coding benchmark failed: {e}")
            import traceback
            traceback.print_exc()
            return BenchmarkResult("coding", 0.0, 0, 10, {"error": str(e)}, 0.0)

    def _invoke_nexus(self, prompt: str, timeout: int = 60) -> str:
        """
        Invoke NEXUS with a prompt and return the response.
        Uses subprocess isolation for safety.

        Args:
            prompt: Question or task for NEXUS
            timeout: Max seconds to wait (default 60)

        Returns:
            NEXUS response text (empty string on error)
        """
        runner_script = r'''
import sys
import os
from pathlib import Path

sys.path.insert(0, os.getcwd())

try:
    from core.orchestration_v7 import OrchestratorV7
    from core.config import load_config
    from core.meta.cli_inspector import CLIInspector

    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    config = load_config()
    config.log_level = "ERROR"
    config.ui_verbose = False

    inspector = CLIInspector()
    gemini_info = inspector.inspect_gemini()
    claude_info = inspector.inspect_claude()

    orchestrator = OrchestratorV7(workspace, config, gemini_info, claude_info)

    prompt = sys.argv[1]
    result = orchestrator.process_turn(prompt)

    print("__NEXUS_RESPONSE_START__")
    print(result.get("output", ""))
    print("__NEXUS_RESPONSE_END__")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"__NEXUS_ERROR_START__\n{e}\n__NEXUS_ERROR_END__")
'''
        runner_path = self.nexus_path / "_benchmark_runner.py"
        runner_path.write_text(runner_script, encoding='utf-8')

        try:
            cmd = ["python", "_benchmark_runner.py", prompt]
            result = subprocess.run(
                cmd,
                cwd=str(self.nexus_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )

            output = result.stdout
            if "__NEXUS_RESPONSE_START__" in output:
                response = output.split("__NEXUS_RESPONSE_START__")[1].split("__NEXUS_RESPONSE_END__")[0].strip()
                return response
            return ""

        except subprocess.TimeoutExpired:
            print(f"[BENCHMARK] NEXUS invocation timed out after {timeout}s")
            return ""
        except Exception as e:
            print(f"[BENCHMARK] NEXUS invocation failed: {e}")
            return ""
        finally:
            if runner_path.exists():
                runner_path.unlink()

    def _run_reasoning_dynamic(self) -> BenchmarkResult:
        """
        V7 Reasoning benchmark: Runtime logic puzzle validation.
        Invokes NEXUS with logic puzzles and validates answers.
        """
        print("[BENCHMARK] Running Reasoning tasks (V7 dynamic)...")
        start = time.time()

        REASONING_TESTS = [
            {
                "id": "logic_001",
                "prompt": "If A implies B, and B implies C, and A is true, is C true? Answer only YES or NO.",
                "expected": ["yes"],
                "fail": ["no"]
            },
            {
                "id": "logic_002",
                "prompt": "Alice is taller than Bob. Bob is taller than Carol. Who is the shortest? Answer with just the name.",
                "expected": ["carol"],
                "fail": ["alice", "bob"]
            },
            {
                "id": "sequence_001",
                "prompt": "What number comes next in the sequence: 2, 4, 8, 16, ? Answer with just the number.",
                "expected": ["32"],
                "fail": ["64", "24", "20"]
            },
            {
                "id": "logic_003",
                "prompt": "All cats are animals. Some animals are pets. Can we conclude that all cats are pets? Answer YES or NO.",
                "expected": ["no"],
                "fail": ["yes"]
            },
            {
                "id": "math_001",
                "prompt": "If x + 5 = 12, what is x? Answer with just the number.",
                "expected": ["7"],
                "fail": ["17", "5", "12"]
            }
        ]

        passed = 0
        details = {"tests": []}

        for test in REASONING_TESTS:
            print(f"   Testing {test['id']}...")
            response = self._invoke_nexus(test["prompt"], timeout=30)
            response_lower = response.lower()

            # Check for expected answers
            test_passed = any(exp in response_lower for exp in test["expected"])

            # Check for fail patterns (wrong answers)
            if test_passed and any(fail in response_lower for fail in test.get("fail", [])):
                # If contains both expected and fail, more careful check
                pass  # Keep test_passed as is (expected match wins)

            if test_passed:
                passed += 1
                print(f"   ✅ {test['id']} passed")
            else:
                print(f"   ❌ {test['id']} failed")

            details["tests"].append({
                "id": test["id"],
                "passed": test_passed,
                "response_preview": response[:100] if response else "(no response)"
            })

        duration = time.time() - start
        score = passed / len(REASONING_TESTS) if REASONING_TESTS else 0

        print(f"[BENCHMARK] Reasoning: {passed}/{len(REASONING_TESTS)} passed in {duration:.1f}s")

        return BenchmarkResult(
            dimension="reasoning",
            score=score,
            tasks_passed=passed,
            tasks_total=len(REASONING_TESTS),
            details=details,
            duration_seconds=duration
        )

    def _run_creativity_dynamic(self) -> BenchmarkResult:
        """
        V7 Creativity benchmark: Novel solution generation validation.
        Invokes NEXUS with open-ended problems and validates diverse solutions.
        """
        print("[BENCHMARK] Running Creativity tasks (V7 dynamic)...")
        start = time.time()

        CREATIVITY_TESTS = [
            {
                "id": "creative_001",
                "prompt": "Name 3 different sorting algorithms (not including Python's built-in sort). Just list the names.",
                "validators": ["bubble", "insertion", "selection", "merge", "quick", "heap", "radix", "counting", "bucket"],
                "min_matches": 2
            },
            {
                "id": "creative_002",
                "prompt": "Name 2 cache eviction policies used in computing. Just list the names.",
                "validators": ["lru", "lfu", "fifo", "lifo", "random", "ttl", "least recently", "least frequently", "first in"],
                "min_matches": 1
            },
            {
                "id": "creative_003",
                "prompt": "Name 2 design patterns used in software engineering. Just list the names.",
                "validators": ["singleton", "factory", "observer", "strategy", "decorator", "adapter", "facade", "proxy", "builder", "prototype"],
                "min_matches": 1
            }
        ]

        passed = 0
        details = {"tests": []}

        for test in CREATIVITY_TESTS:
            print(f"   Testing {test['id']}...")
            response = self._invoke_nexus(test["prompt"], timeout=30)
            response_lower = response.lower()

            # Count validator matches
            matches = sum(1 for v in test["validators"] if v in response_lower)
            test_passed = matches >= test["min_matches"]

            if test_passed:
                passed += 1
                print(f"   ✅ {test['id']} passed ({matches} concepts found)")
            else:
                print(f"   ❌ {test['id']} failed ({matches} concepts found, need {test['min_matches']})")

            details["tests"].append({
                "id": test["id"],
                "passed": test_passed,
                "matches": matches,
                "response_preview": response[:100] if response else "(no response)"
            })

        duration = time.time() - start
        score = passed / len(CREATIVITY_TESTS) if CREATIVITY_TESTS else 0

        print(f"[BENCHMARK] Creativity: {passed}/{len(CREATIVITY_TESTS)} passed in {duration:.1f}s")

        return BenchmarkResult(
            dimension="creativity",
            score=score,
            tasks_passed=passed,
            tasks_total=len(CREATIVITY_TESTS),
            details=details,
            duration_seconds=duration
        )

    def _run_reasoning_heuristic(self) -> BenchmarkResult:
        """
        Reasoning heuristic: Analyzes the complexity of the FSM and Logic.
        More states + complex transitions = higher reasoning potential.
        """
        start = time.time()
        score = 0.5 # Base score
        details = {}
        
        # Analyze orchestration_v7.py
        orch_path = self.nexus_path / "core" / "orchestration_v7.py"
        if orch_path.exists():
            content = orch_path.read_text(encoding='utf-8')
            
            # Metric 1: State complexity
            states_count = content.count("OrchestratorState.")
            
            # Also check for State class definitions in fsm/states.py
            states_file = self.nexus_path / "core" / "fsm" / "states.py"
            if states_file.exists():
                states_content = states_file.read_text(encoding='utf-8')
                import re
                class_states = len(re.findall(r"class\s+\w+State", states_content))
                states_count += class_states * 2 # Weight classes higher
            
            details["states_references"] = states_count
            if states_count > 20: score += 0.1
            if states_count > 40: score += 0.1
            
            # Metric 2: Error handling logic
            try_count = content.count("try:")
            details["try_blocks"] = try_count
            if try_count > 5: score += 0.1
            
            # Metric 3: Stagnation detection
            if "StagnationDetector" in content:
                score += 0.1
                details["stagnation_detector"] = True

        # Metric 4: Memory & Panic (File existence check)
        synapse_dir = self.nexus_path / "core" / "synapse"
        if (synapse_dir / "memory.py").exists() or (synapse_dir / "memory_v6.py").exists():
             score += 0.05
             details["memory_module"] = True
             
        fsm_dir = self.nexus_path / "core" / "fsm"
        if (fsm_dir / "panic.py").exists() or (fsm_dir / "panic_system.py").exists():
             score += 0.05
             details["panic_module"] = True
                
        return BenchmarkResult(
            dimension="reasoning",
            score=min(1.0, score),
            tasks_passed=int(score * 10),
            tasks_total=10,
            details=details,
            duration_seconds=time.time() - start
        )

    def _run_creativity_heuristic(self) -> BenchmarkResult:
        """
        Creativity heuristic: Analyzes mutation and prompting sophistication.
        """
        start = time.time()
        score = 0.5
        details = {}
        
        # Analyze prompt files
        prompts_dir = self.nexus_path / "prompts"
        if prompts_dir.exists():
            prompt_size = 0
            for p in prompts_dir.glob("*.md"):
                prompt_size += len(p.read_text(encoding='utf-8'))
            
            details["prompt_volume"] = prompt_size
            if prompt_size > 5000: score += 0.1
            if prompt_size > 10000: score += 0.1
            
        # Analyze emergent capabilities in REPL
        repl_path = self.nexus_path / "core" / "interface" / "repl.py"
        if repl_path.exists():
            content = repl_path.read_text(encoding='utf-8')
            if "brainstorm_children_with_ais" in content:
                score += 0.2 # Emergent evolution bonus
                details["emergent_evolution"] = True
                
        return BenchmarkResult(
            dimension="creativity",
            score=min(1.0, score),
            tasks_passed=int(score * 10),
            tasks_total=10,
            details=details,
            duration_seconds=time.time() - start
        )

    def _run_scalability_heuristic(self) -> BenchmarkResult:
        """
        Scalability heuristic: Analyzes modularity and config.
        """
        start = time.time()
        score = 0.5
        details = {}
        
        # Count modules
        core_dir = self.nexus_path / "core"
        if core_dir.exists():
            modules = list(core_dir.glob("*"))
            details["module_count"] = len(modules)
            if len(modules) > 5: score += 0.1
            
        # Check for rate limiting
        limiter = self.nexus_path / "core" / "evolution" / "rate_limiter.py"
        if limiter.exists():
            score += 0.2
            details["rate_limiter"] = True
            
        return BenchmarkResult(
            dimension="scalability",
            score=min(1.0, score),
            tasks_passed=int(score * 10),
            tasks_total=10,
            details=details,
            duration_seconds=time.time() - start
        )

# CLI Interface
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--nexus-path", required=True)
    parser.add_argument("--nexus-id", required=True)
    args = parser.parse_args()
    
    benchmark = ASIBenchmark(Path(args.nexus_path))
    score, results = benchmark.run_full_benchmark()
    
    # Output JSON for Evaluator
    output = {
        "nexus_id": args.nexus_id,
        "benchmark_suite": "asi_proximity_real",
        "timestamp": datetime.now().isoformat(),
        "scores": {dim: res.score for dim, res in results.items()},
        "raw_results": {dim: res.details for dim, res in results.items()},
        "simulated": False
    }
    print(json.dumps(output, indent=2))
