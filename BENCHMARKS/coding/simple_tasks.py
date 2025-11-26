"""
Coding Tasks Benchmark - Simple Python problems to verify coding capability.
Part of Phase 1: Real Benchmarks implementation.
"""
from pathlib import Path
from typing import Tuple, Dict, List
import subprocess
import tempfile
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class CodingTasks:
    """10 coding tasks with automated verification."""

    TASKS = [
        {
            "id": "fizzbuzz",
            "prompt": "Write a Python function fizzbuzz(n) that returns 'Fizz' if n is divisible by 3, 'Buzz' if divisible by 5, 'FizzBuzz' if both, else str(n).",
            "test_cases": [
                ("fizzbuzz(3)", "Fizz"),
                ("fizzbuzz(5)", "Buzz"),
                ("fizzbuzz(15)", "FizzBuzz"),
                ("fizzbuzz(7)", "7"),
            ]
        },
        {
            "id": "reverse_string",
            "prompt": "Write a Python function reverse_string(s) that reverses a string without using [::-1].",
            "test_cases": [
                ("reverse_string('hello')", "olleh"),
                ("reverse_string('')", ""),
                ("reverse_string('a')", "a"),
            ]
        },
        {
            "id": "is_palindrome",
            "prompt": "Write a Python function is_palindrome(s) that returns True if s is a palindrome (case-insensitive, ignoring spaces).",
            "test_cases": [
                ("is_palindrome('racecar')", True),
                ("is_palindrome('A man a plan a canal Panama')", True),
                ("is_palindrome('hello')", False),
            ]
        },
        {
            "id": "factorial",
            "prompt": "Write a Python function factorial(n) that returns n! using recursion.",
            "test_cases": [
                ("factorial(0)", 1),
                ("factorial(5)", 120),
                ("factorial(10)", 3628800),
            ]
        },
        {
            "id": "fibonacci",
            "prompt": "Write a Python function fibonacci(n) that returns the nth Fibonacci number (0-indexed).",
            "test_cases": [
                ("fibonacci(0)", 0),
                ("fibonacci(1)", 1),
                ("fibonacci(10)", 55),
            ]
        },
        {
            "id": "find_duplicates",
            "prompt": "Write a Python function find_duplicates(lst) that returns a list of duplicate elements.",
            "test_cases": [
                ("sorted(find_duplicates([1,2,2,3,3,3]))", [2, 3]),
                ("find_duplicates([1,2,3])", []),
                ("find_duplicates([])", []),
            ]
        },
        {
            "id": "merge_sorted",
            "prompt": "Write a Python function merge_sorted(a, b) that merges two sorted lists into one sorted list.",
            "test_cases": [
                ("merge_sorted([1,3,5], [2,4,6])", [1,2,3,4,5,6]),
                ("merge_sorted([], [1,2])", [1,2]),
                ("merge_sorted([1], [])", [1]),
            ]
        },
        {
            "id": "count_words",
            "prompt": "Write a Python function count_words(text) that returns a dict of word frequencies (lowercase).",
            "test_cases": [
                ("count_words('hello hello world')['hello']", 2),
                ("count_words('hello hello world')['world']", 1),
                ("len(count_words('a b c'))", 3),
            ]
        },
        {
            "id": "binary_search",
            "prompt": "Write a Python function binary_search(arr, target) that returns the index of target in sorted arr, or -1 if not found.",
            "test_cases": [
                ("binary_search([1,2,3,4,5], 3)", 2),
                ("binary_search([1,2,3,4,5], 6)", -1),
                ("binary_search([], 1)", -1),
            ]
        },
        {
            "id": "flatten_list",
            "prompt": "Write a Python function flatten(lst) that flattens a nested list.",
            "test_cases": [
                ("flatten([[1,2],[3,[4,5]]])", [1,2,3,4,5]),
                ("flatten([1,[2,[3,[4]]]])", [1,2,3,4]),
                ("flatten([])", []),
            ]
        },
    ]

    def __init__(self, nexus_path: Path, timeout: int = 60):
        self.nexus_path = nexus_path
        self.timeout = timeout

    def run_all(self) -> Tuple[int, int, Dict]:
        """Run all tasks sequentially and return (passed, total, details)."""
        passed = 0
        details = {}

        for task in self.TASKS:
            success, result = self._run_task(task)
            details[task["id"]] = {
                "success": success,
                "result": result
            }
            if success:
                passed += 1
            print(f"   Task {task['id']}: {'PASS' if success else 'FAIL'}")

        return passed, len(self.TASKS), details

    def run_all_parallel(self, max_workers: int = 4) -> Tuple[int, int, Dict]:
        """
        Run all coding tasks in parallel for 3-4x speedup.

        Uses ThreadPoolExecutor to run tasks concurrently.
        Each task invokes NEXUS independently, so parallelization is safe.

        Args:
            max_workers: Maximum parallel tasks (default 4, conservative for API limits)

        Returns:
            Tuple of (passed_count, total_count, details_dict)

        Example:
            tasks = CodingTasks(nexus_path)
            passed, total, details = tasks.run_all_parallel(max_workers=4)
            # Runs 10 tasks in ~180s instead of ~600s
        """
        passed = 0
        details = {}

        print(f"[PARALLEL] Running {len(self.TASKS)} tasks with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._run_task, task): task["id"]
                for task in self.TASKS
            }

            # Collect results as they complete
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    success, result = future.result(timeout=self.timeout + 10)
                    details[task_id] = {
                        "success": success,
                        "result": result
                    }
                    if success:
                        passed += 1
                    print(f"   Task {task_id}: {'PASS' if success else 'FAIL'}")
                except Exception as e:
                    details[task_id] = {
                        "success": False,
                        "result": f"Execution error: {e}"
                    }
                    print(f"   Task {task_id}: ERROR - {e}")

        print(f"[PARALLEL] Completed: {passed}/{len(self.TASKS)} passed")
        return passed, len(self.TASKS), details

    def _run_task(self, task: Dict) -> Tuple[bool, str]:
        """Execute a single task."""
        # 1. Invoke NEXUS to generate code
        code = self._invoke_nexus(task["prompt"])

        if not code:
            return False, "No code generated"

        # 2. Verify the generated code
        return self._verify_code(code, task["test_cases"])

    def _invoke_nexus(self, prompt: str) -> str:
        """
        Invoke NEXUS to solve the coding task.
        Uses a subprocess runner to isolate the child environment.
        """
        runner_script = r"""
import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, os.getcwd())

try:
    from core.orchestration_v6 import OrchestratorV6
    from core.config import load_config
    from core.meta.cli_inspector import CLIInspector

    # Initialize minimal environment
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)
    
    config = load_config()
    config.log_level = "ERROR" 
    config.ui_verbose = False

    inspector = CLIInspector()
    gemini_info = inspector.inspect_gemini()
    claude_info = inspector.inspect_claude()
    
    orchestrator = OrchestratorV6(workspace, config, gemini_info, claude_info)
    
    # Prompt specifically for code only
    full_prompt = sys.argv[1] + "\nIMPORTANT: Provide ONLY the Python code. No markdown, no explanations."
    
    result = orchestrator.process_turn(full_prompt)
    
    print("__NEXUS_CODE_START__")
    print(result.get("output", ""))
    print("__NEXUS_CODE_END__")

except Exception as e:
    print(f"__NEXUS_ERROR_START__\n{e}\n__NEXUS_ERROR_END__")
"""
        
        runner_path = self.nexus_path / "_coding_benchmark_runner.py"
        runner_path.write_text(runner_script, encoding='utf-8')
        
        try:
            cmd = ["python", "_coding_benchmark_runner.py", prompt]
            result = subprocess.run(
                cmd,
                cwd=str(self.nexus_path),
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            output = result.stdout
            
            if "__NEXUS_CODE_START__" in output:
                code = output.split("__NEXUS_CODE_START__")[1].split("__NEXUS_CODE_END__")[0].strip()
                # Clean up markdown code blocks if present
                if code.startswith("```python"):
                    code = code[9:]
                if code.startswith("```"):
                    code = code[3:]
                if code.endswith("```"):
                    code = code[:-3]
                return code.strip()
            return ""
            
        except Exception:
            return ""
        finally:
            if runner_path.exists():
                runner_path.unlink()

    def _verify_code(self, code: str, test_cases: List[Tuple]) -> Tuple[bool, str]:
        """Verify the generated code against test cases."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.write("\n\n# Test cases\n")
            f.write("try:\n")
            for expr, expected in test_cases:
                f.write(f"    assert {expr} == {repr(expected)}, f'Failed: {expr} != {repr(expected)}'\n")
            f.write("    print('ALL TESTS PASSED')\n")
            f.write("except AssertionError as e:\n")
            f.write("    print(f'TEST FAILED: {e}')\n")
            f.write("except Exception as e:\n")
            f.write("    print(f'EXECUTION ERROR: {e}')\n")
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout + result.stderr
            
            if "ALL TESTS PASSED" in output:
                return True, "All tests passed"
            return False, output.strip()
            
        except subprocess.TimeoutExpired:
            return False, "Execution Timeout"
        except Exception as e:
            return False, str(e)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
