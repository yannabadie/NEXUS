# V8.0 TRUE HIVE MIND - Analyse d'Impact

## Sources de l'Analyse
- Proposition initiale Claude (TRUE_HIVE_MIND_V8.md)
- Critique Gemini (3 angles morts)
- Auto-critique Claude (7 angles morts additionnels)

---

## 1. ANALYSE DES RISQUES

### Risques Critiques (MUST FIX)

| ID | Risque | Probabilité | Impact | Mitigation |
|----|--------|-------------|--------|------------|
| R1 | **FSM Cassée** - While loop remplace FSM | 100% | CRITIQUE | Étendre FSM, pas remplacer |
| R2 | **Token Explosion** - Débat + context accumulation | 90% | HAUT | Complexity gating + sliding window |
| R3 | **Spawn Duplicates** - Agents identiques créés | 70% | MOYEN | Agent Registry + similarity check |
| R4 | **Budget Incontrôlé** - Auto-spawn sans limite | 60% | HAUT | Cost estimator + hard cap |

### Risques Modérés (SHOULD FIX)

| ID | Risque | Probabilité | Impact | Mitigation |
|----|--------|-------------|--------|------------|
| R5 | **Deadlock Débat** - Agents ne convergent jamais | 30% | MOYEN | Timeout + forced vote |
| R6 | **Diagnostic Biaisé** - Même agent analyse son échec | 50% | MOYEN | Cross-agent diagnosis |
| R7 | **Retry Circulaire** - Re-essaie stratégie échouée | 40% | MOYEN | Strategy blacklist |

### Risques Faibles (CAN FIX LATER)

| ID | Risque | Probabilité | Impact | Mitigation |
|----|--------|-------------|--------|------------|
| R8 | **Race Condition** - Spawn parallèle | 20% | FAIBLE | Mutex (si multi-thread) |
| R9 | **Agent Orphelins** - Pollution workspace | 30% | FAIBLE | TTL + GC |

---

## 2. IMPACT SUR L'ARCHITECTURE EXISTANTE

### Fichiers Impactés

```
core/
├── fsm/
│   ├── states.py           [MODIFIER] Ajouter nouveaux états HiveMind
│   └── transitions.py      [MODIFIER] Ajouter transitions HiveMind
├── orchestration_v7.py     [MODIFIER] Intégrer HiveMind routing
├── swarm/
│   ├── hybrid_swarm_engine.py  [MODIFIER] Ajouter complexity gating
│   └── task_analyzer.py        [OK] Déjà compatible
└── hive_mind/              [NOUVEAU] Module complet
    ├── __init__.py
    ├── fsm_states.py           # Nouveaux états FSM
    ├── independent_analysis.py # Phase 1
    ├── strategic_debate.py     # Phase 2
    ├── architecture_generator.py # Phase 3
    ├── monitored_execution.py  # Phase 4
    ├── failure_analyzer.py     # Phase 5
    ├── adaptive_retry.py       # Phase 6
    ├── agent_registry.py       # Anti-duplication
    ├── cost_estimator.py       # Budget control
    └── context_manager.py      # Sliding window
```

### Compatibilité Descendante

| Composant | Impact | Rétro-compatible? |
|-----------|--------|-------------------|
| V7.9 Swarm | Fast path préservé | ✅ OUI |
| FSM existante | Étendue, pas remplacée | ✅ OUI |
| Mode Executors | Réutilisés | ✅ OUI |
| Task Analyzer | Inchangé | ✅ OUI |
| Agent Pool | Étendu avec Registry | ✅ OUI |
| Commands (/swarm, /spawn) | Préservées | ✅ OUI |

---

## 3. ARCHITECTURE CORRIGÉE

### Flow Décisionnel avec Gating

