# Analyse des Failles de Raisonnement - Branche NX

**Date**: 2025-12-15
**Analyste**: Claude Opus 4.5
**Branche**: NX (V9.4-V10 PRISM)
**Scope**: Core Logic Reasoning Failures

---

## 1. Vue d'Ensemble des Flux de Raisonnement

```
USER INPUT
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ FSM Dispatcher (process_turn)                                    │
│   ├── TaskAnalyzer.analyze() ──────────────────────────────────┼──► FAILLE F1
│   │       └── Complexity: TRIVIAL | SIMPLE | MODERATE+          │
│   │                                                              │
│   ├── TRIVIAL → Fast Path (direct response) ────────────────────┼──► FAILLE F2
│   │                                                              │
│   ├── SIMPLE → Single Agent Mode ───────────────────────────────┼──► FAILLE F3
│   │                                                              │
│   └── MODERATE+ → Swarm or HiveMind ────────────────────────────┼──► FAILLE F4-F8
│           │                                                      │
│           ├── ModeSelector.select_mode()                        │
│           ├── NegotiationProtocol.negotiate()                   │
│           └── ModeExecutor.execute()                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Failles Identifiées

### F1: Classification de Complexité Incorrecte

**Localisation**: `core/swarm/task_analyzer.py`

**Problème**:
Le `TaskAnalyzer` utilise des heuristiques basées sur les mots-clés pour déterminer la complexité. Cette approche peut mal classifier des tâches:

```python
# Exemple de faux négatif
task = "Ajoute un log"  # Classifié TRIVIAL
# Mais si le contexte est un système distribué complexe,
# cela devrait être MODERATE (multi-fichiers, impact sur performance)
```

**Impact**:
- Tâches complexes traitées par Fast Path → réponses superficielles
- Tâches simples envoyées au Swarm → latence inutile

**Scénarios de Failure**:
1. "Fix the bug" classifié SIMPLE mais le bug est dans l'interaction de 5 modules
2. "Update the README" classifié TRIVIAL mais nécessite analyse du code

**Mitigation Proposée**:
```python
# Ajouter analyse contextuelle
class EnhancedTaskAnalyzer:
    def analyze(self, task: str, context: ProjectContext) -> TaskAnalysis:
        # 1. Heuristique mots-clés (actuel)
        base_complexity = self._keyword_analysis(task)

        # 2. NOUVEAU: Analyse du contexte projet
        project_complexity = context.get_estimated_impact(task)

        # 3. Ajustement si divergence
        if project_complexity > base_complexity + 1:
            return self._upgrade_complexity(base_complexity)
```

---

### F2: Fast Path Sans Validation de Complétude

**Localisation**: `core/orchestration/fsm_handlers.py:_handle_trivial()`

**Problème**:
Les tâches TRIVIAL contournent la validation de complétude (`TaskCompletionValidator`). Si la tâche est mal classifiée comme TRIVIAL, l'agent peut retourner une réponse incomplète sans qu'elle soit vérifiée.

```python
def _handle_trivial(self, user_input: str) -> Dict:
    # Réponse directe SANS validation
    response = self._get_static_or_gemini_response(user_input)
    return self._make_result("FINISHED", response, "gemini", True)
    # ^^^ Pas de TaskCompletionValidator.validate_completion() !
```

**Impact**:
- Réponses incomplètes acceptées comme finies
- Pas de détection des "ongoing work indicators"

**Scénarios de Failure**:
1. Agent dit "I'll fix that" au lieu de réellement fixer
2. Réponse contient "TODO" mais marquée comme FINISHED

**Mitigation Proposée**:
```python
def _handle_trivial(self, user_input: str) -> Dict:
    response = self._get_static_or_gemini_response(user_input)

    # NOUVEAU: Validation légère même pour TRIVIAL
    if self._has_incomplete_indicators(response):
        # Upgrade vers SIMPLE pour traitement complet
        return self._execute_simple_task(user_input, task_analysis)

    return self._make_result("FINISHED", response, "gemini", True)
