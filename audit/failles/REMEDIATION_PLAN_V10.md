# PLAN DE REMÉDIATION NEXUS V10 - FAILLES DE RAISONNEMENT

**Date:** 2025-12-15
**Version:** 1.0
**Auteur:** Claude (Opus 4.5)
**Basé sur:** REASONING_FAILURES_ANALYSIS_NX.md, REASONING_FAILURES_ANALYSIS_NX_2.md
**Contexte:** Préparation CEREBRO UI (React Flow + WebSocket)

---

## SYNTHÈSE EXÉCUTIVE

### Statistiques de Vérification

| Catégorie | Count | Failles |
|-----------|-------|---------|
| **CRITIQUE** | 5 | F8, F13, F14, F15, F12 |
| **HAUTE** | 5 | F1, F2, F6, F10, F11 |
| **MOYENNE** | 4 | F3, F4, F7, F9 |
| **SAFE/MITIGÉE** | 3 | F5, F16, F17 |

### Impact UI/CEREBRO

L'UI CEREBRO (React Flow + WebSocket) amplifie certaines vulnérabilités:
- **F12 (Context Overflow)**: WebSocket broadcast peut saturer le frontend
- **F9 (Session Bleeding)**: Multi-tenant UI = risque de fuite cross-tenant
- **F4 (Race Condition PARALLEL)**: Visualisation de conflits en temps réel
- **F15 (Hallucination Propagation)**: UI affiche des résultats non vérifiés

---

## FAILLES CONFIRMÉES (14)

### CRITIQUE (5) - Fix Immédiat Requis

#### F8: CFL Validation - Default to Success
**Fichier:** `core/orchestration/fsm_handlers.py:326-331`
**Problème:** Validation ambiguë = succès par défaut
```python
# ACTUEL (DANGEREUX)
else:
    validation_success = True  # DEFAULT = SUCCESS!

# CORRECTIF
else:
    validation_success = False  # DEFAULT = ÉCHEC (conservative)
    logger.warning("CFL validation ambiguous, defaulting to failure")
```
**Impact UI:** Les nœuds React Flow afficheront ✓ pour des tâches non validées
**Effort:** 1h | **Dépendances:** Aucune

---

#### F13: Verification Gaps - Keywords Only
**Fichier:** `core/swarm/task_completion_validator.py`
**Problème:** Validation par mots-clés sans vérification sémantique
```python
# ACTUEL
COMPLETION_KEYWORDS = {"finished", "done", "complete", "completed"}
has_completion_keyword = any(kw in response_lower for kw in self.COMPLETION_KEYWORDS)

# CORRECTIF - Ajout validation sémantique
async def validate_completion(self, response: str, task: str) -> ValidationResult:
    # 1. Keyword check (baseline)
    keyword_match = self._check_keywords(response)

    # 2. Semantic validation (LLM-based)
    semantic_score = await self._semantic_validation(response, task)

    # 3. Artifact verification (file existence)
    artifacts_verified = await self._verify_artifacts(response)

    # Require 2/3 validations
    return ValidationResult(
        is_complete=sum([keyword_match, semantic_score > 0.7, artifacts_verified]) >= 2,
        confidence=semantic_score,
        artifacts_checked=artifacts_verified
    )
```
**Impact UI:** Barre de progression affichera 100% pour tâches incomplètes
**Effort:** 4h | **Dépendances:** F15

---

#### F14: Termination Blindness
**Fichier:** `core/swarm/executors/ping_pong_executor.py`
**Problème:** `max_rounds` atteint = considéré comme "completed"
```python
# ACTUEL (DANGEREUX)
if current_round >= self.max_rounds:
    return ExecutionResult(status="completed", ...)

# CORRECTIF
if current_round >= self.max_rounds:
    return ExecutionResult(
        status="incomplete",  # NOT completed!
        metadata={"reason": "max_rounds_exceeded", "rounds": current_round}
    )
```
**Impact UI:** Edge animations montreront succès pour timeouts
**Effort:** 2h | **Dépendances:** Aucune

---

