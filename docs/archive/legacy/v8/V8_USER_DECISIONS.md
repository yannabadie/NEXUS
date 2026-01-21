# V8.0 TRUE HIVE MIND - Décisions Utilisateur

**Date**: 2025-12-08
**Décideur**: Yann Abadie (Architecte en Chef)

---

## Décisions Validées

### 1. Gating Complexity
**Question**: MODERATE → V7.9 ou V8.0?
**Décision**: **V8.0**
**Justification**: Maximiser l'utilisation de l'intelligence collaborative même pour les tâches modérées.

```python
COMPLEXITY_ROUTING = {
    TaskComplexity.TRIVIAL: "v7_fast_path",
    TaskComplexity.SIMPLE: "v7_fast_path",
    TaskComplexity.MODERATE: "v8_hive_mind",  # ← V8.0!
    TaskComplexity.COMPLEX: "v8_hive_mind",
    TaskComplexity.EXPERT: "v8_hive_mind"
}
```

### 2. User Intervention Points
**Question**: Auto-spawn ou confirmation?
**Décision**: **User Intervention Points (Breakpoints)**
**Justification**: L'utilisateur doit pouvoir intervenir aux moments critiques.

### 3. Debate Turns
**Question**: 4, 6, ou adaptatif?
**Décision**: **Adaptatif** (fonction complexité + erreurs)
**Justification**: Plus intelligent, économise tokens sur les cas simples, permet plus de débat sur les cas complexes.

```python
def get_max_debate_turns(complexity: TaskComplexity, error_count: int) -> int:
    """Calcule le nombre max de tours de débat adaptatif."""
    base_turns = {
        TaskComplexity.MODERATE: 3,
        TaskComplexity.COMPLEX: 5,
        TaskComplexity.EXPERT: 7
    }.get(complexity, 4)

    # Ajouter des tours si erreurs rencontrées (max +3)
    error_bonus = min(error_count, 3)

    return base_turns + error_bonus
```

### 4. Knowledge Consolidation (Phase 7)
**Question**: Agent TTL?
**Décision**: **Phase 7 - Débat post-tâche sur la connaissance**
**Justification**: Après une tâche, les agents débattent de ce qu'ils ont appris et décident quoi garder.

---

## Phase 7: Knowledge Consolidation (NOUVEAU)

### Concept

