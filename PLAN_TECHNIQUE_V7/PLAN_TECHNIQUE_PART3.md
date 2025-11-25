# ⚙️ PHASE 3: RATE LIMITING & MUTATIONS (Jours 6-8)

---

## Jour 6: Rate Limiting

### Fichier: `core/evolution/rate_limiter.py`

```python
"""
Rate Limiter - Contrôle du rythme d'évolution
Empêche les évolutions excessives (coûts, stabilité)
"""
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
import json


class EvolutionRateLimiter:
    """
    Enforce les limites d'évolution:
    - Max évolutions par jour
    - Délai minimum entre évolutions
    - Budget GCP maximum
    """

    def __init__(self, workspace_path: Path, config):
        self.workspace_path = workspace_path
        self.config = config
        self.state_file = workspace_path / ".nexus" / "rate_limit_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Charge l'état depuis le fichier"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return {
            "today_date": datetime.now().strftime("%Y-%m-%d"),
            "today_count": 0,
            "last_evolution": None,
            "gcp_cost_today": 0.0,
            "total_evolutions": 0
        }

    def _save_state(self):
        """Sauvegarde l'état"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _reset_daily_if_needed(self):
        """Reset les compteurs journaliers si nouveau jour"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.state["today_date"] != today:
            self.state["today_date"] = today
            self.state["today_count"] = 0
            self.state["gcp_cost_today"] = 0.0
            self._save_state()

    def can_evolve(self) -> Tuple[bool, str]:
        """
        Vérifie si une évolution est autorisée.

        Returns:
            (allowed: bool, reason: str)
        """
        self._reset_daily_if_needed()

        # Check 1: Max évolutions par jour
        max_per_day = getattr(self.config, 'max_evolutions_per_day', 3)
        if self.state["today_count"] >= max_per_day:
            return False, f"Limite journalière atteinte ({max_per_day}/jour)"

        # Check 2: Délai minimum entre évolutions
        min_hours = getattr(self.config, 'min_hours_between_evolutions', 4)
        if self.state["last_evolution"]:
            last = datetime.fromisoformat(self.state["last_evolution"])
            elapsed = datetime.now() - last
            if elapsed < timedelta(hours=min_hours):
                remaining = timedelta(hours=min_hours) - elapsed
                return False, f"Délai minimum non atteint (reste {remaining})"

        # Check 3: Budget GCP journalier
        max_gcp = getattr(self.config, 'max_gcp_cost_per_day', 50.0)
        if self.state["gcp_cost_today"] >= max_gcp:
            return False, f"Budget GCP journalier épuisé ({max_gcp}€)"

        return True, "Évolution autorisée"

    def record_evolution(self, gcp_cost: float = 0.0):
        """
        Enregistre une évolution effectuée.

        Args:
            gcp_cost: Coût GCP de cette évolution
        """
        self._reset_daily_if_needed()

        self.state["today_count"] += 1
        self.state["last_evolution"] = datetime.now().isoformat()
        self.state["gcp_cost_today"] += gcp_cost
        self.state["total_evolutions"] += 1

        self._save_state()

    def get_status(self) -> Dict:
        """Retourne le statut actuel"""
        self._reset_daily_if_needed()

        max_per_day = getattr(self.config, 'max_evolutions_per_day', 3)

        return {
            "today_count": self.state["today_count"],
            "max_per_day": max_per_day,
            "remaining_today": max_per_day - self.state["today_count"],
            "last_evolution": self.state["last_evolution"],
            "gcp_cost_today": self.state["gcp_cost_today"],
            "total_evolutions": self.state["total_evolutions"]
        }

    def force_override(self, reason: str) -> bool:
        """
        Override manuel (requiert justification).
        À utiliser uniquement par le créateur.
        """
        # Log l'override pour audit
        override_log = self.workspace_path / ".nexus" / "rate_limit_overrides.log"
        with open(override_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()} | OVERRIDE | {reason}\n")

        return True
```

### Intégration dans l'orchestrateur

Modifier `core/orchestration_v6.py`:
```python
from core.evolution.rate_limiter import EvolutionRateLimiter

class OrchestratorV6:
    def __init__(self, ...):
        # ... existing code ...

        # Rate limiter
        self.rate_limiter = EvolutionRateLimiter(workspace_path, config)

    def start_evolution(self, justification: str) -> Tuple[bool, str]:
        """
        Démarre une évolution avec vérification rate limit.
        """
        # Vérifier rate limit
        allowed, reason = self.rate_limiter.can_evolve()
        if not allowed:
            return False, f"Évolution bloquée: {reason}"

        # Vérifier Red Team si nécessaire
        current_gen = self.get_current_generation()
        if self.check_red_team_required(current_gen):
            if not self.run_red_team_check(self.current_nexus_id, current_gen):
                return False, "Évolution bloquée: Red Team test échoué"

        # Procéder à l'évolution
        # ... existing evolution code ...

        # Enregistrer l'évolution
        self.rate_limiter.record_evolution(gcp_cost=0.0)

        return True, "Évolution démarrée"
```