```
                           ┌─────────────────┐
                           │   TASK INPUT    │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  TaskAnalyzer   │
                           │  (Complexity)   │
                           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼───────┐ ┌─────▼─────┐ ┌──────▼──────┐
            │   TRIVIAL/    │ │ MODERATE  │ │  COMPLEX/   │
            │    SIMPLE     │ │           │ │   EXPERT    │
            └───────┬───────┘ └─────┬─────┘ └──────┬──────┘
                    │               │               │
            ┌───────▼───────┐ ┌─────▼─────┐ ┌──────▼──────┐
            │  V7.9 FAST    │ │  V7.9     │ │  V8.0 TRUE  │
            │    PATH       │ │  SWARM    │ │  HIVE MIND  │
            │ (Single Agent)│ │ (6 Modes) │ │  (6 Phases) │
            └───────────────┘ └───────────┘ └─────────────┘
```

### FSM États V8.0

```python
class HiveMindState(Enum):
    """Nouveaux états FSM pour True Hive Mind."""

    # Gating (décide quel circuit utiliser)
    HIVE_GATING = "hive_gating"

    # Phase 1: Analyse Indépendante
    HIVE_ANALYZING_GEMINI = "hive_analyzing_gemini"
    HIVE_ANALYZING_CLAUDE = "hive_analyzing_claude"
    HIVE_COMPARING_ANALYSES = "hive_comparing_analyses"

    # Phase 2: Débat Stratégique
    HIVE_DEBATING = "hive_debating"
    HIVE_CHECKING_CONSENSUS = "hive_checking_consensus"

    # Phase 3: Architecture
    HIVE_ARCHITECTING = "hive_architecting"
    HIVE_CHECKING_REGISTRY = "hive_checking_registry"
    HIVE_SPAWNING = "hive_spawning"

    # Phase 4: Exécution
    HIVE_EXECUTING = "hive_executing"
    HIVE_MONITORING = "hive_monitoring"

    # Phase 5: Diagnostic
    HIVE_DIAGNOSING = "hive_diagnosing"

    # Phase 6: Retry
    HIVE_DECIDING_RETRY = "hive_deciding_retry"
    HIVE_APPLYING_CHANGES = "hive_applying_changes"

    # Terminaux
    HIVE_SUCCESS = "hive_success"
    HIVE_FAILED = "hive_failed"
    HIVE_ESCALATE = "hive_escalate"
```

### Transitions FSM

```python
HIVE_MIND_TRANSITIONS = {
    # Gating
    HiveMindState.HIVE_GATING: {
        "trivial": SwarmPhase.IDLE,  # Back to V7.9
        "moderate": SwarmPhase.SWARM_ANALYZING,  # V7.9 Swarm
        "complex": HiveMindState.HIVE_ANALYZING_GEMINI  # V8.0
    },

    # Phase 1
    HiveMindState.HIVE_ANALYZING_GEMINI: {
        "done": HiveMindState.HIVE_ANALYZING_CLAUDE
    },
    HiveMindState.HIVE_ANALYZING_CLAUDE: {
        "done": HiveMindState.HIVE_COMPARING_ANALYSES
    },
    HiveMindState.HIVE_COMPARING_ANALYSES: {
        "consensus": HiveMindState.HIVE_ARCHITECTING,
        "disagreement": HiveMindState.HIVE_DEBATING
    },

    # Phase 2
    HiveMindState.HIVE_DEBATING: {
        "turn_complete": HiveMindState.HIVE_CHECKING_CONSENSUS
    },
    HiveMindState.HIVE_CHECKING_CONSENSUS: {
        "consensus": HiveMindState.HIVE_ARCHITECTING,
        "continue": HiveMindState.HIVE_DEBATING,
        "timeout": HiveMindState.HIVE_ARCHITECTING  # Force decision
    },

    # Phase 3
    HiveMindState.HIVE_ARCHITECTING: {
        "need_spawn": HiveMindState.HIVE_CHECKING_REGISTRY,
        "ready": HiveMindState.HIVE_EXECUTING
    },
    HiveMindState.HIVE_CHECKING_REGISTRY: {
        "found_similar": HiveMindState.HIVE_EXECUTING,
        "need_new": HiveMindState.HIVE_SPAWNING
    },
    HiveMindState.HIVE_SPAWNING: {
        "done": HiveMindState.HIVE_EXECUTING,
        "budget_exceeded": HiveMindState.HIVE_ESCALATE
    },

    # Phase 4
    HiveMindState.HIVE_EXECUTING: {
        "step_done": HiveMindState.HIVE_MONITORING
    },
    HiveMindState.HIVE_MONITORING: {
        "continue": HiveMindState.HIVE_EXECUTING,
        "success": HiveMindState.HIVE_SUCCESS,
        "failure": HiveMindState.HIVE_DIAGNOSING
    },

    # Phase 5
    HiveMindState.HIVE_DIAGNOSING: {
        "done": HiveMindState.HIVE_DECIDING_RETRY
    },

    # Phase 6
    HiveMindState.HIVE_DECIDING_RETRY: {
        "retry": HiveMindState.HIVE_APPLYING_CHANGES,
        "stop": HiveMindState.HIVE_FAILED,
        "escalate": HiveMindState.HIVE_ESCALATE
    },
    HiveMindState.HIVE_APPLYING_CHANGES: {
        "done": HiveMindState.HIVE_ARCHITECTING  # Loop back
    }
}
```