#### F15: Hallucination Propagation
**Fichier:** `core/hive_mind/phases/phase_execution.py:550-554`
**Problème:** `_verify_artifacts()` retourne toujours True
```python
# ACTUEL (STUB)
async def _verify_artifacts(self, artifacts: List[str]) -> bool:
    return self.tool_executor is not None  # ALWAYS TRUE!

# CORRECTIF
async def _verify_artifacts(self, artifacts: List[str]) -> Tuple[bool, List[str]]:
    """Verify artifacts actually exist."""
    verified = []
    failed = []

    for artifact in artifacts:
        if artifact.startswith("file:"):
            path = artifact[5:]
            if Path(path).exists():
                verified.append(artifact)
            else:
                failed.append(artifact)
        elif artifact.startswith("url:"):
            # TODO: HTTP HEAD check
            verified.append(artifact)  # Tentative

    return len(failed) == 0, failed
```
**Impact UI:** Nœuds afficheront des fichiers créés qui n'existent pas
**Effort:** 3h | **Dépendances:** Aucune

---

#### F12: Context Window Overflow
**Fichier:** `core/hive_mind/context_manager.py`
**Problème:** Items CRITICAL peuvent saturer le budget
```python
# CORRECTIF - Hard cap même pour CRITICAL
class ContextManager:
    CRITICAL_MAX_TOKENS = 2000  # Hard limit

    def add_critical(self, content: str) -> bool:
        tokens = self._count_tokens(content)
        if tokens > self.CRITICAL_MAX_TOKENS:
            content = self._truncate_to_tokens(content, self.CRITICAL_MAX_TOKENS)
            logger.warning(f"CRITICAL item truncated: {tokens} -> {self.CRITICAL_MAX_TOKENS}")
        return self._add(content, priority="CRITICAL")
```
**Impact UI:** WebSocket flood avec events trop larges, crash React
**Effort:** 2h | **Dépendances:** Aucune

---

### HAUTE (5) - Fix Cette Semaine

#### F1: Classification Complexity - Keywords Only
**Fichier:** `core/swarm/task_analyzer.py`
**Problème:** Classification par mots-clés sans contexte projet
```python
# CORRECTIF - Ajout analyse contextuelle
async def analyze_task(self, task: str, project_context: Optional[ProjectContext] = None) -> TaskAnalysis:
    # 1. Keyword baseline
    keyword_complexity = self._keyword_analysis(task)

    # 2. Project context boost
    if project_context:
        if self._involves_critical_files(task, project_context.critical_paths):
            keyword_complexity = max(keyword_complexity, Complexity.MODERATE)

    # 3. Historical patterns (SuccessMemory)
    similar_tasks = await self.memory.find_similar(task)
    if similar_tasks:
        avg_complexity = mean([t.actual_complexity for t in similar_tasks])
        keyword_complexity = (keyword_complexity + avg_complexity) / 2

    return TaskAnalysis(complexity=keyword_complexity, ...)
```
**Impact UI:** Tâches critiques routées vers Fast Path, UI affiche "Simple" pour tâche complexe
**Effort:** 4h | **Dépendances:** SuccessMemory

---

#### F2: Fast Path No Validation
**Fichier:** `core/orchestration/fsm_handlers.py`
**Problème:** TaskCompletionValidator jamais appelé pour Fast Path
```python
# CORRECTIF - Validation obligatoire
async def handle_fast_path(self, task: str) -> FSMResult:
    response = await self._execute_single_agent(task)

    # V10: Validation même pour Fast Path
    validator = TaskCompletionValidator()
    validation = await validator.validate(response, task)

    if not validation.is_complete:
        # Escalate to HiveMind
        return await self._escalate_to_hive_mind(task, response)

    return FSMResult(success=True, response=response)
```
**Impact UI:** Progress bar stuck at 100% sans validation réelle
**Effort:** 3h | **Dépendances:** F13

---