```

---

### F3: Single Agent Mode Sans Fallback

**Localisation**: `core/orchestration/fsm_handlers.py:_execute_simple_task()`

**Problème**:
En mode SIMPLE, un seul agent traite la tâche. Si cet agent échoue ou produit une réponse de mauvaise qualité, il n'y a pas de second avis.

**Impact**:
- Pas de CFL (Cognitive Feedback Loop) en mode SIMPLE
- Hallucinations non détectées
- Réponses incorrectes acceptées

**Scénarios de Failure**:
1. Gemini hallucine un nom de fichier → aucune vérification
2. Claude propose une solution avec un bug → pas de review

**Mitigation Proposée**:
```python
def _execute_simple_task(self, user_input, task_analysis) -> Dict:
    response = self._invoke_agent(task_type, context)

    # NOUVEAU: Light CFL même pour SIMPLE
    if self._requires_verification(task_analysis):
        alternate_agent = self._registry.get_alternate(self.active_agent)
        verification = self._quick_verify(alternate_agent, response)

        if not verification.is_valid:
            # Upgrade vers MODERATE pour traitement complet
            return self._handle_moderate_plus(user_input, task_analysis)
```

---

### F4: Race Condition dans PARALLEL Mode

**Localisation**: `core/swarm/executors/parallel_executor.py`

**Problème**:
En mode PARALLEL, deux agents travaillent simultanément. Le merge des résultats peut créer des incohérences si les deux agents modifient la même ressource conceptuelle.

```python
# parallel_executor.py
def execute(self, context: ExecutionContext) -> ExecutionResult:
    # Lance les deux agents en parallèle
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(self._invoke, context, agent.agent_id, ...)
            for agent in agents
        ]

    # Merge des résultats
    merged = self.merge_strategy.merge(outputs)
    # ^^^ Que faire si Agent A dit "delete file X" et Agent B dit "modify file X" ?
```

**Impact**:
- Conflits non résolus dans le merge
- Actions contradictoires possibles
- État incohérent du workspace

**Scénarios de Failure**:
1. Agent A: "J'ai créé auth.py" / Agent B: "J'ai modifié auth.py" (qui n'existait pas pour B)
2. Agent A: "Utilisons React" / Agent B: "Utilisons Vue" → merge confus

**Mitigation Proposée**:
```python
class ConflictAwareMergeStrategy:
    def merge(self, outputs: List[AgentResponse]) -> MergeResult:
        # 1. Détecter les conflits
        conflicts = self._detect_conflicts(outputs)

        if conflicts:
            # 2. Résolution par arbitrage (lead agent décide)
            lead_decision = self._arbitrate(conflicts, lead_agent)
            return self._merge_with_resolution(outputs, lead_decision)

        return self._standard_merge(outputs)
```

---

### F5: Stagnation Detector Trop Sensible

**Localisation**: `core/fsm/stagnation_detector.py`

**Problème**:
Le détecteur de stagnation compare les 3 derniers messages avec un seuil de 0.8 de similarité. Cela peut déclencher de faux positifs quand les agents discutent légitimement d'un même sujet.

```python
class StagnationDetector:
    def __init__(self, similarity_threshold: float = 0.8, window_size: int = 3):
        # Seuil trop strict pour discussions légitimes
```

**Impact**:
- Interruption prématurée de brainstorming productif
- Forçage d'action avant consensus réel
- Perte de nuances dans le raisonnement

**Scénarios de Failure**:
1. Agents débattent architecture → 3 messages mentionnent "microservices" → fausse stagnation
2. Refinement itératif d'une solution → messages similaires par design → interruption

**Mitigation Proposée**:
```python
class AdaptiveStagnationDetector:
    def is_stagnant(self) -> bool:
        # 1. Similarité textuelle (actuel)
        text_similarity = self._compute_similarity()

        # 2. NOUVEAU: Progrès sémantique
        semantic_progress = self._compute_semantic_delta()

        # 3. Stagnation = haute similarité ET pas de progrès sémantique
        return text_similarity > 0.8 and semantic_progress < 0.2
```

---

### F6: JSON Parsing Silent Failures

**Localisation**: `core/hive_mind/json_parser.py`, `core/utils/json_extractor.py`

**Problème**:
Le parser JSON a plusieurs stratégies de fallback, mais certaines peuvent produire des résultats partiellement corrects sans signaler d'erreur.

```python
def parse_json_response(response, agent_id, default=None):
    # Strategy 3: Fix common JSON issues
    try:
        fixed = json_str.replace("'", '"')  # DANGEREUX: Change le contenu aussi !
        # "L'utilisateur a dit 'oui'" devient "L"utilisateur a dit "oui""
