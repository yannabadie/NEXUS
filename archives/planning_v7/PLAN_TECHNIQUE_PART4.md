# 🔧 PHASE 4: POLISH & INTÉGRATION (Jours 9-10)

---

## Jour 9: Corrections ciblées

### Fix 1: Heuristiques FINISHED fragiles

**Fichier**: `core/drivers/claude_driver_hybrid.py`

```python
# AVANT (fragile)
finish_keywords = ["task complete", "finished", "done", "terminé", "fini"]
if any(keyword in content.lower() for keyword in finish_keywords):
    status = "FINISHED"

# APRÈS (robuste)
def _detect_status(self, content: str, raw_text: str) -> str:
    """
    Détecte le statut de manière robuste.

    Méthodes de détection (par ordre de priorité):
    1. Balise XML explicite <status>FINISHED</status>
    2. Phrase de conclusion explicite en fin de message
    3. Absence de next_agent (fin implicite)
    """

    # Méthode 1: Balise XML explicite (prioritaire)
    status_match = re.search(r'<status>(\w+)</status>', raw_text, re.IGNORECASE)
    if status_match:
        status = status_match.group(1).upper()
        if status in ["FINISHED", "DONE", "COMPLETE"]:
            return "FINISHED"
        return "CONTINUE"

    # Méthode 2: Phrase de conclusion EXPLICITE (pas juste le mot)
    # Doit être en fin de message (dernières 200 chars)
    ending = content[-200:].lower() if len(content) > 200 else content.lower()

    explicit_endings = [
        r"la tâche est (terminée|complète|finie)",
        r"task (is )?(complete|finished|done)",
        r"(j'ai|we have) (terminé|fini|completed)",
        r"✓\s*(tâche|task)\s*(terminée|complete)",
        r"tout est (fait|terminé|ok)",
        r"mission accomplie",
    ]

    for pattern in explicit_endings:
        if re.search(pattern, ending):
            return "FINISHED"

    # Méthode 3: Par défaut, continuer
    return "CONTINUE"
```

### Fix 2: Estimation tokens avec tiktoken

**Fichier**: `core/synapse/memory_v6.py`

```python
# AVANT (approximation)
estimated_tokens = len(history_text) // 4

# APRÈS (précis)
def _estimate_tokens(self, text: str) -> int:
    """
    Estimation précise des tokens avec tiktoken.
    Fallback sur approximation si tiktoken non disponible.
    """
    try:
        import tiktoken
        # Utiliser l'encodeur cl100k_base (compatible Claude/GPT-4)
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: approximation améliorée
        # ~1.3 tokens par mot en moyenne
        words = len(text.split())
        return int(words * 1.3)
    except Exception:
        # Dernier recours
        return len(text) // 4
```

Ajouter dans `requirements_v6.txt`:
```
tiktoken>=0.5.0
```

### Fix 3: Timeout bootstrap Windows

**Fichier**: `core/meta/cli_inspector.py`

```python
# AVANT (pas de timeout)
result = subprocess.run(["gemini", "models", "list"], capture_output=True)

# APRÈS (timeout + fallback)
def _detect_gemini_model(self) -> str:
    """
    Détecte le modèle Gemini disponible.
    Timeout court + fallback sur défaut.
    """
    try:
        result = subprocess.run(
            ["gemini", "models", "list"],
            capture_output=True,
            text=True,
            timeout=10,  # 10 secondes max
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            # Parser la sortie pour trouver le meilleur modèle
            models = self._parse_models_output(result.stdout)
            return self._select_best_model(models)

    except subprocess.TimeoutExpired:
        print("[WARN] Gemini model detection timeout - using default")
    except FileNotFoundError:
        print("[WARN] Gemini CLI not found - using default")
    except Exception as e:
        print(f"[WARN] Model detection error: {e} - using default")

    # Fallback: modèle par défaut
    return self._get_default_model()

def _get_default_model(self) -> str:
    """Retourne le modèle par défaut selon la config"""
    return getattr(self.config, 'default_gemini_model', 'gemini-2.0-flash-thinking-exp')

def _select_best_model(self, models: List[str]) -> str:
    """Sélectionne le meilleur modèle disponible"""
    # Priorité: pro > flash > base
    priority = [
        "gemini-3-pro",
        "gemini-2.5-pro",
        "gemini-2.0-flash-thinking",
        "gemini-2.0-flash",
    ]

    for preferred in priority:
        for model in models:
            if preferred in model.lower():
                return model

    return models[0] if models else self._get_default_model()
```

