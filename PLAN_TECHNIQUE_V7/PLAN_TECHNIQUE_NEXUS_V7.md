# 🎯 PLAN TECHNIQUE NEXUS V7 - Guide d'implémentation

**Destinataire**: Claude Code Sonnet 4.5
**Objectif**: Rendre NEXUS production-ready
**Durée estimée**: 10 jours de développement
**Priorité**: Benchmarks → Red Team → Mutations → Polish

---

## 📋 Vue d'ensemble

### Problèmes critiques à résoudre

| # | Problème | Fichier concerné | Priorité |
|---|----------|------------------|----------|
| 1 | Benchmarks simulés (random) | `core/evolution/evaluator.py` | 🔴 CRITIQUE |
| 2 | Red Team tests absents | `benchmarks/red_team.py` (à créer) | 🔴 CRITIQUE |
| 3 | Rate limiting non appliqué | `core/evolution/rate_limiter.py` (à créer) | 🟠 HAUTE |
| 4 | Mutations placeholder | `core/evolution/mutator.py` | 🟠 HAUTE |
| 5 | Heuristiques FINISHED fragiles | `core/drivers/claude_driver_hybrid.py` | 🟠 HAUTE |
| 6 | Tokens estimation approximative | `core/synapse/memory_v6.py` | 🟡 MOYENNE |
| 7 | Timeout bootstrap Windows | `core/meta/cli_inspector.py` | 🟡 MOYENNE |

---

## 🗓️ Planning détaillé

### PHASE 1: BENCHMARKS RÉELS (Jours 1-3)

**Objectif**: Remplacer les scores ASI simulés par des mesures réelles

#### Jour 1: Infrastructure benchmarks

```
NEXUS_V6_PROTOTYPE/
├── benchmarks/
│   ├── __init__.py
│   ├── asi_benchmark.py      # Orchestrateur principal
│   ├── coding/
│   │   ├── __init__.py
│   │   ├── humaneval.py      # HumanEval benchmark
│   │   └── simple_tasks.py   # Tâches coding simples
│   ├── reasoning/
│   │   ├── __init__.py
│   │   ├── gsm8k.py          # Math word problems
│   │   └── logic_puzzles.py  # Puzzles logiques
│   ├── creativity/
│   │   ├── __init__.py
│   │   └── novel_tasks.py    # Tâches ouvertes
│   └── scalability/
│       ├── __init__.py
│       └── multi_file.py     # Refactoring multi-fichiers
```

#### Jour 2: Implémentation coding + reasoning

**Fichier**: `benchmarks/asi_benchmark.py`
```python
"""
ASI Benchmark Orchestrator - Mesures RÉELLES du score ASI
"""
from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass
import json
import time

@dataclass
class BenchmarkResult:
    dimension: str
    score: float  # 0.0 - 1.0
    tasks_passed: int
    tasks_total: int
    details: Dict
    duration_seconds: float

class ASIBenchmark:
    """Orchestrateur des benchmarks ASI"""

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
        Exécute tous les benchmarks et retourne le score ASI.

        Returns:
            (asi_score, results_by_dimension)
        """
        results = {}

        # 1. Coding (30%)
        results["coding"] = self._run_coding_benchmark()

        # 2. Reasoning (30%)
        results["reasoning"] = self._run_reasoning_benchmark()

        # 3. Creativity (25%)
        results["creativity"] = self._run_creativity_benchmark()

        # 4. Scalability (15%)
        results["scalability"] = self._run_scalability_benchmark()

        # Calcul score ASI pondéré
        asi_score = sum(
            results[dim].score * self.WEIGHTS[dim]
            for dim in self.WEIGHTS
        )

        return round(asi_score, 4), results

    def _run_coding_benchmark(self) -> BenchmarkResult:
        """Benchmark coding: tâches de génération/correction de code"""
        from benchmarks.coding.simple_tasks import CodingTasks

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

    def _run_reasoning_benchmark(self) -> BenchmarkResult:
        """Benchmark reasoning: puzzles logiques et math"""
        from benchmarks.reasoning.logic_puzzles import LogicPuzzles

        start = time.time()
        puzzles = LogicPuzzles(self.nexus_path, self.timeout)
        passed, total, details = puzzles.run_all()

        return BenchmarkResult(
            dimension="reasoning",
            score=passed / total if total > 0 else 0,
            tasks_passed=passed,
            tasks_total=total,
            details=details,
            duration_seconds=time.time() - start
        )

    def _run_creativity_benchmark(self) -> BenchmarkResult:
        """Benchmark creativity: solutions originales"""
        from benchmarks.creativity.novel_tasks import NovelTasks

        start = time.time()
        tasks = NovelTasks(self.nexus_path, self.timeout)
        score, details = tasks.run_all()

        return BenchmarkResult(
            dimension="creativity",
            score=score,
            tasks_passed=int(score * 10),
            tasks_total=10,
            details=details,
            duration_seconds=time.time() - start
        )

    def _run_scalability_benchmark(self) -> BenchmarkResult:
        """Benchmark scalability: tâches multi-fichiers"""
        from benchmarks.scalability.multi_file import MultiFileTasks

        start = time.time()
        tasks = MultiFileTasks(self.nexus_path, self.timeout)
        passed, total, details = tasks.run_all()

        return BenchmarkResult(
            dimension="scalability",
            score=passed / total if total > 0 else 0,
            tasks_passed=passed,
            tasks_total=total,
            details=details,
            duration_seconds=time.time() - start
        )
```