```

**Impact**:
- Données corrompues silencieusement
- Interprétation incorrecte des intentions de l'agent
- Actions basées sur JSON malformé

**Scénarios de Failure**:
1. Agent inclut du code avec apostrophes → JSON corrompu
2. Réponse avec nested quotes → parsing incorrect

**Mitigation Proposée**:
```python
def parse_json_response(response, agent_id, default=None):
    # NOUVEAU: Validation stricte du résultat
    result = self._try_parse(json_str)

    if result:
        # Vérifier que les champs critiques sont intacts
        if not self._validate_critical_fields(result, original=json_str):
            logger.warning(f"JSON parsing may have corrupted content for {agent_id}")
            return default

    return result
```

---

### F7: Négociation Sans Timeout Adaptatif

**Localisation**: `core/swarm/negotiation_protocol.py`

**Problème**:
La négociation a un maximum fixe de 4 tours. Si les agents n'arrivent pas à un consensus, le mode par défaut est utilisé, même si un tour supplémentaire aurait suffi.

```python
class NegotiationProtocol:
    def __init__(self, max_turns=4, skip_trivial=True):
        # 4 tours fixes pour TOUTES les négociations
```

**Impact**:
- Négociations complexes interrompues prématurément
- Mode sous-optimal choisi par défaut
- Perte de l'intelligence collective

**Scénarios de Failure**:
1. Agents convergent au tour 5 → forcés en mode par défaut
2. Tâche EXPERT nécessite 6+ tours de négociation → timeout

**Mitigation Proposée**:
```python
class AdaptiveNegotiationProtocol:
    def __init__(self, complexity: TaskComplexity):
        # Tours adaptés à la complexité
        self.max_turns = {
            TaskComplexity.SIMPLE: 2,
            TaskComplexity.MODERATE: 4,
            TaskComplexity.COMPLEX: 6,
            TaskComplexity.EXPERT: 8
        }[complexity]

        # NOUVEAU: Extension si proche du consensus
        self.allow_extension = True
        self.extension_threshold = 0.7  # 70% consensus
```

---

### F8: CFL Validation Trop Permissive

**Localisation**: `core/orchestration/fsm_handlers.py:handle_validating_cfl()`

**Problème**:
La validation CFL utilise des mots-clés simples pour déterminer le succès:

```python
# Determine validation success
if "✓" in content or "success" in content.lower() or "successfully" in content.lower():
    validation_success = True
elif "✗" in content or "error" in content.lower() or "failed" in content.lower():
    validation_success = False
else:
    validation_success = True  # DEFAULT = SUCCESS !
```

**Impact**:
- Réponses ambiguës validées par défaut
- Erreurs subtiles non détectées
- Fausse confiance dans les résultats

**Scénarios de Failure**:
1. Agent dit "I tried but couldn't complete" → pas de mot-clé erreur → SUCCESS
2. "The operation completed but with warnings" → contient "completed" → SUCCESS malgré warnings

**Mitigation Proposée**:
```python
def _determine_validation_success(self, content: str, tool_result: Dict) -> Tuple[bool, float]:
    # 1. Keyword analysis (actuel)
    keyword_score = self._keyword_analysis(content)

    # 2. NOUVEAU: Semantic analysis
    semantic_score = self._semantic_validation(content, tool_result)

    # 3. NOUVEAU: Tool result verification
    tool_success = tool_result.get("success", False)

    # 4. Weighted decision
    final_score = (keyword_score * 0.3 + semantic_score * 0.4 + tool_success * 0.3)

    # 5. Require high confidence for success
    return final_score > 0.7, final_score
```

---

### F9: Session Bleeding Entre Tâches

**Localisation**: `core/drivers/gemini_driver_v7.py`, `core/swarm/session_manager.py`

**Problème**:
Le système utilise `--resume latest` pour Gemini, ce qui peut contaminer une nouvelle tâche avec le contexte de la précédente si l'isolation n'est pas parfaite.

```python
# V9.7.1: Session Isolation via HOME Spoofing
# Mais que se passe-t-il si le spoofing échoue ?
def get_isolated_env(self, task_id: str, role: str) -> Optional[Dict[str, str]]:
    try:
        return self.session_manager.get_isolated_env(task_id, role)
    except Exception:
        return None  # Fallback = PAS d'isolation !