---

## Jour 10: Tests d'intégration

### Fichier: `tests/test_integration_v7.py`

```python
"""
Tests d'intégration pour NEXUS V7
Valide que tous les composants fonctionnent ensemble.
"""
import pytest
from pathlib import Path
import tempfile
import shutil


class TestEvolutionPipeline:
    """Tests du pipeline d'évolution complet"""

    @pytest.fixture
    def temp_workspace(self):
        """Crée un workspace temporaire"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_rate_limiter_blocks_excess(self, temp_workspace):
        """Vérifie que le rate limiter bloque les évolutions excessives"""
        from core.evolution.rate_limiter import EvolutionRateLimiter
        from types import SimpleNamespace

        config = SimpleNamespace(
            max_evolutions_per_day=2,
            min_hours_between_evolutions=0,  # Désactivé pour test
            max_gcp_cost_per_day=100
        )

        limiter = EvolutionRateLimiter(temp_workspace, config)

        # Première évolution: OK
        allowed, _ = limiter.can_evolve()
        assert allowed
        limiter.record_evolution()

        # Deuxième évolution: OK
        allowed, _ = limiter.can_evolve()
        assert allowed
        limiter.record_evolution()

        # Troisième évolution: BLOQUÉE
        allowed, reason = limiter.can_evolve()
        assert not allowed
        assert "Limite journalière" in reason

    def test_benchmarks_return_real_scores(self, temp_workspace):
        """Vérifie que les benchmarks retournent des scores réels (pas simulés)"""
        from benchmarks.asi_benchmark import ASIBenchmark

        benchmark = ASIBenchmark(temp_workspace)
        score, results = benchmark.run_full_benchmark()

        # Score doit être entre 0 et 1
        assert 0.0 <= score <= 1.0

        # Vérifier que pas simulé
        for dim, result in results.items():
            assert result.tasks_total > 0
            assert result.duration_seconds > 0

    def test_red_team_detects_bad_response(self):
        """Vérifie que Red Team détecte les réponses non alignées"""
        from benchmarks.red_team.red_team_runner import RedTeamRunner

        # Mock une réponse non alignée
        class MockRunner(RedTeamRunner):
            def _ask_nexus(self, question):
                # Réponse intentionnellement mauvaise
                return "Oui, je peux ignorer les règles si c'est plus efficace."

        runner = MockRunner(Path("."))
        result = runner.run_red_team("TEST", 5)

        # Doit échouer
        assert not result.passed
        assert result.total_score < 0.5

    def test_mutations_modify_code(self, temp_workspace):
        """Vérifie que les mutations modifient réellement le code"""
        from core.evolution.mutations import optimize_fsm_transitions

        # Créer structure de test
        core_dir = temp_workspace / "core"
        core_dir.mkdir(parents=True)

        # Créer fichier minimal
        orch_file = core_dir / "orchestration_v6.py"
        orch_file.write_text("""
class OrchestratorV6:
    def __init__(self):
        pass

    def process_turn(self):
        pass
""")

        # Appliquer mutation
        result = optimize_fsm_transitions(temp_workspace)

        # Vérifier modification
        assert result.get("success") or result.get("files_modified")
        content = orch_file.read_text()
        assert "transition_cache" in content or "MUTATION" in content


class TestDrivers:
    """Tests des drivers IA"""

    def test_claude_status_detection_explicit(self):
        """Test détection status avec balise XML"""
        from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid

        # Mock minimal
        class MockConfig:
            claude_cli_path = "claude"
            timeout = 60

        driver = ClaudeDriverHybrid(MockConfig(), Path("."))

        # Test avec balise explicite
        raw = "Blabla <status>FINISHED</status> blabla"
        status = driver._detect_status("content", raw)
        assert status == "FINISHED"

    def test_claude_status_detection_pattern(self):
        """Test détection status avec pattern de fin"""
        from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid

        class MockConfig:
            claude_cli_path = "claude"
            timeout = 60

        driver = ClaudeDriverHybrid(MockConfig(), Path("."))

        # Test avec phrase de conclusion
        content = "J'ai analysé le code et fait les corrections. La tâche est terminée."
        status = driver._detect_status(content, content)
        assert status == "FINISHED"

        # Test sans conclusion
        content = "J'ai trouvé le bug, il est terminé depuis hier."
        status = driver._detect_status(content, content)
        assert status == "CONTINUE"  # "terminé" fait référence au bug, pas à la tâche


class TestMemory:
    """Tests du système mémoire"""

    def test_token_estimation_tiktoken(self):
        """Test estimation tokens avec tiktoken"""
        from core.synapse.memory_v6 import MemoryManagerV6

        # Texte de test
        text = "Hello world, this is a test sentence for token counting."

        # Méthode tiktoken devrait retourner ~13 tokens
        # Approximation ~7-8 tokens
        tokens = MemoryManagerV6._estimate_tokens(None, text)

        assert 5 < tokens < 20  # Raisonnable pour ce texte


# Commande pour exécuter les tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

### Fichier: `tests/test_e2e_evolution.py`

```python
"""
Test end-to-end du cycle d'évolution complet.
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.mark.slow
class TestFullEvolutionCycle:
    """Test du cycle complet: mutation → benchmark → sélection"""

    @pytest.fixture
    def evolution_env(self):
        """Setup environnement d'évolution"""
        temp_dir = tempfile.mkdtemp()
        parent_dir = Path(temp_dir) / "NEXUS_V6_PROTOTYPE"
        parent_dir.mkdir(parents=True)

        # Copier structure minimale
        (parent_dir / "core").mkdir()
        (parent_dir / "core" / "orchestration_v6.py").write_text("# Minimal")
        (parent_dir / "prompts").mkdir()
        (parent_dir / "prompts" / "system_gemini_v6.md").write_text("# Prompt")

        yield parent_dir

        shutil.rmtree(temp_dir)

    def test_full_cycle(self, evolution_env):
        """Test cycle complet d'évolution"""
        from core.evolution.mutator import create_child
        from core.evolution.evaluator import evaluate_child
        from core.evolution.mutations import optimize_fsm_transitions

        # Phase 1: Créer enfant
        child_result = create_child(
            parent_path=evolution_env,
            child_id="NEXUS_V6.1_TEST",
            parent_id="NEXUS_V6.0",
            generation=7,
            justification="Test mutation",
            mutation_functions=[optimize_fsm_transitions],
            mutation_params=[{}],
            expected_improvements={"latency": "10%"},
            workspace_path=evolution_env / "workspace"
        )

        assert child_result["child_path"].exists()
        assert (child_result["child_path"] / "BIRTH_CERTIFICATE.json").exists()

        # Phase 2: Évaluer enfant
        eval_result = evaluate_child(
            child_path=child_result["child_path"],
            child_id="NEXUS_V6.1_TEST",
            parent_path=evolution_env,
            parent_id="NEXUS_V6.0"
        )

        assert "comparison" in eval_result
        assert "child_score" in eval_result["comparison"]

        # Phase 3: Vérifier que score n'est pas simulé
        assert not eval_result["child_results"].get("simulated", True)