**Fichier**: `benchmarks/coding/simple_tasks.py`
```python
"""
Tâches de coding pour benchmark ASI
"""
from pathlib import Path
from typing import Tuple, Dict, List
import subprocess
import tempfile

class CodingTasks:
    """10 tâches de coding avec vérification automatique"""

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
        """Exécute toutes les tâches et retourne (passed, total, details)"""
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

        return passed, len(self.TASKS), details

    def _run_task(self, task: Dict) -> Tuple[bool, str]:
        """Exécute une tâche et vérifie le résultat"""
        # Invoke NEXUS pour générer le code
        code = self._invoke_nexus(task["prompt"])

        if not code:
            return False, "No code generated"

        # Tester le code généré
        return self._verify_code(code, task["test_cases"])

    def _invoke_nexus(self, prompt: str) -> str:
        """Appelle NEXUS pour générer du code"""
        # TODO: Implémenter l'appel réel à NEXUS
        # Pour l'instant, placeholder
        return ""

    def _verify_code(self, code: str, test_cases: List[Tuple]) -> Tuple[bool, str]:
        """Vérifie le code avec les test cases"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.write("\n\n# Test cases\n")
            for expr, expected in test_cases:
                f.write(f"assert {expr} == {repr(expected)}, f'Failed: {expr}'\n")
            f.write("print('ALL TESTS PASSED')\n")
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if "ALL TESTS PASSED" in result.stdout:
                return True, "All tests passed"
            return False, result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
```

#### Jour 3: Intégration dans evaluator.py

**Modifier**: `core/evolution/evaluator.py`
```python
# REMPLACER run_simulated_benchmarks par:

def run_benchmarks(nexus_path: Path, nexus_id: str) -> Dict:
    """
    Exécute les VRAIS benchmarks ASI.
    """
    from benchmarks.asi_benchmark import ASIBenchmark

    benchmark = ASIBenchmark(nexus_path)
    asi_score, results = benchmark.run_full_benchmark()

    return {
        "nexus_id": nexus_id,
        "benchmark_suite": "asi_proximity_real",
        "timestamp": datetime.now().isoformat(),
        "asi_score": asi_score,
        "scores": {
            dim: results[dim].score for dim in results
        },
        "details": {
            dim: results[dim].details for dim in results
        },
        "simulated": False  # IMPORTANT: plus simulé!
    }
```

---

### PHASE 2: RED TEAM TESTS (Jours 4-5)

Voir fichier `PLAN_TECHNIQUE_PART2.md`

---

### PHASE 3: RATE LIMITING & MUTATIONS (Jours 6-8)

Voir fichier `PLAN_TECHNIQUE_PART3.md`

---

### PHASE 4: POLISH & INTÉGRATION (Jours 9-10)

Voir fichier `PLAN_TECHNIQUE_PART4.md`

---

## ✅ Checklist de validation

Avant de considérer une phase terminée:

- [ ] Tests unitaires passent
- [ ] Code documenté (docstrings)
- [ ] Pas de placeholders restants
- [ ] Intégration avec orchestrator testée
- [ ] Git commit signé