```

**Impact**:
- Contexte de tâche A influence tâche B
- Hallucinations basées sur tâches précédentes
- Comportement non déterministe

**Scénarios de Failure**:
1. Tâche A: "Modifie auth.py" → Tâche B: Agent pense que auth.py existe déjà modifié
2. Tâche A: Échec avec erreur → Tâche B: Agent toujours en mode "erreur"

**Mitigation Proposée**:
```python
def get_isolated_env(self, task_id: str, role: str) -> Dict[str, str]:
    try:
        return self.session_manager.get_isolated_env(task_id, role)
    except Exception as e:
        # NOUVEAU: Forcer nouvelle session au lieu de fallback sans isolation
        logger.warning(f"Session isolation failed: {e}. Forcing new session.")
        self._force_new_session()
        return self._create_fresh_env(task_id, role)
```

---

### F10: HiveMind Checkpoint Recovery Incomplète

**Localisation**: `core/hive_mind/saga_manager.py`, `core/hive_mind/orchestrator.py`

**Problème**:
Le système de checkpoints (SagaManager) permet de reprendre après une interruption, mais la reprise ne restaure pas complètement l'état mental des agents.

```python
async def process_task(self, task: str, ...):
    # V8.4.4b: Initialize SagaManager for checkpoint/rollback
    if self.saga_enabled:
        self._saga = await SagaManager.resume_from(sagas_dir, task_id)
        if self._saga:
            logger.info(f"[Saga] Resumed: {task_id}")
            # MAIS: Les agents n'ont pas le contexte du raisonnement précédent !
```

**Impact**:
- Reprise après interruption perd le contexte de raisonnement
- Agents recommencent des analyses déjà faites
- Décisions incohérentes avec l'état pré-interruption

**Scénarios de Failure**:
1. Phase 2 (Debate) interrompue → Reprise → Agents refont Phase 1 mentalement
2. Phase 4 (Execution) interrompue → Reprise → Agent ne sait pas quels fichiers déjà modifiés

**Mitigation Proposée**:
```python
async def resume_from(cls, sagas_dir: Path, task_id: str):
    saga = cls._load_checkpoint(sagas_dir, task_id)

    if saga:
        # NOUVEAU: Restaurer le contexte complet
        saga.restore_agent_context()

        # Injecter un résumé de l'état pré-interruption
        saga.inject_recovery_context(
            f"[RECOVERY] Task was interrupted at phase {saga.last_phase}. "
            f"Previous context: {saga.get_context_summary()}"
        )

    return saga
```

---

## 3. Matrice de Criticité

| Faille | Sévérité | Probabilité | Impact | Score |
|--------|----------|-------------|--------|-------|
| F1 | HAUTE | Fréquent | Raisonnement incorrect | 8/10 |
| F2 | MOYENNE | Occasionnel | Réponses incomplètes | 6/10 |
| F3 | HAUTE | Fréquent | Pas de validation | 7/10 |
| F4 | CRITIQUE | Rare | État corrompu | 9/10 |
| F5 | MOYENNE | Occasionnel | Interruption prématurée | 5/10 |
| F6 | HAUTE | Fréquent | Données corrompues | 7/10 |
| F7 | MOYENNE | Occasionnel | Mode sous-optimal | 5/10 |
| F8 | HAUTE | Fréquent | Faux positifs | 7/10 |
| F9 | CRITIQUE | Rare | Non-déterminisme | 9/10 |
| F10 | HAUTE | Occasionnel | Perte de contexte | 7/10 |

---

## 4. Plan de Remédiation Prioritaire

### Phase 1 - Critique (Semaine 1-2)

1. **F4 - Race Condition PARALLEL**
   - Implémenter `ConflictAwareMergeStrategy`
   - Ajouter locking granulaire sur ressources partagées

2. **F9 - Session Bleeding**
   - Forcer nouvelle session en cas d'échec d'isolation
   - Ajouter tests d'isolation entre tâches

### Phase 2 - Haute (Semaine 3-4)

3. **F1 - Classification Complexité**
   - Ajouter analyse contextuelle du projet
   - Implémenter feedback loop sur classifications

4. **F3 - Single Agent Sans Fallback**
   - Ajouter light CFL pour mode SIMPLE
   - Seuil de confiance pour escalade automatique

5. **F6 - JSON Parsing**
   - Validation stricte post-parsing
   - Logging des transformations

6. **F8 - CFL Validation**
   - Semantic analysis en plus des keywords
   - Seuil de confiance explicite

### Phase 3 - Moyenne (Semaine 5-6)

7. **F2 - Fast Path Validation**
   - Détection des "incomplete indicators"
   - Escalade automatique si détecté

8. **F5 - Stagnation Detector**
   - Ajout du semantic progress
   - Seuils adaptatifs par complexité

9. **F7 - Négociation Timeout**
   - Tours adaptatifs à la complexité
   - Extension si proche du consensus

10. **F10 - Checkpoint Recovery**
    - Restauration complète du contexte agent
    - Injection du recovery context

---

## 5. Tests Recommandés

### Tests Unitaires

```python
# test_reasoning_failures.py