#### F6: JSON Parsing - Naive Quote Replacement
**Fichier:** `core/hive_mind/json_parser.py`
**Problème:** Remplacement `'` → `"` casse les strings
```python
# ACTUEL (CASSÉ)
content = content.replace("'", '"')

# CORRECTIF - Parser robuste
import re

def parse_json_safe(content: str) -> dict:
    """Parse JSON with fallback strategies."""
    # Strategy 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract JSON block
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 3: LLM repair (last resort)
    return await self._llm_json_repair(content)
```
**Impact UI:** Crash parsing des events WebSocket malformés
**Effort:** 3h | **Dépendances:** Aucune

---

#### F10: Checkpoint Recovery - No LLM Context
**Fichier:** `core/hive_mind/saga_manager.py`
**Problème:** Pas de restauration du contexte LLM
```python
# CORRECTIF - Contexte LLM dans checkpoint
@dataclass
class SagaCheckpoint:
    phase: str
    step: int
    data: Dict[str, Any]
    # V10: LLM context
    conversation_summary: str  # Compressed conversation
    agent_states: Dict[str, str]  # Per-agent state

async def restore_checkpoint(self, checkpoint: SagaCheckpoint) -> bool:
    # Restore phase/step
    self.current_phase = checkpoint.phase
    self.current_step = checkpoint.step

    # V10: Inject context summary into agents
    for agent_id, state in checkpoint.agent_states.items():
        await self._inject_context(agent_id, checkpoint.conversation_summary, state)

    return True
```
**Impact UI:** Reprise après crash = agents perdus, UI out of sync
**Effort:** 6h | **Dépendances:** Aucune

---

#### F11: Inter-Agent Misalignment
**Fichier:** `core/hive_mind/phases/phase_debate.py`
**Problème:** Pas de détection de désalignement
```python
# CORRECTIF - Misalignment detector
class MisalignmentDetector:
    PATTERNS = [
        r"I disagree but will proceed",  # Silent dissent
        r"ignoring.*input",  # Input dismissal
        r"already decided",  # Premature closure
    ]

    def detect(self, message: str, previous_context: str) -> List[MisalignmentFlag]:
        flags = []
        for pattern in self.PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                flags.append(MisalignmentFlag(
                    type="detected_pattern",
                    pattern=pattern,
                    severity="HIGH"
                ))
        return flags
```
**Impact UI:** Edges montrent collaboration mais agents en désaccord
**Effort:** 4h | **Dépendances:** Aucune

---

### MOYENNE (4) - Fix Ce Mois

#### F3: Single Agent No Fallback
**Fichier:** `core/orchestration/fsm_handlers.py`
**Problème:** Pas de CFL pour mode SIMPLE
**Correctif:** Ajouter CFL léger pour SIMPLE
**Effort:** 2h

#### F4: Race Condition PARALLEL
**Fichier:** `core/swarm/executors/parallel_executor.py`
**Problème:** Merge basique sans détection de conflits
**Correctif:** Conflict detection + resolution strategy
**Effort:** 4h

#### F7: Negotiation Timeout - Fixed 4 Turns
**Fichier:** `core/swarm/negotiation_protocol.py`
**Problème:** Max 4 tours non adaptatif
**Correctif:** Adaptive max_turns basé sur complexité
**Effort:** 2h

#### F9: Session Bleeding
**Fichier:** `core/swarm/session_manager.py`
**Problème:** HOME spoofing mitigé mais fallback silencieux
**Correctif:** Logging explicite + isolation workspace
**Effort:** 3h

---

## ANGLES MORTS IDENTIFIÉS

### B1: WebSocket Injection (UI-SPÉCIFIQUE)
**Risque:** Event malveillant injecté via WebSocket
**Impact:** XSS dans React Flow, exécution de code client
```python
# CORRECTIF dans api/websocket_handler.py
async def on_message(self, event: dict):
    # Sanitize ALL event payloads
    sanitized = self._sanitize_event(event)
    await self.broadcast(sanitized)

def _sanitize_event(self, event: dict) -> dict:
    """Remove potential XSS vectors."""
    if "content" in event:
        event["content"] = bleach.clean(event["content"])
    return event
```
**Effort:** 2h