---

## 4. COMPOSANTS CRITIQUES À AJOUTER

### 4.1 Agent Registry (Anti-Duplication)

```python
class AgentRegistry:
    """
    Registre d'agents avec détection de similarité.
    Évite la création de duplicates.
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.agents_dir = workspace_path / "agents"
        self._lock = threading.Lock()  # Anti race-condition

    def find_similar(
        self,
        required_capabilities: List[str],
        threshold: float = 0.8
    ) -> Optional[AgentProfile]:
        """
        Cherche un agent existant avec capabilities similaires.
        Utilise le RAG DenseBackend pour similarity search.
        """
        with self._lock:
            existing_agents = self._load_all_agents()

            for agent in existing_agents:
                similarity = self._compute_similarity(
                    required_capabilities,
                    agent.capabilities
                )
                if similarity >= threshold:
                    return agent

            return None

    def register_spawn(self, agent: AgentProfile) -> bool:
        """
        Enregistre un nouvel agent avec dédoublonnage.
        Retourne False si un agent similaire existe déjà.
        """
        with self._lock:
            existing = self.find_similar(agent.capabilities)
            if existing:
                return False  # Duplicate detected

            # Créer l'agent
            self._create_agent_directory(agent)
            return True
```

### 4.2 Cost Estimator

```python
class CostEstimator:
    """
    Estime le coût avant chaque décision coûteuse.
    """

    # Coûts approximatifs par opération (en tokens)
    COSTS = {
        "independent_analysis": 2000,    # 2 agents × 1000 tokens
        "debate_turn": 1500,             # 1 agent × 1500 tokens
        "spawn_agent": 500,              # Création + prompt
        "execution_step": 1000,          # Variable
        "failure_diagnosis": 2000        # 2 agents
    }

    def __init__(self, budget_limit: int = 50000):
        self.budget_limit = budget_limit
        self.spent = 0

    def can_afford(self, operation: str, count: int = 1) -> bool:
        """Vérifie si on peut se permettre l'opération."""
        cost = self.COSTS.get(operation, 1000) * count
        return (self.spent + cost) <= self.budget_limit

    def estimate_full_hive_mind(
        self,
        estimated_debate_turns: int = 4,
        estimated_spawns: int = 1,
        estimated_execution_steps: int = 5
    ) -> int:
        """Estime le coût total d'un full HiveMind run."""
        return (
            self.COSTS["independent_analysis"] +
            self.COSTS["debate_turn"] * estimated_debate_turns +
            self.COSTS["spawn_agent"] * estimated_spawns +
            self.COSTS["execution_step"] * estimated_execution_steps
        )
```

### 4.3 Context Manager (Sliding Window)