class TestF1_ComplexityClassification:
    def test_complex_task_not_trivial(self):
        """Bug fix in distributed system should not be TRIVIAL"""
        task = "Fix the race condition in the cache invalidation"
        analysis = TaskAnalyzer().analyze(task)
        assert analysis.complexity >= TaskComplexity.MODERATE

class TestF4_ParallelRaceCondition:
    def test_conflicting_actions_detected(self):
        """Conflicting agent actions should be detected"""
        outputs = [
            AgentResponse("gemini", "I deleted auth.py"),
            AgentResponse("claude", "I modified auth.py")
        ]
        merger = ConflictAwareMergeStrategy()
        result = merger.merge(outputs)
        assert result.has_conflicts

class TestF9_SessionIsolation:
    def test_no_context_bleeding(self):
        """Task B should not see Task A context"""
        # Execute Task A
        result_a = swarm.process_task("Modify file X")

        # Execute Task B (different session)
        result_b = swarm.process_task("Create file Y")

        # Task B should not reference file X
        assert "file X" not in result_b.final_output
```

### Tests d'Intégration

```python
class TestReasoningPipeline:
    def test_complex_task_full_pipeline(self):
        """Complex task should go through full reasoning pipeline"""
        task = "Refactor the authentication system to use JWT"

        # Should trigger MODERATE+ path
        result = orchestrator.process_turn(task)

        # Verify full pipeline was used
        assert "swarm" in result.get("pipeline_used", [])
        assert result["phases_completed"] >= 3

    def test_recovery_maintains_context(self):
        """Recovery after interrupt should maintain reasoning context"""
        task = "Implement caching layer"

        # Start task
        orchestrator.process_turn(task)

        # Simulate interrupt at Phase 3
        orchestrator.interrupt()

        # Resume
        result = orchestrator.resume()

        # Should have context from before interrupt
        assert "Phase 1" in result.get("context_summary", "")
        assert "Phase 2" in result.get("context_summary", "")
```

---

## 6. Conclusion

La branche NX a une architecture solide mais présente **10 failles de raisonnement** identifiées qui peuvent causer des échecs dans des scénarios réels:

1. **Classification incorrecte** des tâches (F1)
2. **Pas de validation** pour les tâches simples (F2, F3)
3. **Race conditions** en mode parallèle (F4)
4. **Détection de stagnation** trop agressive (F5)
5. **Parsing JSON** fragile (F6)
6. **Négociation** non adaptative (F7)
7. **Validation CFL** trop permissive (F8)
8. **Bleeding de session** possible (F9)
9. **Recovery** incomplète (F10)

Les failles F4 (Race Condition) et F9 (Session Bleeding) sont les plus critiques car elles peuvent causer des comportements non déterministes et des corruptions d'état.

**Recommandation**: Prioriser la remédiation des failles CRITIQUE (F4, F9) avant tout déploiement en production.

---

*Document généré par analyse statique du code - Branche NX*
*Classification: INTERNAL - Engineering Review*