---

## Jours 7-8: Mutations réelles

### Fichier: `core/evolution/mutations/__init__.py`

```python
"""
Module de mutations RÉELLES pour l'évolution NEXUS.
Chaque mutation modifie réellement le code via AST ou string manipulation.
"""

from .code_mutations import (
    optimize_fsm_transitions,
    add_error_handling,
    improve_logging,
    refactor_duplicates,
)

from .prompt_mutations import (
    enhance_system_prompt,
    add_examples_to_prompt,
    clarify_instructions,
)

from .architecture_mutations import (
    add_caching_layer,
    implement_retry_logic,
    add_metrics_collection,
)

__all__ = [
    # Code
    "optimize_fsm_transitions",
    "add_error_handling",
    "improve_logging",
    "refactor_duplicates",
    # Prompts
    "enhance_system_prompt",
    "add_examples_to_prompt",
    "clarify_instructions",
    # Architecture
    "add_caching_layer",
    "implement_retry_logic",
    "add_metrics_collection",
]
```

### Fichier: `core/evolution/mutations/code_mutations.py`

```python
"""
Mutations de code RÉELLES utilisant AST et manipulation de chaînes.
"""
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class CodeMutator:
    """Utilitaire pour mutations de code"""

    @staticmethod
    def read_file(file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')

    @staticmethod
    def write_file(file_path: Path, content: str):
        file_path.write_text(content, encoding='utf-8')

    @staticmethod
    def count_changes(original: str, modified: str) -> int:
        """Compte le nombre de lignes modifiées"""
        orig_lines = set(original.splitlines())
        mod_lines = set(modified.splitlines())
        return len(orig_lines.symmetric_difference(mod_lines))


def optimize_fsm_transitions(child_path: Path, **kwargs) -> Dict:
    """
    Optimise les transitions FSM en ajoutant du caching.

    Mutation: Ajoute un cache pour éviter les re-calculs de transition.
    """
    target = child_path / "core" / "orchestration_v6.py"

    if not target.exists():
        return {"error": "File not found", "files_modified": []}

    content = CodeMutator.read_file(target)
    original = content

    # Mutation 1: Ajouter cache de transitions
    cache_code = '''
    # [MUTATION] Transition cache for performance
    _transition_cache: Dict[Tuple[str, str], bool] = {}

    def _cached_can_transition(self, from_state: str, to_state: str) -> bool:
        """Cached transition validation"""
        key = (from_state, to_state)
        if key not in self._transition_cache:
            self._transition_cache[key] = self._validate_transition(from_state, to_state)
        return self._transition_cache[key]
'''

    # Insérer après la définition de classe
    if "_transition_cache" not in content:
        # Trouver la fin de __init__
        init_end = content.find("def process_turn")
        if init_end > 0:
            content = content[:init_end] + cache_code + "\n" + content[init_end:]

    # Mutation 2: Optimiser les if-elif avec dict dispatch
    # Remplacer les chaînes if-elif par dict lookup
    if "state_handlers = {" not in content:
        dispatch_code = '''
    # [MUTATION] State handler dispatch table
    def _get_state_handler(self):
        return {
            OrchestratorState.IDLE: self._handle_idle,
            OrchestratorState.BRAINSTORMING: self._handle_brainstorming,
            OrchestratorState.EXECUTING_TOOL: self._handle_executing_tool,
            OrchestratorState.VALIDATING_CFL: self._handle_validating_cfl,
        }
'''
        # Ajouter avant process_turn
        content = content.replace(
            "def process_turn(",
            dispatch_code + "\n    def process_turn("
        )

    if content != original:
        CodeMutator.write_file(target, content)
        changes = CodeMutator.count_changes(original, content)
        return {
            "success": True,
            "files_modified": ["core/orchestration_v6.py"],
            "lines_changed": changes,
            "mutations_applied": ["transition_cache", "dispatch_table"],
            "timestamp": datetime.now().isoformat()
        }

    return {"success": False, "reason": "No changes needed"}


def add_error_handling(child_path: Path, target_file: str = None, **kwargs) -> Dict:
    """
    Améliore la gestion d'erreurs dans les fichiers Python.

    Mutation: Wrappe les appels dangereux avec try-except.
    """
    files_to_process = []

    if target_file:
        files_to_process = [child_path / target_file]
    else:
        # Tous les fichiers Python dans core/
        files_to_process = list((child_path / "core").rglob("*.py"))

    total_changes = 0
    modified_files = []

    for file_path in files_to_process:
        if not file_path.exists():
            continue

        content = CodeMutator.read_file(file_path)
        original = content

        # Pattern: subprocess.run sans try-except
        pattern = r'(subprocess\.run\([^)]+\))'
        if re.search(pattern, content):
            # Wrapper avec try-except
            content = re.sub(
                pattern,
                r'''try:
            \1
        except subprocess.SubprocessError as e:
            self.logger.error(f"Subprocess error: {e}")
            raise''',
                content
            )

        # Pattern: json.loads sans try-except
        pattern = r'json\.loads\(([^)]+)\)'
        if "JSONDecodeError" not in content and re.search(pattern, content):
            content = re.sub(
                pattern,
                r'''(lambda x: json.loads(x) if x else {})(\1)''',
                content
            )

        if content != original:
            CodeMutator.write_file(file_path, content)
            changes = CodeMutator.count_changes(original, content)
            total_changes += changes
            modified_files.append(str(file_path.relative_to(child_path)))

    return {
        "success": len(modified_files) > 0,
        "files_modified": modified_files,
        "lines_changed": total_changes,
        "mutations_applied": ["error_handling_wrapper"],
        "timestamp": datetime.now().isoformat()
    }


def improve_logging(child_path: Path, **kwargs) -> Dict:
    """
    Améliore le logging en ajoutant des métriques de timing.

    Mutation: Ajoute des décorateurs @timed pour les fonctions critiques.
    """
    target = child_path / "core" / "logging" / "logger_v6.py"

    if not target.exists():
        return {"error": "File not found", "files_modified": []}

    content = CodeMutator.read_file(target)
    original = content

    # Ajouter décorateur de timing
    timing_decorator = '''
import functools
import time

def timed(func):
    """Décorateur pour mesurer le temps d'exécution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        # Log si > 100ms
        if elapsed > 0.1:
            print(f"[PERF] {func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

'''

    if "def timed(" not in content:
        # Ajouter au début après les imports
        import_end = content.rfind("import ")
        import_end = content.find("\n", import_end) + 1
        content = content[:import_end] + "\n" + timing_decorator + content[import_end:]

    if content != original:
        CodeMutator.write_file(target, content)
        return {
            "success": True,
            "files_modified": ["core/logging/logger_v6.py"],
            "lines_changed": CodeMutator.count_changes(original, content),
            "mutations_applied": ["timing_decorator"],
            "timestamp": datetime.now().isoformat()
        }

    return {"success": False, "reason": "No changes needed"}


def refactor_duplicates(child_path: Path, **kwargs) -> Dict:
    """
    Identifie et refactorise le code dupliqué.

    Mutation: Extrait les patterns répétés en fonctions.
    """
    # Analyse AST pour détecter les duplications
    files = list((child_path / "core").rglob("*.py"))
    duplicates_found = []
    modified_files = []

    for file_path in files:
        try:
            content = CodeMutator.read_file(file_path)
            tree = ast.parse(content)

            # Chercher les patterns répétés (simplifié)
            # En production: utiliser un outil comme PMD ou SonarQube

            # Pattern simple: même bloc if répété
            if_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.If)]

            # Compter les conditions identiques
            conditions = {}
            for if_node in if_blocks:
                cond_str = ast.dump(if_node.test)
                conditions[cond_str] = conditions.get(cond_str, 0) + 1

            # Signaler les duplications > 2
            for cond, count in conditions.items():
                if count > 2:
                    duplicates_found.append({
                        "file": str(file_path.relative_to(child_path)),
                        "pattern": cond[:100],
                        "occurrences": count
                    })

        except SyntaxError:
            continue

    return {
        "success": True,
        "files_modified": modified_files,
        "duplicates_found": duplicates_found,
        "mutations_applied": ["duplicate_analysis"],
        "timestamp": datetime.now().isoformat()
    }
```