Après chaque tâche COMPLEX/EXPERT terminée (succès ou échec), Gemini et Claude débattent:
1. **Qu'avons-nous appris?** (patterns, erreurs, solutions)
2. **Que faut-il garder?** (agents, outils, knowledge)
3. **Comment améliorer NEXUS?** (suggestions d'évolution)

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 7: KNOWLEDGE CONSOLIDATION                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                                │
│  │ TASK DONE   │ (Succès ou Échec)                              │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ HIVE_REFLECTING                         │                    │
│  │ "Qu'avons-nous appris de cette tâche?"  │                    │
│  │                                         │                    │
│  │ Gemini: [Analyse des patterns]          │                    │
│  │ Claude: [Analyse des erreurs/succès]    │                    │
│  └──────┬──────────────────────────────────┘                    │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ HIVE_DECIDING_RETENTION                 │                    │
│  │ "Que garder de cette expérience?"       │                    │
│  │                                         │                    │
│  │ Options débattues:                      │                    │
│  │ - Garder agent spawné (permanent)       │                    │
│  │ - Archiver knowledge (sans agent)       │                    │
│  │ - Merger dans agent existant            │                    │
│  │ - Supprimer (one-shot task)             │                    │
│  └──────┬──────────────────────────────────┘                    │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ 🔴 BREAKPOINT: USER DECISION            │                    │
│  │                                         │                    │
│  │ "Gemini+Claude recommandent:            │                    │
│  │  [Garder PDF Expert - score: 0.87]"     │                    │
│  │                                         │                    │
│  │ [Accepter] [Modifier] [Ignorer]         │                    │
│  └──────┬──────────────────────────────────┘                    │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ HIVE_CONSOLIDATING                      │                    │
│  │ Applique la décision:                   │                    │
│  │ - Met à jour Agent Registry             │                    │
│  │ - Sauvegarde dans Success/Failure Memory│                    │
│  │ - Met à jour DyLAN metrics              │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Données Consolidées

```python
@dataclass
class KnowledgeConsolidation:
    """Résultat de la consolidation de connaissances."""

    # Ce qui a été appris
    learned_patterns: List[str]          # Patterns efficaces découverts
    learned_antipatterns: List[str]      # Ce qui ne marche pas
    new_capabilities_identified: List[str]  # Capacités à ajouter

    # Décisions sur les assets
    agents_to_keep: List[AgentRetention]
    knowledge_to_archive: List[KnowledgeEntry]
    tools_to_create: List[ToolSuggestion]

    # Suggestions d'amélioration
    nexus_improvements: List[str]        # Suggestions pour NEXUS lui-même

    # Métriques
    task_success: bool
    confidence_in_decisions: float


@dataclass
class AgentRetention:
    """Décision de rétention d'un agent."""
    agent_id: str
    decision: str  # "KEEP_PERMANENT", "ARCHIVE_KNOWLEDGE", "MERGE", "DELETE"
    reason: str
    gemini_vote: str
    claude_vote: str
    user_override: Optional[str] = None
```

### Prompt de Réflexion

```python
REFLECTION_PROMPT = """
PHASE DE RÉFLEXION POST-TÂCHE

Tâche: {task_description}
Résultat: {success_or_failure}
Durée: {duration}
Tokens utilisés: {tokens}

Architecture utilisée:
{architecture_summary}

Exécution:
{execution_log_summary}

---

QUESTIONS À ANALYSER:

1. PATTERNS APPRIS
   - Qu'est-ce qui a bien fonctionné?
   - Qu'est-ce qui a mal fonctionné?
   - Quels patterns pouvons-nous réutiliser?

2. AGENTS SPAWNED
   Pour chaque agent créé ({spawned_agents}):
   - Cet agent a-t-il été utile?
   - Devrait-il être gardé pour des tâches futures?
   - Sa configuration est-elle optimale?

3. CONNAISSANCES À ARCHIVER
   - Quelles informations du contexte sont réutilisables?
   - Y a-t-il des "recettes" à sauvegarder?

4. SUGGESTIONS D'AMÉLIORATION
   - Comment NEXUS pourrait-il mieux gérer ce type de tâche?
   - Manque-t-il des outils ou capacités?

Réponds en JSON structuré.
"""
```

---

## User Intervention Points (Breakpoints)

### Architecture des Breakpoints

```python
class UserBreakpoint(Enum):
    """Points où l'utilisateur peut intervenir."""

    # Phase 2: Après débat stratégique
    AFTER_DEBATE = "after_debate"

    # Phase 3: Avant spawn d'agent
    BEFORE_SPAWN = "before_spawn"

    # Phase 5: Après diagnostic d'échec
    AFTER_DIAGNOSIS = "after_diagnosis"

    # Phase 7: Consolidation de connaissances
    KNOWLEDGE_CONSOLIDATION = "knowledge_consolidation"


@dataclass
class BreakpointRequest:
    """Requête de breakpoint vers l'utilisateur."""
    breakpoint_type: UserBreakpoint
    context: str                      # Résumé du contexte
    recommendation: str               # Ce que les agents recommandent
    options: List[BreakpointOption]   # Options disponibles
    timeout_seconds: int = 60         # Auto-continue après timeout
    default_action: str = "accept"    # Action si timeout


@dataclass
class BreakpointOption:
    """Option présentée à l'utilisateur."""
    id: str
    label: str
    description: str
    is_recommended: bool = False


class UserInteractionHandler:
    """
    Gère les interactions utilisateur aux breakpoints.
    """

    def __init__(self, interaction_mode: str = "interactive"):
        """
        Args:
            interaction_mode:
                - "interactive": Attend réponse utilisateur (défaut)
                - "auto_accept": Accepte automatiquement les recommandations
                - "auto_reject": Rejette automatiquement (plus conservateur)
        """
        self.mode = interaction_mode
        self.pending_breakpoints: List[BreakpointRequest] = []

    async def request_user_decision(
        self,
        breakpoint: BreakpointRequest
    ) -> str:
        """
        Demande une décision à l'utilisateur.

        Returns:
            L'ID de l'option choisie
        """
        if self.mode == "auto_accept":
            return breakpoint.default_action

        if self.mode == "auto_reject":
            return "reject"

        # Mode interactif: afficher et attendre
        self._display_breakpoint(breakpoint)

        try:
            response = await asyncio.wait_for(
                self._wait_for_user_input(),
                timeout=breakpoint.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Auto-selecting: {breakpoint.default_action}")
            return breakpoint.default_action

    def _display_breakpoint(self, bp: BreakpointRequest):
        """Affiche le breakpoint à l'utilisateur."""
        print("\n" + "="*60)
        print(f"🔴 BREAKPOINT: {bp.breakpoint_type.value}")
        print("="*60)
        print(f"\n{bp.context}\n")
        print(f"💡 Recommandation: {bp.recommendation}\n")
        print("Options:")
        for i, opt in enumerate(bp.options, 1):
            marker = "→" if opt.is_recommended else " "
            print(f"  {marker} [{i}] {opt.label}: {opt.description}")
        print(f"\n(Timeout: {bp.timeout_seconds}s, défaut: {bp.default_action})")
        print("="*60)
```

### Exemples de Breakpoints

#### Breakpoint 1: Après Débat

```python
BreakpointRequest(
    breakpoint_type=UserBreakpoint.AFTER_DEBATE,
    context="""
    Tâche: Analyser et corriger les vulnérabilités de sécurité dans auth.py

    Débat (3 tours):
    - Gemini: Propose RED_BLUE (adversarial security review)
    - Claude: D'accord mais suggère d'ajouter un specialist
    - Consensus: RED_BLUE avec spawn d'un security_auditor
    """,
    recommendation="RED_BLUE mode avec spawn security_auditor",
    options=[
        BreakpointOption("accept", "Accepter", "Utiliser RED_BLUE + spawn", is_recommended=True),
        BreakpointOption("modify", "Modifier", "Changer le mode ou les agents"),
        BreakpointOption("cancel", "Annuler", "Ne pas exécuter cette tâche")
    ]
)
```

#### Breakpoint 2: Avant Spawn

```python
BreakpointRequest(
    breakpoint_type=UserBreakpoint.BEFORE_SPAWN,
    context="""
    Agent proposé: security_auditor

    Capabilities: vulnerability_scan, code_review, threat_modeling
    Coût estimé: ~500 tokens pour création

    Agents similaires existants:
    - code_reviewer (similarité: 45%) - Ne couvre pas security
    """,
    recommendation="Créer security_auditor (aucun agent similaire)",
    options=[
        BreakpointOption("create", "Créer", "Spawner le nouvel agent", is_recommended=True),
        BreakpointOption("use_existing", "Utiliser existant", "Essayer avec code_reviewer"),
        BreakpointOption("skip", "Ignorer", "Continuer sans specialist")
    ]
)
```

#### Breakpoint 3: Après Diagnostic

```python
BreakpointRequest(
    breakpoint_type=UserBreakpoint.AFTER_DIAGNOSIS,
    context="""
    Échec détecté: CAPABILITY_MISSING

    Diagnostic:
    - Root cause: Aucun agent ne sait parser les PDF scannés
    - Evidence: "Cannot extract text from image-based PDF"

    Stratégie actuelle blacklistée: direct_pdf_read
    """,
    recommendation="Spawner un ocr_specialist et réessayer",
    options=[
        BreakpointOption("retry_spawn", "Retry + Spawn", "Créer OCR expert et réessayer", is_recommended=True),
        BreakpointOption("retry_different", "Retry différent", "Essayer une autre approche"),
        BreakpointOption("abandon", "Abandonner", "Marquer comme échec")
    ]
)
```

#### Breakpoint 4: Consolidation

```python
BreakpointRequest(
    breakpoint_type=UserBreakpoint.KNOWLEDGE_CONSOLIDATION,
    context="""
    Tâche terminée: ✅ Succès

    Agents spawned pendant la tâche:
    - pdf_expert (utilisé 5 fois, succès: 100%)
    - ocr_specialist (utilisé 2 fois, succès: 100%)

    Débat de consolidation:
    - Gemini: Garder pdf_expert (très utile), archiver ocr_specialist
    - Claude: D'accord, mais suggère de merger ocr dans pdf_expert
    - Consensus: Garder pdf_expert enrichi avec OCR capabilities
    """,
    recommendation="Garder pdf_expert avec OCR capabilities intégrées",
    options=[
        BreakpointOption("keep_merged", "Garder (merged)", "pdf_expert avec OCR", is_recommended=True),
        BreakpointOption("keep_both", "Garder les deux", "Agents séparés"),
        BreakpointOption("archive", "Archiver", "Sauver knowledge, supprimer agents"),
        BreakpointOption("delete", "Supprimer", "One-shot, pas besoin de garder")
    ]
)
```

---

## Adaptive Debate Turns

```python
class AdaptiveDebateConfig:
    """Configuration adaptative des tours de débat."""

    # Base turns par complexité
    BASE_TURNS = {
        TaskComplexity.MODERATE: 3,
        TaskComplexity.COMPLEX: 5,
        TaskComplexity.EXPERT: 7
    }

    # Bonus/malus
    ERROR_BONUS_PER_ERROR = 1      # +1 tour par erreur précédente
    ERROR_BONUS_MAX = 3            # Maximum +3 tours pour erreurs
    STAGNATION_PENALTY = -1        # -1 tour si débat stagne
    HIGH_DISAGREEMENT_BONUS = 2    # +2 si forte divergence initiale

    @classmethod
    def calculate_max_turns(
        cls,
        complexity: TaskComplexity,
        previous_errors: int = 0,
        initial_disagreement: float = 0.0,  # 0-1
        stagnation_detected: bool = False
    ) -> int:
        """Calcule le nombre max de tours adaptatif."""

        base = cls.BASE_TURNS.get(complexity, 4)

        # Erreurs = plus de débat nécessaire
        error_bonus = min(previous_errors * cls.ERROR_BONUS_PER_ERROR, cls.ERROR_BONUS_MAX)

        # Forte divergence = plus de débat
        disagreement_bonus = cls.HIGH_DISAGREEMENT_BONUS if initial_disagreement > 0.7 else 0

        # Stagnation = moins de débat (futile)
        stagnation_penalty = cls.STAGNATION_PENALTY if stagnation_detected else 0

        total = base + error_bonus + disagreement_bonus + stagnation_penalty

        # Bornes: minimum 2, maximum 10
        return max(2, min(10, total))
```

---

## Architecture Finale V8.0 (Révisée)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRUE HIVE MIND V8.0 (FINAL)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TASK → Complexity Analysis → GATING                                        │
│                                │                                            │
│         ┌──────────────────────┼──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│    TRIVIAL/SIMPLE         MODERATE              COMPLEX/EXPERT              │
│         │                      │                      │                     │
│         ▼                      └──────────┬───────────┘                     │
│    V7.9 Fast Path                         ▼                                 │
│    (Done)                    V8.0 TRUE HIVE MIND                            │
│                                           │                                 │
│                              ┌────────────┴────────────┐                    │
│                              ▼                         │                    │
│                    Phase 1: Independent Analysis       │                    │
│                    (Gemini seul, puis Claude seul)     │                    │
│                              │                         │                    │
│                              ▼                         │                    │
│                    Phase 2: Strategic Debate           │                    │
│                    (Adaptatif: 3-10 tours)             │                    │
│                              │                         │                    │
│                    ══════════╪══════════               │                    │
│                    🔴 BREAKPOINT 1                     │                    │
│                    ══════════╪══════════               │                    │
│                              │                         │                    │
│                              ▼                         │                    │
│                    Phase 3: Architecture Generation    │                    │
│                    (Agent Registry check)              │                    │
│                              │                         │                    │
│                    ══════════╪══════════               │                    │
│                    🔴 BREAKPOINT 2 (si spawn)          │                    │
│                    ══════════╪══════════               │                    │
│                              │                         │                    │
│                              ▼                         │                    │
│                    Phase 4: Monitored Execution        │                    │
│                              │                         │                    │
│                     ┌────────┴────────┐                │                    │
│                     ▼                 ▼                │                    │
│                  SUCCESS           FAILURE             │                    │
│                     │                 │                │                    │
│                     │                 ▼                │                    │
│                     │       Phase 5: Failure Analysis  │                    │
│                     │                 │                │                    │
│                     │       ══════════╪══════════      │                    │
│                     │       🔴 BREAKPOINT 3            │                    │
│                     │       ══════════╪══════════      │                    │
│                     │                 │                │                    │
│                     │                 ▼                │                    │
│                     │       Phase 6: Adaptive Retry ───┘                    │
│                     │       (Loop back to Phase 3)                          │
│                     │                                                       │
│                     └──────────────────┐                                    │
│                                        ▼                                    │
│                           Phase 7: Knowledge Consolidation                  │
│                           (Débat: que garder?)                              │
│                                        │                                    │
│                           ══════════════╪══════════════                     │
│                           🔴 BREAKPOINT 4                                   │
│                           ══════════════╪══════════════                     │
│                                        │                                    │
│                                        ▼                                    │
│                                     DONE                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FSM States (Mise à jour)

```python
class HiveMindState(Enum):
    """États FSM V8.0 avec Phase 7."""

    # Gating
    HIVE_GATING = "hive_gating"

    # Phase 1
    HIVE_ANALYZING_GEMINI = "hive_analyzing_gemini"
    HIVE_ANALYZING_CLAUDE = "hive_analyzing_claude"
    HIVE_COMPARING_ANALYSES = "hive_comparing_analyses"

    # Phase 2
    HIVE_DEBATING = "hive_debating"
    HIVE_CHECKING_CONSENSUS = "hive_checking_consensus"
    HIVE_BREAKPOINT_DEBATE = "hive_breakpoint_debate"  # 🔴 BP1

    # Phase 3
    HIVE_ARCHITECTING = "hive_architecting"
    HIVE_CHECKING_REGISTRY = "hive_checking_registry"
    HIVE_BREAKPOINT_SPAWN = "hive_breakpoint_spawn"    # 🔴 BP2
    HIVE_SPAWNING = "hive_spawning"

    # Phase 4
    HIVE_EXECUTING = "hive_executing"
    HIVE_MONITORING = "hive_monitoring"

    # Phase 5
    HIVE_DIAGNOSING = "hive_diagnosing"
    HIVE_BREAKPOINT_DIAGNOSIS = "hive_breakpoint_diagnosis"  # 🔴 BP3

    # Phase 6
    HIVE_DECIDING_RETRY = "hive_deciding_retry"
    HIVE_APPLYING_CHANGES = "hive_applying_changes"

    # Phase 7 (NOUVEAU)
    HIVE_REFLECTING = "hive_reflecting"
    HIVE_DECIDING_RETENTION = "hive_deciding_retention"
    HIVE_BREAKPOINT_CONSOLIDATION = "hive_breakpoint_consolidation"  # 🔴 BP4
    HIVE_CONSOLIDATING = "hive_consolidating"

    # Terminaux
    HIVE_SUCCESS = "hive_success"
    HIVE_FAILED = "hive_failed"
    HIVE_ESCALATE = "hive_escalate"
```
