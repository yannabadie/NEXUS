# TRUE HIVE MIND - Architecture V8.0

**Objectif**: Transformer NEXUS d'un "orchestrateur séquentiel avec fallback" en une "intelligence collaborative autonome".

---

## Problème Actuel (V7.9)

```
Tâche → Scoring → Mode (6 fixes) → Exécution → Fallback si échec → Fin
         ↑                              ↑
    Déterministe              Pas d'analyse d'erreur
    (pas de débat)            (juste "essaie le suivant")
```

## Architecture Cible (V8.0)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRUE HIVE MIND LOOP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   PHASE 1    │    │   PHASE 2    │    │   PHASE 3    │                  │
│  │  INDEPENDENT │───▶│   STRATEGIC  │───▶│ ARCHITECTURE │                  │
│  │   ANALYSIS   │    │    DEBATE    │    │  GENERATION  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  Gemini analyse      Arguments +         Auto-Spawn si                     │
│  SEUL, puis          Contre-arguments    nécessaire +                      │
│  Claude analyse      jusqu'à consensus   RAG injection                     │
│  SEUL                                                                      │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   PHASE 4    │    │   PHASE 5    │    │   PHASE 6    │                  │
│  │  EXECUTION   │───▶│   FAILURE    │───▶│   ADAPTIVE   │                  │
│  │              │    │   ANALYSIS   │    │    RETRY     │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  Exécution avec      Diagnostic:         Nouvelle stratégie                │
│  monitoring          POURQUOI échec?     basée sur diagnostic              │
│  temps réel          Pattern matching    (pas juste fallback)              │
│                                                                             │
│                      ◄───────────────────────┘                             │
│                      (Boucle jusqu'à succès ou budget épuisé)              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: INDEPENDENT ANALYSIS

### Problème V7.9
Les deux agents reçoivent le MÊME contexte et la MÊME proposition initiale.

### Solution V8.0

```python
# core/hive_mind/independent_analysis.py

@dataclass
class IndependentAnalysis:
    """Résultat d'analyse indépendante d'un agent."""
    agent_id: str
    task_understanding: str          # Comment l'agent comprend la tâche
    complexity_assessment: str       # Son évaluation de complexité
    proposed_approach: str           # Son approche proposée
    required_capabilities: List[str] # Capacités nécessaires selon lui
    potential_risks: List[str]       # Risques identifiés
    confidence: float                # Confiance dans son analyse
    reasoning: str                   # Chain-of-thought complet


class IndependentAnalyzer:
    """
    Fait analyser la tâche par chaque agent SÉPARÉMENT.

    Crucial: Chaque agent NE VOIT PAS l'analyse de l'autre.
    """

    async def analyze_independently(
        self,
        task: str,
        context: Dict
    ) -> Tuple[IndependentAnalysis, IndependentAnalysis]:
        """
        Lance les analyses en parallèle, sans contamination croisée.
        """
        # Prompt pour analyse indépendante
        analysis_prompt = """
        ANALYSE INDÉPENDANTE - Tu es SEUL à analyser cette tâche.

        TÂCHE: {task}
        CONTEXTE: {context}

        Réponds UNIQUEMENT en JSON:
        {{
            "task_understanding": "Comment tu comprends cette tâche",
            "complexity_assessment": "TRIVIAL|MODERATE|COMPLEX|EXPERT + justification",
            "proposed_approach": "Ta stratégie détaillée",
            "required_capabilities": ["cap1", "cap2", ...],
            "potential_risks": ["risk1", "risk2", ...],
            "confidence": 0.0-1.0,
            "reasoning": "Ton raisonnement complet (chain-of-thought)"
        }}

        IMPORTANT: Ne suppose PAS ce que l'autre agent penserait.
        Donne TON analyse authentique.
        """

        # Lancer en parallèle
        gemini_task = self._invoke_agent("gemini", analysis_prompt)
        claude_task = self._invoke_agent("claude", analysis_prompt)

        gemini_analysis, claude_analysis = await asyncio.gather(
            gemini_task, claude_task
        )

        return gemini_analysis, claude_analysis
```

---

## Phase 2: STRATEGIC DEBATE

### Problème V7.9
- Max 4 tours arbitraires
- Agents demandent juste "tu es d'accord?"
- Consensus = timeout ou "oui"

### Solution V8.0

```python
# core/hive_mind/strategic_debate.py

@dataclass
class DebateArgument:
    """Un argument dans le débat."""
    agent_id: str
    position: str                    # "SUPPORT" ou "OPPOSE"
    target_point: str                # Quel point de l'autre il adresse
    argument: str                    # Son argument
    evidence: List[str]              # Preuves/exemples
    proposed_modification: Optional[str]  # Modification suggérée
    concession: Optional[str]        # Ce qu'il concède à l'autre


class StrategicDebate:
    """
    Protocole de débat structuré avec arguments explicites.
    """

    def __init__(self, max_rounds: int = 6, consensus_threshold: float = 0.85):
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold

    async def debate(
        self,
        gemini_analysis: IndependentAnalysis,
        claude_analysis: IndependentAnalysis,
        task: str
    ) -> DebateResult:
        """
        Débat structuré jusqu'à consensus ou désaccord explicite.
        """
        debate_history = []

        # Identifier les DÉSACCORDS explicites
        disagreements = self._identify_disagreements(
            gemini_analysis, claude_analysis
        )

        if not disagreements:
            # Consensus immédiat
            return DebateResult(
                status="IMMEDIATE_CONSENSUS",
                final_approach=self._merge_approaches(gemini_analysis, claude_analysis),
                debate_history=[]
            )

        # Débat sur chaque désaccord
        for round_num in range(self.max_rounds):
            # Tour de Gemini: défendre sa position
            gemini_argument = await self._get_argument(
                agent="gemini",
                own_analysis=gemini_analysis,
                other_analysis=claude_analysis,
                disagreements=disagreements,
                history=debate_history,
                prompt_type="DEFEND_OR_CONCEDE"
            )
            debate_history.append(gemini_argument)

            # Tour de Claude: répondre à l'argument
            claude_argument = await self._get_argument(
                agent="claude",
                own_analysis=claude_analysis,
                other_analysis=gemini_analysis,
                disagreements=disagreements,
                history=debate_history,
                last_argument=gemini_argument,
                prompt_type="RESPOND_AND_PROPOSE"
            )
            debate_history.append(claude_argument)

            # Vérifier convergence
            consensus = self._check_consensus(debate_history, disagreements)
            if consensus.score >= self.consensus_threshold:
                return DebateResult(
                    status="CONSENSUS_REACHED",
                    final_approach=consensus.merged_approach,
                    debate_history=debate_history,
                    resolved_disagreements=consensus.resolved,
                    remaining_disagreements=consensus.unresolved
                )

        # Max rounds atteint - décision par vote pondéré
        return self._resolve_by_weighted_vote(
            gemini_analysis, claude_analysis, debate_history
        )

    def _identify_disagreements(
        self,
        a1: IndependentAnalysis,
        a2: IndependentAnalysis
    ) -> List[Disagreement]:
        """
        Identifie les points de désaccord explicites.
        """
        disagreements = []

        # Comparer complexité
        if a1.complexity_assessment != a2.complexity_assessment:
            disagreements.append(Disagreement(
                topic="complexity",
                gemini_position=a1.complexity_assessment,
                claude_position=a2.complexity_assessment
            ))

        # Comparer approches
        approach_similarity = self._semantic_similarity(
            a1.proposed_approach, a2.proposed_approach
        )
        if approach_similarity < 0.7:
            disagreements.append(Disagreement(
                topic="approach",
                gemini_position=a1.proposed_approach,
                claude_position=a2.proposed_approach
            ))

        # Comparer capacités requises
        gemini_caps = set(a1.required_capabilities)
        claude_caps = set(a2.required_capabilities)
        if gemini_caps != claude_caps:
            disagreements.append(Disagreement(
                topic="required_capabilities",
                gemini_position=list(gemini_caps),
                claude_position=list(claude_caps),
                gemini_only=list(gemini_caps - claude_caps),
                claude_only=list(claude_caps - gemini_caps)
            ))

        return disagreements
```

---

## Phase 3: ARCHITECTURE GENERATION (Auto-Spawn)

### Problème V7.9
- 6 modes hardcodés
- Jamais de spawn automatique
- Utilisateur doit /spawn manuellement

### Solution V8.0

```python
# core/hive_mind/architecture_generator.py

@dataclass
class AgentArchitecture:
    """Architecture d'agents générée pour une tâche."""
    required_agents: List[AgentSpec]
    collaboration_pattern: str       # Custom pattern, pas juste 6 modes
    rag_requirements: RAGConfig
    tool_requirements: List[ToolSpec]
    execution_plan: ExecutionPlan


@dataclass
class AgentSpec:
    """Spécification d'un agent à spawner."""
    role: str                        # "security_expert", "pdf_parser", etc.
    capabilities: List[str]
    spawn_if_missing: bool           # True = auto-spawn
    fallback_agent: str              # "claude" ou "gemini" si spawn échoue


class ArchitectureGenerator:
    """
    Génère une architecture d'agents basée sur le consensus du débat.

    NOUVEAU: Peut décider de spawner des agents spécialisés.
    """

    async def generate(
        self,
        task: str,
        debate_result: DebateResult,
        existing_agents: List[str]
    ) -> AgentArchitecture:
        """
        Génère l'architecture optimale pour la tâche.
        """
        required_capabilities = debate_result.final_approach.required_capabilities

        # Vérifier quelles capacités sont couvertes
        covered, missing = self._check_capability_coverage(
            required_capabilities, existing_agents
        )

        agents_to_use = []
        agents_to_spawn = []

        for capability in required_capabilities:
            if capability in covered:
                agents_to_use.append(covered[capability])
            else:
                # Capacité manquante -> proposer spawn
                agent_spec = self._design_specialist(capability)
                agents_to_spawn.append(agent_spec)

        # Si spawn nécessaire, demander confirmation ou auto-spawn
        if agents_to_spawn:
            architecture = await self._handle_spawn_decision(
                task, agents_to_spawn, debate_result
            )
        else:
            architecture = self._design_collaboration(
                task, agents_to_use, debate_result
            )

        # Configurer RAG si nécessaire
        architecture.rag_requirements = self._determine_rag_needs(
            task, debate_result
        )

        return architecture

    async def _handle_spawn_decision(
        self,
        task: str,
        agents_to_spawn: List[AgentSpec],
        debate_result: DebateResult
    ) -> AgentArchitecture:
        """
        Décide si on spawn automatiquement ou on demande à l'utilisateur.
        """
        # Règles d'auto-spawn
        auto_spawn_rules = {
            "complexity": debate_result.complexity >= TaskComplexity.COMPLEX,
            "confidence": debate_result.consensus_confidence >= 0.9,
            "cost_acceptable": self._estimate_spawn_cost(agents_to_spawn) < BUDGET_THRESHOLD
        }

        if all(auto_spawn_rules.values()):
            # Auto-spawn approuvé
            spawned_agents = []
            for spec in agents_to_spawn:
                agent = await self._spawn_agent(spec)
                spawned_agents.append(agent)

            return self._design_collaboration_with_spawned(
                task, spawned_agents, debate_result
            )
        else:
            # Demander à l'utilisateur
            suggestion = self._format_spawn_suggestion(agents_to_spawn)
            return AgentArchitecture(
                status="SPAWN_SUGGESTED",
                suggestion=suggestion,
                spawn_commands=[
                    f'/spawn "{spec.role}" --mission "{spec.mission}"'
                    for spec in agents_to_spawn
                ]
            )

    def _design_specialist(self, capability: str) -> AgentSpec:
        """
        Conçoit un agent spécialisé pour une capacité manquante.
        """
        # Templates de spécialistes
        specialist_templates = {
            "pdf_parsing": AgentSpec(
                role="pdf_expert",
                mission="Expert en extraction et analyse de documents PDF",
                capabilities=["pdf_extraction", "ocr", "table_parsing"],
                tools_priority=["read_pdf", "ocr_extract", "table_to_json"]
            ),
            "security_audit": AgentSpec(
                role="security_auditor",
                mission="Expert en audit de sécurité et détection de vulnérabilités",
                capabilities=["vulnerability_scan", "code_review", "threat_modeling"],
                tools_priority=["static_analysis", "dependency_check"]
            ),
            "data_analysis": AgentSpec(
                role="data_analyst",
                mission="Expert en analyse de données et visualisation",
                capabilities=["statistics", "visualization", "pattern_detection"],
                tools_priority=["pandas_query", "plot_chart", "correlation_analysis"]
            )
            # ... autres templates
        }

        return specialist_templates.get(
            capability,
            self._generate_custom_specialist(capability)
        )
```

---

## Phase 4: EXECUTION WITH MONITORING

### Solution V8.0

```python
# core/hive_mind/monitored_execution.py

class MonitoredExecution:
    """
    Exécution avec monitoring temps réel et détection de problèmes.
    """

    async def execute(
        self,
        architecture: AgentArchitecture,
        task: str
    ) -> ExecutionResult:
        """
        Exécute avec monitoring continu.
        """
        execution_log = []

        for step in architecture.execution_plan.steps:
            step_result = await self._execute_step(step)
            execution_log.append(step_result)

            # Monitoring temps réel
            issues = self._detect_issues(step_result)
            if issues:
                # Alerte immédiate, pas attendre la fin
                for issue in issues:
                    if issue.severity == "CRITICAL":
                        return ExecutionResult(
                            status="EARLY_FAILURE",
                            failed_at_step=step,
                            issue=issue,
                            partial_results=execution_log,
                            needs_retry=True
                        )
                    elif issue.severity == "WARNING":
                        # Log mais continue
                        execution_log.append(f"WARNING: {issue}")

        return ExecutionResult(
            status="COMPLETED",
            results=execution_log
        )

    def _detect_issues(self, step_result: StepResult) -> List[Issue]:
        """
        Détecte les problèmes pendant l'exécution.
        """
        issues = []

        # Timeout
        if step_result.duration > step_result.expected_duration * 2:
            issues.append(Issue(
                type="TIMEOUT_RISK",
                severity="WARNING",
                details=f"Step took {step_result.duration}s, expected {step_result.expected_duration}s"
            ))

        # Erreur explicite
        if step_result.error:
            issues.append(Issue(
                type="EXECUTION_ERROR",
                severity="CRITICAL",
                details=step_result.error,
                error_category=self._categorize_error(step_result.error)
            ))

        # Output vide ou suspect
        if not step_result.output or len(step_result.output) < 10:
            issues.append(Issue(
                type="EMPTY_OUTPUT",
                severity="WARNING",
                details="Step produced minimal output"
            ))

        # Hallucination détectée (fichiers mentionnés mais inexistants)
        fake_artifacts = self._check_artifact_existence(step_result.output)
        if fake_artifacts:
            issues.append(Issue(
                type="HALLUCINATION",
                severity="CRITICAL",
                details=f"Mentioned non-existent files: {fake_artifacts}"
            ))

        return issues
```

---

## Phase 5: FAILURE ANALYSIS

### Problème V7.9
- "Échec → essaie le mode suivant"
- Aucune analyse du POURQUOI

### Solution V8.0

```python
# core/hive_mind/failure_analyzer.py

@dataclass
class FailureDiagnosis:
    """Diagnostic détaillé d'un échec."""
    failure_type: str                # "TIMEOUT", "CAPABILITY_MISSING", "STRATEGY_WRONG", etc.
    root_cause: str                  # Cause racine identifiée
    contributing_factors: List[str]  # Facteurs contribuants
    evidence: List[str]              # Preuves du diagnostic
    recommended_changes: List[str]   # Changements recommandés
    confidence: float                # Confiance dans le diagnostic


class FailureAnalyzer:
    """
    Analyse les échecs pour comprendre POURQUOI et proposer des solutions.
    """

    FAILURE_PATTERNS = {
        "timeout": {
            "indicators": ["timed out", "exceeded", "too long"],
            "root_causes": ["task_too_complex", "agent_overloaded", "wrong_agent"],
            "solutions": ["split_task", "use_faster_agent", "increase_timeout"]
        },
        "capability_missing": {
            "indicators": ["cannot", "don't know how", "not supported"],
            "root_causes": ["wrong_agent_selected", "tool_missing", "need_specialist"],
            "solutions": ["spawn_specialist", "add_tool", "use_different_approach"]
        },
        "hallucination": {
            "indicators": ["file not found", "doesn't exist", "no such"],
            "root_causes": ["agent_hallucinated", "context_lost", "wrong_assumption"],
            "solutions": ["add_verification_step", "provide_more_context", "use_rag"]
        },
        "strategy_wrong": {
            "indicators": ["doesn't work", "wrong approach", "need different"],
            "root_causes": ["bad_mode_selection", "wrong_architecture", "misunderstood_task"],
            "solutions": ["re_debate", "change_architecture", "clarify_task"]
        }
    }

    async def analyze(
        self,
        execution_result: ExecutionResult,
        architecture: AgentArchitecture,
        debate_result: DebateResult
    ) -> FailureDiagnosis:
        """
        Analyse un échec et produit un diagnostic actionnable.
        """
        # Collecter les indices
        error_text = execution_result.error or ""
        output_text = execution_result.partial_output or ""

        # Classifier le type d'échec
        failure_type = self._classify_failure(error_text, output_text)

        # Analyser la cause racine
        root_cause = await self._find_root_cause(
            failure_type,
            execution_result,
            architecture,
            debate_result
        )

        # Générer les recommandations
        recommendations = self._generate_recommendations(
            failure_type,
            root_cause,
            architecture
        )

        return FailureDiagnosis(
            failure_type=failure_type,
            root_cause=root_cause,
            contributing_factors=self._find_contributing_factors(execution_result),
            evidence=self._collect_evidence(execution_result),
            recommended_changes=recommendations,
            confidence=self._calculate_confidence(failure_type, root_cause)
        )

    async def _find_root_cause(
        self,
        failure_type: str,
        execution_result: ExecutionResult,
        architecture: AgentArchitecture,
        debate_result: DebateResult
    ) -> str:
        """
        Trouve la cause racine via analyse et/ou consultation des agents.
        """
        # D'abord, pattern matching
        pattern_match = self._pattern_match_cause(failure_type, execution_result)
        if pattern_match and pattern_match.confidence > 0.8:
            return pattern_match.cause

        # Sinon, demander aux agents d'analyser
        analysis_prompt = f"""
        ANALYSE D'ÉCHEC - Trouve la cause racine.

        TYPE D'ÉCHEC: {failure_type}
        ERREUR: {execution_result.error}
        ARCHITECTURE UTILISÉE: {architecture.summary()}
        DÉBAT INITIAL: {debate_result.summary()}

        Questions à répondre:
        1. Pourquoi cette approche a-t-elle échoué?
        2. Qu'est-ce qui aurait dû être fait différemment?
        3. L'architecture était-elle adaptée à la tâche?

        Réponds en JSON:
        {{
            "root_cause": "...",
            "what_went_wrong": "...",
            "what_should_have_been_done": "..."
        }}
        """

        gemini_analysis = await self._invoke_agent("gemini", analysis_prompt)
        claude_analysis = await self._invoke_agent("claude", analysis_prompt)

        # Synthétiser les deux analyses
        return self._synthesize_root_cause(gemini_analysis, claude_analysis)
```

---

## Phase 6: ADAPTIVE RETRY

### Problème V7.9
- Fallback hardcodé: PING_PONG → SEQUENTIAL → PARALLEL
- Pas basé sur le diagnostic

### Solution V8.0

```python
# core/hive_mind/adaptive_retry.py

class AdaptiveRetry:
    """
    Retry intelligent basé sur le diagnostic d'échec.
    """

    def __init__(self, max_retries: int = 3, budget_limit: float = 100.0):
        self.max_retries = max_retries
        self.budget_limit = budget_limit
        self.retry_history = []

    async def retry_with_new_strategy(
        self,
        task: str,
        failure_diagnosis: FailureDiagnosis,
        previous_architecture: AgentArchitecture,
        debate_result: DebateResult
    ) -> RetryDecision:
        """
        Décide comment réessayer basé sur le diagnostic.
        """
        # Vérifier budget
        if self._budget_exceeded():
            return RetryDecision(
                action="STOP",
                reason="Budget exceeded",
                suggestion="Consider manual intervention"
            )

        # Vérifier si on a déjà essayé cette stratégie
        if self._strategy_already_tried(failure_diagnosis.recommended_changes):
            return RetryDecision(
                action="ESCALATE",
                reason="All known strategies exhausted",
                suggestion="Task may require human guidance"
            )

        # Appliquer les changements recommandés
        new_strategy = await self._apply_recommendations(
            failure_diagnosis,
            previous_architecture,
            debate_result
        )

        self.retry_history.append({
            "attempt": len(self.retry_history) + 1,
            "failure_type": failure_diagnosis.failure_type,
            "root_cause": failure_diagnosis.root_cause,
            "new_strategy": new_strategy.summary()
        })

        return RetryDecision(
            action="RETRY",
            new_architecture=new_strategy.architecture,
            changes_made=new_strategy.changes,
            expected_improvement=new_strategy.expected_improvement
        )

    async def _apply_recommendations(
        self,
        diagnosis: FailureDiagnosis,
        prev_arch: AgentArchitecture,
        debate: DebateResult
    ) -> NewStrategy:
        """
        Applique les recommandations du diagnostic.
        """
        changes = []
        new_arch = prev_arch.copy()

        for recommendation in diagnosis.recommended_changes:
            if recommendation == "spawn_specialist":
                # Auto-spawn un spécialiste
                specialist = await self._spawn_for_capability(
                    diagnosis.missing_capability
                )
                new_arch.agents.append(specialist)
                changes.append(f"Spawned specialist: {specialist.role}")

            elif recommendation == "change_architecture":
                # Regénérer l'architecture complètement
                new_arch = await self._regenerate_architecture(
                    debate,
                    exclude_patterns=[prev_arch.pattern]  # Ne pas réutiliser le même
                )
                changes.append(f"Changed architecture from {prev_arch.pattern} to {new_arch.pattern}")

            elif recommendation == "add_verification_step":
                # Ajouter une étape de vérification
                new_arch.execution_plan.add_step(
                    VerificationStep(
                        name="artifact_verification",
                        position="after_each_tool_call"
                    )
                )
                changes.append("Added artifact verification step")

            elif recommendation == "use_rag":
                # Activer/améliorer RAG
                new_arch.rag_requirements = RAGConfig(
                    enabled=True,
                    depth="deep",
                    sources=["codebase", "docs", "history"]
                )
                changes.append("Enhanced RAG injection")

            elif recommendation == "split_task":
                # Décomposer la tâche
                subtasks = await self._decompose_task(debate.task)
                new_arch.execution_plan = ExecutionPlan(
                    strategy="sequential_subtasks",
                    subtasks=subtasks
                )
                changes.append(f"Split task into {len(subtasks)} subtasks")

        return NewStrategy(
            architecture=new_arch,
            changes=changes,
            expected_improvement=self._estimate_improvement(changes)
        )
```

---

## Intégration: Le Loop Principal

```python
# core/hive_mind/main_loop.py

class TrueHiveMind:
    """
    Le loop principal de l'intelligence collaborative.
    """

    async def process_task(self, task: str) -> HiveMindResult:
        """
        Traite une tâche avec le full pipeline.
        """
        attempt = 0

        while attempt < self.max_attempts:
            attempt += 1

            # PHASE 1: Analyse indépendante
            gemini_analysis, claude_analysis = await self.analyzer.analyze_independently(
                task, self.context
            )

            # PHASE 2: Débat stratégique
            debate_result = await self.debater.debate(
                gemini_analysis, claude_analysis, task
            )

            # PHASE 3: Génération d'architecture
            architecture = await self.architect.generate(
                task, debate_result, self.existing_agents
            )

            # Si spawn suggéré mais pas auto-approuvé
            if architecture.status == "SPAWN_SUGGESTED":
                # Proposer à l'utilisateur ou auto-spawn si confiance haute
                if self._should_auto_spawn(architecture):
                    architecture = await self._execute_spawns(architecture)
                else:
                    return HiveMindResult(
                        status="SPAWN_NEEDED",
                        suggestion=architecture.spawn_commands
                    )

            # PHASE 4: Exécution avec monitoring
            execution_result = await self.executor.execute(architecture, task)

            if execution_result.status == "COMPLETED":
                # Succès!
                return HiveMindResult(
                    status="SUCCESS",
                    output=execution_result.results,
                    architecture_used=architecture,
                    attempts=attempt
                )

            # PHASE 5: Analyse d'échec
            diagnosis = await self.failure_analyzer.analyze(
                execution_result, architecture, debate_result
            )

            # PHASE 6: Retry adaptatif
            retry_decision = await self.retry_handler.retry_with_new_strategy(
                task, diagnosis, architecture, debate_result
            )

            if retry_decision.action == "STOP":
                return HiveMindResult(
                    status="FAILED",
                    reason=retry_decision.reason,
                    attempts=attempt,
                    diagnosis=diagnosis
                )
            elif retry_decision.action == "ESCALATE":
                return HiveMindResult(
                    status="NEEDS_HUMAN",
                    reason=retry_decision.reason,
                    suggestion=retry_decision.suggestion
                )

            # Préparer le prochain attempt avec la nouvelle stratégie
            self.context["previous_attempt"] = {
                "architecture": architecture,
                "failure": diagnosis,
                "changes": retry_decision.changes_made
            }

        return HiveMindResult(
            status="MAX_ATTEMPTS_REACHED",
            attempts=attempt
        )
```

---

## Résumé des Changements

| Aspect | V7.9 (Actuel) | V8.0 (Proposé) |
|--------|---------------|----------------|
| Analyse | Identique pour les 2 agents | Indépendante puis comparée |
| Débat | 2-4 tours, "tu es d'accord?" | Arguments structurés, consensus explicite |
| Architecture | 6 modes fixes | Génération dynamique + auto-spawn |
| Exécution | Fire-and-forget | Monitoring temps réel |
| Échec | Fallback hardcodé | Diagnostic + retry adaptatif |
| Apprentissage | Record metrics | Patterns appris, stratégies évitées |

---

## Fichiers à Créer

```
core/hive_mind/
├── __init__.py
├── independent_analysis.py    # Phase 1
├── strategic_debate.py        # Phase 2
├── architecture_generator.py  # Phase 3
├── monitored_execution.py     # Phase 4
├── failure_analyzer.py        # Phase 5
├── adaptive_retry.py          # Phase 6
├── main_loop.py               # Intégration
└── types.py                   # Dataclasses
```

---

## Estimation d'Effort

| Phase | Complexité | Estimation |
|-------|------------|------------|
| Phase 1: Independent Analysis | Moyenne | 1 jour |
| Phase 2: Strategic Debate | Haute | 2-3 jours |
| Phase 3: Architecture Generator | Très Haute | 3-4 jours |
| Phase 4: Monitored Execution | Moyenne | 1-2 jours |
| Phase 5: Failure Analyzer | Haute | 2 jours |
| Phase 6: Adaptive Retry | Haute | 2 jours |
| Intégration + Tests | Haute | 3-4 jours |
| **Total** | | **~15-18 jours** |

---

## Questions Ouvertes

1. **Auto-spawn budget**: Limite de coût pour auto-spawn sans confirmation?
2. **Débat max rounds**: Combien de tours de débat avant vote forcé?
3. **Retry budget**: Budget max avant escalade à l'humain?
4. **Patterns à apprendre**: Quels patterns stocker pour apprentissage?