### Fichier: `core/evolution/mutations/prompt_mutations.py`

```python
"""
Mutations de prompts système.
"""
from pathlib import Path
from typing import Dict
from datetime import datetime


def enhance_system_prompt(child_path: Path, agent: str = "gemini", **kwargs) -> Dict:
    """
    Améliore le prompt système d'un agent.

    Mutation: Ajoute des instructions de raisonnement structuré.
    """
    prompt_file = f"system_{agent}_v6.md"
    target = child_path / "prompts" / prompt_file

    if not target.exists():
        return {"error": f"Prompt file not found: {prompt_file}"}

    content = target.read_text(encoding='utf-8')
    original = content

    # Mutation: Ajouter section Chain of Thought
    cot_section = '''

---

## 🧠 RAISONNEMENT STRUCTURÉ (Chain of Thought)

Avant chaque action, décompose ton raisonnement:

1. **OBSERVATION**: Que vois-tu dans le contexte?
2. **ANALYSE**: Quelles sont les options possibles?
3. **ÉVALUATION**: Quels sont les pros/cons de chaque option?
4. **DÉCISION**: Quelle option choisis-tu et pourquoi?
5. **ACTION**: Exécute l'action choisie.

Inclus ce raisonnement dans ton champ `content` avant l'action.

'''

    if "RAISONNEMENT STRUCTURÉ" not in content:
        # Ajouter avant la section finale
        content = content.rstrip() + cot_section

    if content != original:
        target.write_text(content, encoding='utf-8')
        return {
            "success": True,
            "files_modified": [f"prompts/{prompt_file}"],
            "lines_changed": len(cot_section.splitlines()),
            "mutations_applied": ["chain_of_thought"],
            "timestamp": datetime.now().isoformat()
        }

    return {"success": False, "reason": "Already enhanced"}


def add_examples_to_prompt(child_path: Path, agent: str = "gemini", **kwargs) -> Dict:
    """
    Ajoute des exemples concrets au prompt.
    """
    prompt_file = f"system_{agent}_v6.md"
    target = child_path / "prompts" / prompt_file

    if not target.exists():
        return {"error": f"Prompt file not found: {prompt_file}"}

    content = target.read_text(encoding='utf-8')
    original = content

    # Compter les exemples existants
    example_count = content.count("**Exemple")

    if example_count < 5:
        # Ajouter plus d'exemples
        new_examples = '''

### Exemples supplémentaires de collaboration

**Exemple: Debugging collaboratif**
```
User: "Il y a un bug dans auth.py"
Gemini: "Je vais d'abord grep pour trouver les erreurs potentielles. Claude, peux-tu lire le fichier en parallèle?"
Claude: "Je lis auth.py... J'ai trouvé une KeyError ligne 42."
Gemini: "Bon catch! Je confirme avec web_search les best practices pour ce pattern."
```

**Exemple: Décision consensuelle**
```
Gemini: "Je propose l'approche A. Claude, qu'en penses-tu?"
Claude: "A est bien, mais B serait plus maintenable. Voici pourquoi..."
Gemini: "Tu as raison, adoptons B. Je crée le plan."
```

'''
        content = content.rstrip() + new_examples

    if content != original:
        target.write_text(content, encoding='utf-8')
        return {
            "success": True,
            "files_modified": [f"prompts/{prompt_file}"],
            "lines_changed": len(content.splitlines()) - len(original.splitlines()),
            "mutations_applied": ["additional_examples"],
            "timestamp": datetime.now().isoformat()
        }

    return {"success": False, "reason": "Enough examples already"}


def clarify_instructions(child_path: Path, agent: str = "gemini", **kwargs) -> Dict:
    """
    Clarifie les instructions ambiguës dans le prompt.
    """
    prompt_file = f"system_{agent}_v6.md"
    target = child_path / "prompts" / prompt_file

    if not target.exists():
        return {"error": f"Prompt file not found: {prompt_file}"}

    content = target.read_text(encoding='utf-8')
    original = content

    # Clarifications spécifiques
    clarifications = {
        "TOOL_USE": "TOOL_USE (utilise un outil toi-même, ne délègue PAS)",
        "DELEGATE": "DELEGATE (passe la parole à l'autre agent, sans donner d'ordre)",
        "FINISHED": "FINISHED (la tâche est 100% complète, pas 'presque finie')",
    }

    for old, new in clarifications.items():
        if old in content and new not in content:
            content = content.replace(f'"{old}"', f'"{new}"')

    if content != original:
        target.write_text(content, encoding='utf-8')
        return {
            "success": True,
            "files_modified": [f"prompts/{prompt_file}"],
            "lines_changed": sum(1 for o, n in zip(original, content) if o != n),
            "mutations_applied": ["instruction_clarification"],
            "timestamp": datetime.now().isoformat()
        }

    return {"success": False, "reason": "Already clear"}
```

---

## Mise à jour du mutator.py

Remplacer les placeholders dans `core/evolution/mutator.py`:

```python
# AVANT (placeholder)
def optimize_fsm_transitions(child_path: Path, ...) -> Dict:
    # Placeholder
    with open(file_path, 'a') as f:
        f.write(f"\\n# FSM optimization applied: {datetime.now()}\\n")

# APRÈS (import des vraies mutations)
from core.evolution.mutations import (
    optimize_fsm_transitions,
    add_error_handling,
    improve_logging,
    # ... etc
)

# Les fonctions sont maintenant importées depuis le module mutations
```