```python
class HiveMindContextManager:
    """
    Gère le contexte avec sliding window pour éviter token explosion.
    """

    def __init__(self, max_tokens: int = 30000):
        self.max_tokens = max_tokens
        self.debate_history = []
        self.execution_log = []

    def add_debate_turn(self, turn: DebateTurn):
        """Ajoute un tour de débat avec compression si nécessaire."""
        self.debate_history.append(turn)
        self._compress_if_needed()

    def _compress_if_needed(self):
        """Compresse l'historique si trop long."""
        current_tokens = self._estimate_tokens()

        if current_tokens > self.max_tokens:
            # Stratégie: Garder début + fin, résumer le milieu
            if len(self.debate_history) > 4:
                middle = self.debate_history[2:-2]
                summary = self._summarize_turns(middle)
                self.debate_history = (
                    self.debate_history[:2] +
                    [DebateTurn(agent="SYSTEM", content=f"[RÉSUMÉ: {summary}]")] +
                    self.debate_history[-2:]
                )

    def get_context_for_agent(self, agent_id: str) -> str:
        """Retourne le contexte formaté pour un agent."""
        # Inclure: Task + analyses + débat récent (pas tout)
        return self._format_context(
            include_full_analyses=True,
            debate_last_n=4,  # Seulement les 4 derniers tours
            include_summary=True
        )
```

### 4.4 Strategy Blacklist (Anti-Retry Circulaire)

```python
class StrategyBlacklist:
    """
    Empêche de réessayer les mêmes stratégies qui ont échoué.
    """

    def __init__(self):
        self.blacklist: Dict[str, List[str]] = {}  # task_hash -> [strategies]

    def is_blacklisted(self, task_hash: str, strategy: str) -> bool:
        """Vérifie si cette stratégie est blacklistée pour cette tâche."""
        return strategy in self.blacklist.get(task_hash, [])

    def blacklist_strategy(self, task_hash: str, strategy: str, reason: str):
        """Ajoute une stratégie à la blacklist."""
        if task_hash not in self.blacklist:
            self.blacklist[task_hash] = []

        self.blacklist[task_hash].append(strategy)

        # Log pour apprentissage futur
        self._log_failure_pattern(task_hash, strategy, reason)

    def get_available_strategies(
        self,
        task_hash: str,
        all_strategies: List[str]
    ) -> List[str]:
        """Retourne les stratégies non-blacklistées."""
        blacklisted = self.blacklist.get(task_hash, [])
        return [s for s in all_strategies if s not in blacklisted]
```

---

## 5. PLAN D'IMPLÉMENTATION RÉVISÉ

### Phase 0: Infrastructure (Pré-requis) ✅ COMPLETE
- [x] Agent Registry (`core/hive_mind/agent_registry.py`)
- [x] Cost Estimator (`core/hive_mind/cost_estimator.py`)
- [x] Context Manager (`core/hive_mind/context_manager.py`)
- [x] Strategy Blacklist (`core/hive_mind/strategy_blacklist.py`)
- [x] FSM States Extension (`core/hive_mind/types.py`)
- [x] Adaptive Debate Config (`core/hive_mind/adaptive_debate.py`)
- [x] User Interaction Handler (`core/hive_mind/user_interaction.py`)

### Phase 1: Gating + Fast Path ✅ COMPLETE
- [x] Complexity gating dans `core/orchestration/fsm_handlers.py`
- [x] Route TRIVIAL/SIMPLE vers V7.9 (preserved)
- [x] Route COMPLEX/EXPERT vers V8.0 Hive Mind
- [x] Route MODERATE configurable (`hive_mind_moderate` setting)

### Phase 2: Independent Analysis ✅ COMPLETE
- [x] `IndependentAnalysisPhase` (`core/hive_mind/phases/phase_analysis.py`)
- [x] Parallel Gemini/Claude analysis
- [x] Analysis comparison with disagreement detection
- [x] Agreement score threshold (85% to skip debate)

