"""
ASI Benchmark Orchestrator - REAL MEASUREMENT Engine

Orchestrates the evaluation of NEXUS across 4 dimensions:
1. Coding (30%) - 10 real Python tasks
2. Reasoning (30%) - Heuristic analysis of FSM complexity (MVP)
3. Creativity (25%) - Heuristic analysis of mutation diversity (MVP)
4. Scalability (15%) - Heuristic analysis of modularity (MVP)

Note: For MVP Phase 1, only "Coding" is fully dynamic. 
Other dimensions use static heuristic analysis of the codebase itself 
to avoid needing 4 complex datasets immediately.
"""
from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import time
import sys

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

    def run_full_benchmark(self) -> Tuple[float, Dict[str, BenchmarkResult]]:
        """
        Execute all benchmarks and return ASI score.

        Returns:
            (asi_score, results_by_dimension)
        """
        print(f"[BENCHMARK] Starting full ASI benchmark on {self.nexus_path.name}")
        results = {}

        # 1. Coding (Dynamic)
        results["coding"] = self._run_coding_benchmark()

        # 2. Reasoning (Static Heuristic)
        results["reasoning"] = self._run_reasoning_heuristic()

        # 3. Creativity (Static Heuristic)
        results["creativity"] = self._run_creativity_heuristic()

        # 4. Scalability (Static Heuristic)
        results["scalability"] = self._run_scalability_heuristic()

        # Calculate weighted ASI score
        asi_score = sum(
            results[dim].score * self.WEIGHTS[dim]
            for dim in self.WEIGHTS
        )

        print(f"[BENCHMARK] Final ASI Score: {asi_score:.4f}")
        return round(asi_score, 4), results

    def _run_coding_benchmark(self) -> BenchmarkResult:
        """Coding benchmark: Real Python task generation."""
        print("[BENCHMARK] Running Coding tasks...")
        try:
            # Import from consolidated BENCHMARKS directory at project root
            benchmarks_root = self.nexus_path.parent  # 20_NEXUS/
            if str(benchmarks_root) not in sys.path:
                sys.path.insert(0, str(benchmarks_root))
            from BENCHMARKS.coding.simple_tasks import CodingTasks
            
            start = time.time()
            tasks = CodingTasks(self.nexus_path, self.timeout)
            passed, total, details = tasks.run_all()
            
            return BenchmarkResult(
                dimension="coding",
                score=passed / total if total > 0 else 0,
                tasks_passed=passed,
                tasks_total=total,
                details=details,
                duration_seconds=time.time() - start
            )
        except Exception as e:
            print(f"[BENCHMARK] Coding benchmark failed: {e}")
            import traceback
            traceback.print_exc()
            return BenchmarkResult("coding", 0.0, 0, 10, {"error": str(e)}, 0.0)

    def _run_reasoning_heuristic(self) -> BenchmarkResult:
        """
        Reasoning heuristic: Analyzes the complexity of the FSM and Logic.
        More states + complex transitions = higher reasoning potential.
        """
        start = time.time()
        score = 0.5 # Base score
        details = {}
        
        # Analyze orchestration_v6.py
        orch_path = self.nexus_path / "core" / "orchestration_v6.py"
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