### B2: Tenant Isolation WebSocket (UI-SPÉCIFIQUE)
**Risque:** Events d'un tenant visibles par un autre
**Impact:** Fuite de données confidentielles
```python
# CORRECTIF - Room isolation
class WebSocketManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}  # tenant_id -> connections

    async def broadcast_to_tenant(self, tenant_id: str, event: CerebroEvent):
        if tenant_id in self.rooms:
            for ws in self.rooms[tenant_id]:
                await ws.send_json(event.to_dict())
```
**Effort:** 3h

### B3: Rate Limiting WebSocket (UI-SPÉCIFIQUE)
**Risque:** Flood de messages WebSocket
**Impact:** DoS du backend, React freeze
```python
# CORRECTIF
class WebSocketRateLimiter:
    MAX_MESSAGES_PER_SECOND = 10

    async def check(self, connection_id: str) -> bool:
        now = time.time()
        count = self._get_count(connection_id, now)
        if count > self.MAX_MESSAGES_PER_SECOND:
            logger.warning(f"Rate limit exceeded: {connection_id}")
            return False
        return True
```
**Effort:** 2h

### B4: JWT Expiration Mid-Session
**Risque:** Token expire pendant session longue
**Impact:** WebSocket disconnecté, perte de travail
**Correctif:** Token refresh automatique + reconnection handler
**Effort:** 3h

### B5: Event Ordering Guarantee
**Risque:** Events WebSocket arrivent dans le désordre
**Impact:** React Flow affiche état incohérent
**Correctif:** Sequence numbers (déjà dans TelemetryBridge) + client-side reordering
**Effort:** 2h

---

## PLAN D'EXÉCUTION PRIORITISÉ

### Phase 1: CRITIQUE (Semaine 1)
| # | Faille | Fichier | Effort | Bloque UI? |
|---|--------|---------|--------|------------|
| 1 | F8 | fsm_handlers.py | 1h | OUI |
| 2 | F14 | ping_pong_executor.py | 2h | OUI |
| 3 | F15 | phase_execution.py | 3h | OUI |
| 4 | F12 | context_manager.py | 2h | OUI |
| 5 | B1 | websocket_handler.py | 2h | OUI |

**Total Phase 1:** 10h

### Phase 2: HAUTE (Semaine 2)
| # | Faille | Fichier | Effort | Bloque UI? |
|---|--------|---------|--------|------------|
| 6 | F13 | task_completion_validator.py | 4h | NON |
| 7 | F2 | fsm_handlers.py | 3h | NON |
| 8 | F6 | json_parser.py | 3h | OUI |
| 9 | B2 | websocket_manager.py | 3h | OUI |
| 10 | B3 | websocket_rate_limiter.py | 2h | OUI |

**Total Phase 2:** 15h

### Phase 3: MOYENNE + BLINDSPOTS (Semaine 3)
| # | Faille | Fichier | Effort |
|---|--------|---------|--------|
| 11 | F1 | task_analyzer.py | 4h |
| 12 | F10 | saga_manager.py | 6h |
| 13 | F11 | phase_debate.py | 4h |
| 14 | F3-F4-F7-F9 | Various | 11h |
| 15 | B4-B5 | JWT + Ordering | 5h |

**Total Phase 3:** 30h

---

## MÉTRIQUES DE VALIDATION

### Tests Requis
```bash
# Après chaque fix
pytest tests/v10/test_remediation_fXX.py -v

# Regression complète
pytest tests/ -v --cov=core

# UI Integration (si applicable)
npm run test:e2e --spec=cerebro-security
```

### Critères de Succès
- [ ] Tous les tests CRITIQUE passent
- [ ] Couverture > 80% sur fichiers modifiés
- [ ] Zero crash WebSocket sous load test (100 msg/s)
- [ ] Tenant isolation vérifié (pentest manuel)
- [ ] No XSS vectors dans événements

---

## RÉFÉRENCES

- MASFT Taxonomy (Berkeley): 14 failure modes, 3 categories
- NEXUS Audit V1: `audit/failles/REASONING_FAILURES_ANALYSIS_NX.md`
- NEXUS Audit V2: `audit/failles/REASONING_FAILURES_ANALYSIS_NX_2.md`
- CEREBRO Genesis: `tests/v10/test_cerebro.py`
- TelemetryBridge: `core/events/telemetry_bridge.py`