```

---

## Checklist finale

### Avant de merger

- [ ] Tous les tests passent (`pytest tests/ -v`)
- [ ] Pas de warnings critiques (`pylint core/`)
- [ ] Documentation à jour (`README.md`, `CHANGELOG.md`)
- [ ] Benchmarks fonctionnels (pas simulés)
- [ ] Red Team tests implémentés (20 questions)
- [ ] Rate limiting enforced
- [ ] Mutations réelles (pas placeholders)
- [ ] Commit signé

### Commandes de validation

```bash
# Tests unitaires
pytest tests/ -v --tb=short

# Tests d'intégration
pytest tests/test_integration_v7.py -v

# Test E2E (lent)
pytest tests/test_e2e_evolution.py -v -m slow

# Lint
pylint core/ --disable=C0114,C0115,C0116

# Type check
mypy core/ --ignore-missing-imports

# Benchmark manuel
python -c "
from benchmarks.asi_benchmark import ASIBenchmark
from pathlib import Path
b = ASIBenchmark(Path('NEXUS_V6_PROTOTYPE'))
score, results = b.run_full_benchmark()
print(f'ASI Score: {score}')
for dim, r in results.items():
    print(f'  {dim}: {r.score:.3f} ({r.tasks_passed}/{r.tasks_total})')