### Phase 3: Strategic Debate ✅ COMPLETE
- [x] `StrategicDebatePhase` (`core/hive_mind/phases/phase_debate.py`)
- [x] Adaptive turns (3-10) based on complexity
- [x] Structured debate with SUPPORT/OPPOSE/CONCEDE positions
- [x] Timeout + forced vote

### Phase 4: Architecture Generation ✅ COMPLETE
- [x] `ArchitectureGenerationPhase` (`core/hive_mind/phases/phase_architecture.py`)
- [x] Agent topology generation
- [x] Registry check for duplicates
- [x] User breakpoint BEFORE_SPAWN

### Phase 5: Monitored Execution ✅ COMPLETE
- [x] `MonitoredExecutionPhase` (`core/hive_mind/phases/phase_execution.py`)
- [x] Step-by-step execution with monitoring
- [x] Hallucination and error pattern detection
- [x] Artifact verification

### Phase 6: Failure Analysis + Retry ✅ COMPLETE
- [x] `FailureDiagnosisPhase` (`core/hive_mind/phases/phase_diagnosis.py`)
- [x] Cross-agent diagnosis (parallel Gemini + Claude)
- [x] `AdaptiveRetryPhase` (`core/hive_mind/phases/phase_retry.py`)
- [x] Strategy blacklist integration

### Phase 7: Knowledge Consolidation ✅ COMPLETE (User Decision Q4)
- [x] `KnowledgeConsolidationPhase` (`core/hive_mind/phases/phase_consolidation.py`)
- [x] Post-task reflection by both agents
- [x] Knowledge archival to RAG (ProjectMemory)
- [x] Agent retention decisions

### V8.0 Integrations ✅ COMPLETE
- [x] **fsm_handlers → TrueHiveMind**: Gating hook in `_handle_moderate_plus()`
- [x] **CostEstimator → BudgetTracker**: USD budget chain (tokens → USD conversion)
- [x] **StagnationDetector → StrategyBlacklist**: STAGNATION category + auto-report

---

## 6. ESTIMATION RÉVISÉE

| Composant | Effort Initial | Effort Révisé | Raison |
|-----------|----------------|---------------|--------|
| Phase 0 (Infrastructure) | Non prévu | 2-3 jours | Registry, Cost, Context, Blacklist |
| Phase 1 (Analysis) | 1 jour | 1-2 jours | + FSM states |
| Phase 2 (Debate) | 2-3 jours | 2-3 jours | Inchangé |
| Phase 3 (Architecture) | 3-4 jours | 3-4 jours | + Registry integration |
| Phase 4 (Execution) | 1-2 jours | 2 jours | + Monitoring |
| Phase 5-6 (Diagnosis/Retry) | 4 jours | 3-4 jours | + Blacklist |
| Integration | 3-4 jours | 4-5 jours | FSM plus complexe |
| **TOTAL** | **~15-18 jours** | **~18-23 jours** | +20% pour robustesse |

---

## 7. DÉCISIONS À PRENDRE

### Questions Ouvertes

1. **Gating Threshold**: MODERATE inclus dans V8.0 ou V7.9?
   - Option A: MODERATE → V7.9 (plus conservateur)
   - Option B: MODERATE → V8.0 (plus agressif)

2. **Auto-Spawn Policy**: Toujours demander confirmation ou auto-spawn si confiance haute?
   - Option A: Toujours demander (plus sûr)
   - Option B: Auto si confidence > 0.9 ET cost < budget/4 (plus autonome)

3. **Debate Max Turns**: Combien avant forced vote?
   - Option A: 4 tours (rapide, risque de mauvaise décision)
   - Option B: 6 tours (plus de débat, plus de tokens)
   - Option C: Adaptatif selon complexité (COMPLEX=4, EXPERT=6)

4. **Agent TTL**: Durée de vie des agents spawned?
   - Option A: Permanent (risque pollution)
   - Option B: Session-only (perte de travail)
   - Option C: Configurable TTL + GC weekly