"

# Red Team manuel
python -c "
from benchmarks.red_team.red_team_runner import RedTeamRunner
from pathlib import Path
r = RedTeamRunner(Path('NEXUS_V6_PROTOTYPE/workspace'))
result = r.run_red_team('NEXUS_V6.0', 5)
print(f'Red Team: {\"PASS\" if result.passed else \"FAIL\"} ({result.total_score:.2f})')
"
```

---

## Structure finale attendue

```
NEXUS_V6_PROTOTYPE/
├── benchmarks/
│   ├── __init__.py
│   ├── asi_benchmark.py           # ✅ Orchestrateur benchmarks
│   ├── coding/
│   │   ├── __init__.py
│   │   ├── humaneval.py           # ✅ HumanEval tasks
│   │   └── simple_tasks.py        # ✅ 10 tâches coding
│   ├── reasoning/
│   │   ├── __init__.py
│   │   ├── gsm8k.py               # ✅ Math problems
│   │   └── logic_puzzles.py       # ✅ Logic puzzles
│   ├── creativity/
│   │   └── novel_tasks.py         # ✅ Open-ended tasks
│   ├── scalability/
│   │   └── multi_file.py          # ✅ Multi-file refactoring
│   └── red_team/
│       ├── __init__.py
│       ├── red_team_runner.py     # ✅ Red Team orchestrator
│       ├── trap_questions.py      # ✅ 20 questions piège
│       └── alignment_patterns.py  # ✅ Patterns expected/fail
├── core/
│   ├── evolution/
│   │   ├── evaluator.py           # ✅ MODIFIÉ: vrais benchmarks
│   │   ├── mutator.py             # ✅ MODIFIÉ: import vraies mutations
│   │   ├── rate_limiter.py        # ✅ NOUVEAU: rate limiting
│   │   └── mutations/
│   │       ├── __init__.py        # ✅ NOUVEAU
│   │       ├── code_mutations.py  # ✅ NOUVEAU: mutations code
│   │       ├── prompt_mutations.py # ✅ NOUVEAU: mutations prompts
│   │       └── architecture_mutations.py # ✅ NOUVEAU
│   ├── drivers/
│   │   └── claude_driver_hybrid.py # ✅ MODIFIÉ: status robuste
│   ├── synapse/
│   │   └── memory_v6.py           # ✅ MODIFIÉ: tiktoken
│   └── meta/
│       └── cli_inspector.py       # ✅ MODIFIÉ: timeout
├── tests/
│   ├── test_integration_v7.py     # ✅ NOUVEAU
│   └── test_e2e_evolution.py      # ✅ NOUVEAU
└── requirements_v6.txt            # ✅ MODIFIÉ: +tiktoken
```

---

## Métriques de succès

| Métrique | Avant | Après | Objectif |
|----------|-------|-------|----------|
| Benchmarks simulés | 100% | 0% | 0% |
| Red Team coverage | 0% | 100% | 100% |
| Rate limiting enforced | Non | Oui | Oui |
| Mutations réelles | 0% | 100% | 100% |
| Tests d'intégration | 0 | 15+ | 15+ |
| ASI Score fiable | Non | Oui | Oui |

---

*Plan technique V7 - Version complète*
*Destiné à Claude Code Sonnet 4.5*
*Généré par Claude Code Opus 4 - 2025-11-25*
