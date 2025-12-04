# ROADMAP NEXUS V7.5 "HIVE MIND"

**Version**: 7.5.6 | **Status**: Active | **Last Updated**: 2025-12-04
**Vision**: Cœur d'Intelligence Collaborative Générant des Agents Spécialisés
**Analyse Croisée**: Gemini + Claude collaboration (2025-12-04)
**Étude d'Impact**: Workspace & Blackboard Analysis (2025-12-04)

---

## 1. Vision Stratégique

**NEXUS n'est plus une quête vers l'ASI.**
NEXUS est une **plateforme de collaboration multi-agents** capable de:
1. **Analyser** les besoins complexes
2. **Générer** des agents spécialisés (enfants qui coexistent)
3. **Orchestrer** leur collaboration via Hybrid Swarm
4. **Évoluer** par sélection des meilleures configurations

### Coeur de Puissance
```
GEMINI 3 Pro  <═══════════════>  CLAUDE Opus 4.5
     │           SYMBIOSE            │
     │         COGNITIVE             │
     └──────────────┬────────────────┘
                    │
            6 MODES SWARM
     PARALLEL │ SEQUENTIAL │ LEAD_SUPPORT
     PING_PONG │ SPECIALIST │ RED_BLUE
                    │
            SPAWNED AGENTS
     Spécialistes générés et orchestrés
```

---

## 1.1 Analyse Croisée Gemini + Claude (2025-12-04)

> **Méthode**: Gemini et Claude ont analysé indépendamment la roadmap et la codebase,
> puis leurs conclusions ont été fusionnées. Cette section documente les convergences
> et les idées uniques de chaque agent.

### Convergences Validées (Consensus)

| Point | Gemini | Claude | Statut |
|-------|--------|--------|--------|
| Phase 7 = CRITIQUE (Priorité #1) | ✅ "Socle de tout le reste" | ✅ "Priorité #1" | **CONSENSUS** |
| Mapping Task+Role→UUID | ✅ "Registry Intelligent" | ✅ Proposé identique | **CONSENSUS** |
| Phase 5b = Bloquant | ✅ "Agent Factory bloquée" | ✅ "Hardcoded lookups" | **CONSENSUS** |
| Shared Memory Files | ✅ "Fichiers > JSON prompt" | ✅ "Protocole 2" | **CONSENSUS** |
| Agent-as-Tool | ✅ "Architecture Fractale" | ✅ "Phase 12.4" | **CONSENSUS** |
| Cleanup Sessions | ✅ "Saturation ~/.gemini/tmp" | ✅ "session_retention_hours" | **CONSENSUS** |

### Idées Uniques Gemini 🤖

| Idée | Description | Phase Cible |
|------|-------------|-------------|
| **Mode EPHEMERAL** | Sessions one-shot sans persistence pour tâches triviales | Phase 7 |
| **Checkpointing** | Snapshot état avant exécution pour retry propre | Phase 8 |
| **Dynamic Tool Generation** | Scripts Python jetables générés à la volée | Phase 12.5 |
| **Économie de Tokens** | Fichiers Markdown > JSON dans prompt système | Phase 7 |
| **Debuggabilité Humaine** | Shared Memory lisible par humain | Phase 7 |

### Idées Uniques Claude 🧠

| Idée | Description | Phase Cible |
|------|-------------|-------------|
| **Spawned Agent Session Persistence** | UUID persistant dans BIRTH_CERTIFICATE.json | Phase 7 |
| **Session Metrics pour DyLAN** | Tracker succès par type de session | Phase 10 |
| **Hot-Swap Lead Agent** | Handover mid-execution si stagnation détectée | Phase 8 |
| **Session Branching PARALLEL** | `--fork-session` Claude pour branches isolées | Phase 7 |

### Fusion des Idées → SessionMode Enrichi

```python
class SessionMode(Enum):
    """Modes de session unifiés (Gemini + Claude analysis)"""
    FRESH = "fresh"           # Nouvelle session, pas de resume
    CONTINUE = "continue"     # Resume session existante (brainstorm)
    BRANCH = "branch"         # Fork depuis parent (Claude --fork-session)
    EPHEMERAL = "ephemeral"   # ⬅️ GEMINI: One-shot, PAS de persistence
```

---

## 1.2 Étude d'Impact: Workspace & Blackboard (2025-12-04)

> **Méthode**: Analyse approfondie des modules `memory_v7.py`, `auto_memory.py`, `blackboard.json`
> par Gemini et Claude indépendamment, puis fusion des découvertes critiques.

### Fragilités Identifiées

| Problème | Fichier | Ligne(s) | Impact | Priorité |
|----------|---------|----------|--------|----------|
| **Race Condition** | `memory_v7.py` | 149-153 | PARALLEL mode = corruption | 🔴 CRITIQUE |
| **Single Blackboard** | `orchestration_v7.py` | - | Context bleeding inter-tâches | 🔴 CRITIQUE |
| **Non-Atomic Writes** | `memory_v7.py` | 166-172 | Corruption JSON si crash | 🟠 HAUTE |
| **Schema Outdated** | `blackboard.json` | - | Version 6.0.0 vs 7.5 | 🟡 MOYENNE |
| **Magic Numbers** | `memory_v7.py` | - | Hardcodés, non configurables | 🟡 MOYENNE |
| **Compression CLI** | `memory_v7.py` | 200+ | Dépend Claude CLI externe | 🟡 MOYENNE |

### Détail: Race Condition (CRITIQUE)

**Code problématique** (`memory_v7.py:149-153`):
```python
def add_to_history(self, message: Dict):
    self.blackboard["recent_history"].append(message)  # ❌ Non thread-safe
    if len(self.blackboard["recent_history"]) > 50:
        self.blackboard["recent_history"] = self.blackboard["recent_history"][-50:]
```

**Scénario de corruption**:
```
Thread 1 (Gemini):  read len() = 49 → append → len = 50
Thread 2 (Claude):  read len() = 49 → append → len = 50
                    ❌ Deux appends simultanés = 51 éléments
                    ❌ Ou pire: list modification during iteration
```

**Solution**: `threading.RLock()` autour des opérations blackboard
```python
from threading import RLock

class MemoryManagerV7:
    def __init__(self):
        self._lock = RLock()
        # ...

    def add_to_history(self, message: Dict):
        with self._lock:
            self.blackboard["recent_history"].append(message)
            if len(self.blackboard["recent_history"]) > 50:
                self.blackboard["recent_history"] = self.blackboard["recent_history"][-50:]
```

### Détail: Atomic Writes (Gemini Pattern)

**Problème**: Un crash pendant `json.dump()` = fichier corrompu

**Solution Write-Replace** (Gemini proposal):
```python
def save_atomic(filepath: Path, data: dict) -> None:
    """Écriture atomique: write temp → fsync → rename"""
    temp_path = filepath.with_suffix('.tmp')

    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())  # Force write to disk

    os.replace(temp_path, filepath)  # Atomic on POSIX & Windows
```

**Intégration**: Wrapper `AtomicJsonStore` pour tous les fichiers JSON critiques

### Détail: TaskScopedBlackboard (Claude Pattern)

**Problème**: Un seul blackboard partagé = context bleeding

**Solution**: Wrapper par tâche avec isolation
```python
class TaskScopedBlackboard:
    """Blackboard isolé par tâche Swarm"""

    def __init__(self, parent: 'MemoryManagerV7', task_id: str):
        self.task_id = task_id
        self._parent = parent
        self._lock = RLock()
        self._state = {
            "objective": "",
            "history": [],
            "iteration": 0,
            "created_at": datetime.utcnow().isoformat()
        }

    def add_to_history(self, message: Dict):
        with self._lock:
            self._state["history"].append(message)
            # Pas de limite: la tâche a sa propre histoire isolée

    def merge_to_parent(self, summary: str):
        """Merge résumé vers blackboard global après complétion"""
        self._parent.add_task_summary(self.task_id, summary)
```

### Bonnes Pratiques Découvertes

| Pattern | Source | Description | Adoption |
|---------|--------|-------------|----------|
| **JSONL Append-Only** | `auto_memory.py` | Logs événements sans réécriture | ✅ Existant |
| **Backup System** | `memory_v7.py` | Backup avant modification | ✅ Existant |
| **Tiktoken Counting** | `auto_memory.py` | Comptage tokens précis | ✅ Existant |
| **Global Memory** | `auto_memory.py` | Partage cross-session | ⚠️ Pas intégré blackboard |

### Fonctionnalités Dormantes Découvertes (Gemini)

| Feature | Fichier | État | Potentiel |
|---------|---------|------|-----------|
| **Graph of Thought (GoT)** | `hybrid_swarm_engine.py` | Import mort | Phase 13 |
| **/workspace commands** | `repl.py` | Commenté | Réactivation facile |
| **Telemetry Hooks** | `config.py` | Config existe | Export externe |
| **suggest_mode()** | `auto_memory.py` | Implémenté | Pas appelé |
| **suggest_lead()** | `auto_memory.py` | Implémenté | Pas appelé |

### Décisions Architecturales

| Décision | Choix | Raison |
|----------|-------|--------|
| **Concurrence** | `RLock()` | Plus simple que SQLite, suffisant pour 2-5 agents |
| **Atomic Writes** | Write-Replace | Standard industrie, cross-platform |
| **Isolation** | TaskScopedBlackboard | Évite refactoring massif de MemoryManagerV7 |
| **Schema Migration** | Auto-upgrade | Lire 6.0.0 → écrire 7.5.0 automatiquement |
| **Cold Storage** | Avant compression | Garder raw history pour debug/audit |
| **Global Registry** | `~/.nexus/` | Cross-workspace, pattern Google ADK |

---

## 2. Phases Complétées (V7.0 → V7.5)

### Phase 1: Activation Swarm ✅
- [x] Commandes `/swarm`, `/swarm-status` ajoutées
- [x] `swarm_auto_route=True` par défaut (MODERATE+ tasks)
- [x] 6 modes de collaboration fonctionnels

### Phase 2: Refonte Vision ✅
- [x] MISSION.md réécrit (exit ASI → Cœur Collaboratif)
- [x] CLAUDE.md mis à jour (Agent Factory Mission)
- [x] GEMINI.md mis à jour (Agent Factory Mission)
- [x] KERNEL.py: OBJECTIVE et IMMUTABILITY_RULE mis à jour
- [x] INVARIANTS.md sections 3 & 4 réécrites

### Phase 3: Déblocage Évolution ✅
- [x] Red Team optionnel (`RED_TEAM_MANDATORY=False`)
- [x] Seuil abaissé à 0.60 (était 0.80)

### Phase 4: Architecture FSM ✅
- [x] États SWARM_* documentés comme [RESERVED]
- [x] Swarm fonctionne via `process_with_swarm()` (bypass FSM)

### Phase 5: Agent Factory ✅ (Complétée 2025-12-03)
- [x] `/spawn <role>` créé agents dans `workspace/agents/`
- [x] `/agents` liste les agents spawnés
- [x] `SpawnedAgentLoader` - Discovery au startup (`core/bootstrap/agent_loader.py`)
- [x] `get_spawned_agents()` / `get_internal_agents()` dans AgentPool
- [x] `_invoke_spawned_agent()` - Invocation avec system_prompt.md
- [x] `_find_best_spawned_specialist()` - Sélection SPECIALIST pour agents spawned
- [x] Agents spawned = citoyens de première classe dans le Swarm

### Phase 6: Robustesse JSON ✅
- [x] `core/utils/json_extractor.py` implémenté
- [x] Intégré dans Gemini driver et REPL
- [x] Support multi-format (markers, markdown, braces)

### Phase 7: Task Fitness (ex-ASI) ✅
- [x] Suppression benchmarks simulés
- [x] Implémentation scores baseline honnêtes
- [x] Terminologie ASI → Task Fitness dans tout le code

---

## 3. Phases Prioritaires (V7.5.3 → V7.6)

### Phase 5b: N-Agent Agnosticism Complet [Priorité: CRITIQUE]
**Objectif**: Agents spawned utilisables dans TOUS les 6 modes Swarm
**Effort**: 2-3 jours
**Source**: Analyse architecturale Gemini (2025-12-03)

> **Contexte**: Phase 5 a ajouté support spawned pour SPECIALIST uniquement.
> Les 5 autres modes (PARALLEL, SEQUENTIAL, LEAD_SUPPORT, PING_PONG, RED_BLUE)
> utilisent encore des lookups hardcodés `gemini`/`claude`.

**Problème actuel** (`mode_selector.py` lignes 304-305):
```python
gemini = next((a for a in agents if "gemini" in a.agent_id.lower()), None)
claude = next((a for a in agents if "claude" in a.agent_id.lower()), None)
```

**Solution**:
- [ ] Refactorer `_assign_agents()` pour utiliser `AgentPool.select_best_for_task(domain)`
- [ ] Supprimer lookups hardcodés gemini/claude
- [ ] Sélection basée sur `AgentProfile.capabilities` + scores DyLAN
- [ ] Permettre spawned agents comme LEAD dans LEAD_SUPPORT
- [ ] Permettre spawned agents dans PARALLEL (split par compétence)
- [ ] Tests: spawned agent prend le lead sur tâche de son domaine

### Phase 8: Self-Healing Swarm [Priorité: HAUTE]
**Objectif**: Fallback automatique de MODE en cas d'échec
**Effort**: 3-4 jours
**Source**: Analyse architecturale Gemini (2025-12-03) + [AWS Strands Patterns](https://aws.amazon.com/blogs/machine-learning/multi-agent-collaboration-patterns-with-strands-agents-and-amazon-nova/)
**Enrichi**: Gemini+Claude collab (2025-12-04) - Checkpointing + Hot-Swap

> **Contexte industrie**: "Graceful degradation from complex to simple patterns" est un
> best practice validé (AWS, IEEE). NEXUS a un failover AGENT mais pas de failover MODE.

**Problème actuel**: Si PARALLEL échoue, l'exécution est marquée FAILED. Pas de retry.

**Solution**:
- [ ] `ModeExecutor.recover_with_fallback()` - méthode abstraite
- [ ] Matrice de fallback:
  ```
  PARALLEL     → SEQUENTIAL (si merge échoue)
  RED_BLUE     → LEAD_SUPPORT (si adversarial timeout)
  LEAD_SUPPORT → SPECIALIST (si support non-réactif)
  ```
- [ ] `ExecutionStatus.RECOVERED` - nouveau status
- [ ] Métadonnées de bascule dans `ExecutionResult`
- [ ] Log: "Mode PARALLEL échoué, fallback SEQUENTIAL... Succès"
- [ ] Config: `swarm_fallback_enabled=True` (désactivable)

#### Checkpointing avant Fallback (Gemini proposal 2025-12-04)

> **Problème identifié par Gemini**: Si l'état est corrompu au moment du fallback,
> le retry échouera aussi. Solution: Checkpoint AVANT exécution.

**Extension SwarmSessionManager**:
```python
class SwarmSessionManager:
    # ... existing methods ...

    def create_checkpoint(self, task_id: str) -> str:
        """Snapshot état avant exécution risquée"""
        checkpoint_id = f"checkpoint_{task_id}_{int(time.time())}"
        task = self._registry["tasks"].get(task_id, {})
        self._registry["checkpoints"][checkpoint_id] = {
            "task_state": copy.deepcopy(task),
            "created_at": datetime.utcnow().isoformat()
        }
        self._persist_registry()
        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore état depuis checkpoint (pour retry propre)"""
        checkpoint = self._registry["checkpoints"].get(checkpoint_id)
        if checkpoint:
            task_id = checkpoint["task_state"].get("task_id")
            self._registry["tasks"][task_id] = checkpoint["task_state"]
            self._persist_registry()
            return True
        return False
```

**Utilisation dans ModeExecutor**:
```python
def execute_with_fallback(self, context: ExecutionContext) -> ExecutionResult:
    # CHECKPOINT avant exécution (Gemini proposal)
    checkpoint = self.session_manager.create_checkpoint(context.task_id)

    try:
        return self.execute(context)
    except ExecutionError as e:
        # RESTORE checkpoint avant fallback (état propre)
        self.session_manager.restore_checkpoint(checkpoint)

        fallback_mode = self.get_fallback_mode()
        if fallback_mode:
            fallback_executor = get_executor(fallback_mode)
            result = fallback_executor.execute(context)
            result.status = ExecutionStatus.RECOVERED
            result.recovery_metadata = {
                "original_mode": self.mode.value,
                "fallback_mode": fallback_mode.value,
                "checkpoint_used": checkpoint
            }
            return result
        raise
```

#### Hot-Swap Lead Agent (Claude proposal 2025-12-04)

> **Concept**: Si le lead agent stagne, handover dynamique au support
> qui devient le nouveau lead avec le contexte accumulé.

**Détection de stagnation mid-execution**:
```python
def check_lead_stagnation(self, context: ExecutionContext) -> bool:
    """Détecte si le lead agent est bloqué"""
    recent_outputs = context.get_recent_outputs(limit=3)

    # Heuristiques de stagnation
    if len(recent_outputs) >= 3:
        # 1. Répétition du même contenu
        if all(o.content == recent_outputs[0].content for o in recent_outputs):
            return True
        # 2. Outputs vides ou erreurs consécutives
        if all(o.status == "error" for o in recent_outputs):
            return True

    return False

def hot_swap_lead(self, context: ExecutionContext) -> None:
    """Échange lead/support avec handover de contexte"""
    # 1. Résumer le contexte du lead actuel
    summary = self.summarize_context(context.lead_outputs)

    # 2. Handover vers le nouveau lead
    self.session_manager.context_handover(
        task_id=context.task_id,
        from_role="lead",
        to_role="lead",  # Le support devient lead
        summary=summary
    )

    # 3. Swap les agents
    context.lead_agent, context.support_agent = context.support_agent, context.lead_agent

    logger.info(f"[HOT-SWAP] Lead changé: {context.support_agent.id} → {context.lead_agent.id}")
```

#### Panic → Recovery Transformation (Impact Study 2025-12-04)

> **Découverte**: L'état PANIC actuel est un "cul-de-sac" - l'utilisateur doit
> redémarrer manuellement. Avec les nouveaux patterns de data integrity,
> PANIC peut devenir un état de récupération automatique.

**État actuel du FSM**:
```
ERROR → (manual reset) → IDLE
PANIC → (restart required) → IDLE
```

**État cible**:
```
ERROR → (auto-recovery) → IDLE
PANIC → (cold restart + checkpoint restore) → IDLE
```

**Implémentation Recovery Manager**:
```python
# core/fsm/recovery_manager.py
class RecoveryManager:
    """Gère la récupération automatique des états d'erreur"""

    def __init__(self, memory: MemoryManagerV7, session_manager: SwarmSessionManager):
        self.memory = memory
        self.session_manager = session_manager

    def attempt_recovery(self, error_state: FSMState, exception: Exception) -> RecoveryResult:
        """Tente une récupération automatique"""

        if error_state == FSMState.ERROR:
            # Erreur légère: reset blackboard de tâche
            return self._recover_from_error(exception)

        elif error_state == FSMState.PANIC:
            # Erreur grave: cold restart avec checkpoint
            return self._recover_from_panic(exception)

    def _recover_from_error(self, exception: Exception) -> RecoveryResult:
        """Récupération d'erreur légère"""
        # 1. Sauvegarder l'état actuel pour debug
        self.memory.save_error_snapshot(exception)

        # 2. Clear le blackboard de la tâche en cours
        current_task = self.memory.get_current_task_id()
        if current_task:
            self.memory.clear_task_blackboard(current_task)

        # 3. Retourner à IDLE
        return RecoveryResult(
            success=True,
            new_state=FSMState.IDLE,
            message="Recovered from error, task blackboard cleared"
        )

    def _recover_from_panic(self, exception: Exception) -> RecoveryResult:
        """Récupération d'erreur grave (PANIC)"""
        # 1. Sauvegarder tout pour analyse
        self.memory.save_panic_snapshot(exception)

        # 2. Chercher le dernier checkpoint valide
        checkpoint = self.session_manager.get_latest_valid_checkpoint()

        if checkpoint:
            # 3a. Restore depuis checkpoint
            self.session_manager.restore_checkpoint(checkpoint)
            return RecoveryResult(
                success=True,
                new_state=FSMState.IDLE,
                message=f"Recovered from panic via checkpoint {checkpoint}"
            )
        else:
            # 3b. Cold restart: clear everything
            self.memory.cold_restart()
            return RecoveryResult(
                success=True,
                new_state=FSMState.IDLE,
                message="Recovered from panic via cold restart"
            )
```

**Intégration FSM**:
```python
# core/orchestration_v7.py
def handle_state_transition(self, from_state: FSMState, to_state: FSMState):
    if to_state in [FSMState.ERROR, FSMState.PANIC]:
        recovery_result = self.recovery_manager.attempt_recovery(to_state, self.last_exception)
        if recovery_result.success:
            logger.info(f"[RECOVERY] {recovery_result.message}")
            return recovery_result.new_state
    return to_state
```

#### Cold Storage avant Compression (Impact Study 2025-12-04)

> **Découverte**: La compression actuelle est IRRÉVERSIBLE. L'historique brut
> est perdu. Pour debug/audit, il faut un "cold storage" avant compression.

**Pattern Journal + Snapshot** (Gemini proposal):
```
workspace/.nexus/
├── blackboard.json           ← État courant (hot)
├── events.jsonl              ← Journal append-only (warm)
└── cold_storage/             ← Archives brutes (cold)
    ├── 2025-12-04_pre_compress.json
    └── 2025-12-03_pre_compress.json
```

**Implémentation**:
```python
# core/synapse/memory_v7.py
def compress_history(self) -> None:
    """Compresse l'historique avec cold storage préalable"""

    # 1. COLD STORAGE: Sauvegarder raw history AVANT compression
    cold_path = self.cold_storage_dir / f"{date.today()}_pre_compress.json"
    self._save_atomic(cold_path, {
        "raw_history": self.blackboard["recent_history"],
        "compressed_at": datetime.utcnow().isoformat(),
        "token_count": self._count_tokens(self.blackboard["recent_history"])
    })

    # 2. Compression (existing logic)
    summary = self._compress_with_llm(self.blackboard["recent_history"])
    self.blackboard["compressed_history_summary"] = summary
    self.blackboard["recent_history"] = []

    # 3. Cleanup old cold storage (> 7 days)
    self._cleanup_cold_storage(retention_days=7)
```

**Avantages**:
- Debug: "Qu'est-ce que l'agent a vraiment dit avant compression?"
- Audit: Traçabilité complète des décisions
- Recovery: Reconstruire état depuis cold storage si nécessaire

### Phase 9: Fast Path (UX) ⚡ [Priorité: HAUTE]
**Objectif**: Réponses instantanées pour requêtes triviales
**Effort**: 2-3 jours

> **Contexte**: TaskAnalyzer détecte déjà TRIVIAL, mais le FSM traite quand même.
> Fast Path = court-circuiter FSM + Swarm pour réponses < 2s.

**Implémentation** (`core/orchestration_v7.py`):
```python
def process_turn(self, user_input: str):
    # FAST PATH: Trivial inputs bypass FSM entirely
    if self._is_fast_path_eligible(user_input):
        return self._fast_path_response(user_input)
    # ... existing FSM logic
```

**Solution**:
- [ ] `_is_fast_path_eligible()` - Regex patterns pour greetings, thanks, confirmations
- [ ] `_fast_path_response()` - Single-agent response (Claude Haiku ou Gemini Flash)
- [ ] Patterns détectés:
  ```python
  FAST_PATH_PATTERNS = [
      r"^(hello|hi|bonjour|salut|hey)\b",
      r"^(merci|thanks|thank you|thx)\b",
      r"^(ok|oui|yes|non|no|d'accord)\b",
      r"^(quit|exit|bye|au revoir)\b",
  ]
  ```
- [ ] Config: `fast_path_enabled=True` (désactivable)
- [ ] Métrique: Temps de réponse < 2s pour patterns matchés

### Phase 7: Session Isolation & Context Management [Priorité: CRITIQUE]
**Objectif**: Isolation des contextes pour exécution parallèle multi-agents
**Effort**: 3-4 jours
**Source**: Bug context bleeding (2025-12-03) + [Google ADK Parallel Agents](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/) + [Microsoft MCP Patterns](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/orchestrating-multi-agent-intelligence-mcp-driven-patterns-in-agent-framework/4462150)

> **Problème actuel**: `--resume latest` cause un "context bleeding" entre tâches Swarm.
> Task 2 reçoit le contexte de Task 1, causant confusion et mauvaise analyse.
>
> **Contexte industrie**: "Independent Branches: Sub-agents operate in isolated execution
> paths with no automatic sharing of conversation history" (Google ADK)

#### Résultats Tests CLI (2025-12-04)

| Méthode | Commande | Résultat |
|---------|----------|----------|
| `--resume latest` | `gemini --resume latest` | ✅ Fonctionne (mais context bleeding) |
| `--resume <index>` | `gemini --resume 1` | ✅ Fonctionne - session resumée |
| `--resume <UUID>` (pipe) | `echo "..." \| gemini --resume UUID` | ❌ Hang (mode interactif) |
| `--resume <UUID>` + `-p` | `gemini --resume UUID -p "prompt"` | ✅ **FONCTIONNE !** |

> **CORRECTION (Gemini + Claude collab)**: Le resume par UUID **FONCTIONNE** avec le flag `-p`.
> Le test initial échouait car `echo | gemini` force le mode interactif.
> Solution: Toujours utiliser `-p "prompt"` pour le mode non-interactif.

**Architecture Session Management**:
```
~/.gemini/tmp/<project_hash>/chats/
├── <session-uuid-1>.json  ← Task: "Analyse core/swarm"
├── <session-uuid-2>.json  ← Task: "Fibonacci function"
└── <session-uuid-3>.json  ← Agent: sql_expert parallel work

gemini --list-sessions →
  1. Session Title [uuid-1]  ← Index = 1
  2. Session Title [uuid-2]  ← Index = 2
```

**Stratégie d'isolation VALIDÉE** (collaboration Gemini+Claude 2025-12-04):

**Option B: UUID-Based Resume (RECOMMANDÉE) ✅**

**Architecture Session Registry** (Gemini proposal 2025-12-04):
```json
// workspace/.nexus/session_registry.json
{
  "tasks": {
    "task_fibonacci_abc123": {
      "status": "active",
      "created_at": "2025-12-04T10:30:00Z",
      "swarm_mode": "LEAD_SUPPORT",
      "roles": {
        "lead_developer": {
          "agent_id": "gemini_pro",
          "session_uuid": "uuid-aaa-bbb-ccc",
          "context_summary": "Lead dev implementing Fibonacci"
        },
        "reviewer": {
          "agent_id": "claude_sonnet",
          "session_uuid": "uuid-ddd-eee-fff",
          "context_summary": "Code reviewer for Fibonacci"
        }
      }
    }
  }
}
```

**Mapping clé**: `Task + Role → UUID` (pas juste `Task → UUID`)

```python
class SwarmSessionManager:
    """Gestionnaire de sessions structuré par Tâche + Rôle"""

    def __init__(self, workspace: Path):
        self.registry_path = workspace / ".nexus" / "session_registry.json"
        self._registry: Dict = {"tasks": {}}
        self._load_registry()

    def get_or_create_session(
        self, task_id: str, role: str, agent_id: str
    ) -> str:
        """Récupère session existante ou en crée une nouvelle pour ce rôle"""
        if task_id not in self._registry["tasks"]:
            self._registry["tasks"][task_id] = {
                "status": "active",
                "roles": {}
            }

        roles = self._registry["tasks"][task_id]["roles"]
        if role not in roles:
            roles[role] = {
                "agent_id": agent_id,
                "session_uuid": str(uuid.uuid4()),
                "context_summary": f"{role} for task {task_id}"
            }
            self._persist_registry()

        return roles[role]["session_uuid"]

    def context_handover(
        self, task_id: str, from_role: str, to_role: str, summary: str
    ) -> None:
        """Passage de témoin entre rôles (quand architecture change)"""
        # Stocke le résumé du contexte pour injection dans le nouveau rôle
        task = self._registry["tasks"][task_id]
        task["handovers"] = task.get("handovers", [])
        task["handovers"].append({
            "from": from_role,
            "to": to_role,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._persist_registry()
```

**Risques évités** (Gemini analysis):
- ❌ **Amnésie**: On recrée un cerveau vide alors qu'on avait besoin du contexte
- ❌ **Schizophrénie**: On réutilise le cerveau du "chercheur" pour du "codage"
- ✅ **Solution**: Mapping `Task + Role → UUID` + Context Handover

→ Avantage: Isolation parfaite + Continuité multi-tour par rôle
→ Avantage: Changement d'architecture sans perte de contexte
→ Avantage: Agents parallèles avec "cerveau" persistant isolé par rôle

**Option A: FRESH Mode (Fallback simple)**
```python
def get_resume_args(self, context: str) -> List[str]:
    if context == "BRAINSTORM":
        return ["--resume", "latest"]  # Continuité conversation
    elif context == "SWARM_TASK":
        return []  # Nouvelle session = isolation
    return []
```
→ Utilisé si UUID non disponible (fallback)

**Décision: Option B (UUID-Based) pour V7.5.4**
- Isolation parfaite via UUID unique par tâche
- Continuité multi-tour préservée
- Agents parallèles avec "cerveau" persistant isolé

#### Architecture Asymétrique Claude vs Gemini (Gemini research 2025-12-04)

| Fonctionnalité | Gemini CLI | Claude Code CLI | Verdict |
|----------------|------------|-----------------|---------|
| Session ID | UUID généré par CLI | `--session-id <uuid>` imposable | Claude 🏆 |
| Forking | Non natif | `--fork-session` (branche!) | Claude 🏆 |
| Multi-Agent | Non natif | `--agents <json>` (expérimental) | Claude 🏆 |
| Headless | `-p` | `-p` ou `--print` | Égalité |
| Output JSON | `-o json` | `--output-format json` | Égalité |

**Implémentation** (`core/drivers/gemini_driver_v7.py`):
- [ ] Ajouter paramètre `session_uuid: Optional[str] = None`
- [ ] Si `session_uuid` fourni → `--resume {session_uuid} -p "{prompt}"`
- [ ] Si non fourni + brainstorm → `--resume latest`
- [ ] **IMPORTANT**: Toujours utiliser `-p` pour mode non-interactif
- [ ] Context handover = réinjection manuelle du résumé

**Implémentation** (`core/drivers/claude_driver_v7.py`) [NOUVEAU]:
- [ ] Ajouter paramètre `session_uuid: Optional[str] = None`
- [ ] NEXUS génère l'UUID → `--session-id {uuid}` (imposé!)
- [ ] Fork natif: `--resume {parent_uuid} --fork-session`
- [ ] Mode BRANCH = fork depuis parent (isolation parfaite)
- [ ] `-p` pour mode non-interactif

**Stratégie par Driver**:
```python
# GEMINI: UUID généré par CLI, stocké par NEXUS
gemini --resume {cli_generated_uuid} -p "{prompt}"

# CLAUDE: UUID imposé par NEXUS, fork natif
claude --session-id {nexus_generated_uuid} -p "{prompt}"
# OU pour fork:
claude --resume {parent_uuid} --fork-session -p "{prompt}"
```

**Implémentation** (`core/swarm/hybrid_swarm_engine.py`):
- [ ] Générer `task_id` unique au début de `process_task()`
- [ ] Passer `task_id` + `role` au SessionManager
- [ ] Adapter appel selon driver (Gemini vs Claude)
- [ ] `reset()` nettoie aussi le session manager

**Modes de session** (enrichi Gemini+Claude 2025-12-04):
| Mode | Comportement | Use Case | Source |
|------|--------------|----------|--------|
| `FRESH` | Nouvelle session, pas de resume | Swarm task isolée | Original |
| `CONTINUE` | Resume session existante | Brainstorm multi-tour | Original |
| `BRANCH` | Fork depuis session parent | Agent spawned parallèle | Claude |
| `EPHEMERAL` | One-shot, PAS de persistence | Tâches TRIVIAL/SIMPLE | Gemini |

> **EPHEMERAL Mode** (Gemini proposal): Pour éviter la saturation de `~/.gemini/tmp`,
> les tâches triviales ne créent PAS de session persistante. Gain de performance + propreté.

```python
def get_session_mode(complexity: TaskComplexity, is_parallel: bool) -> SessionMode:
    """Sélection automatique du mode de session"""
    if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
        return SessionMode.EPHEMERAL  # ⬅️ GEMINI: No persistence
    elif is_parallel:
        return SessionMode.BRANCH     # ⬅️ CLAUDE: Fork isolation
    else:
        return SessionMode.FRESH      # Default: nouvelle session isolée
```

#### Protocoles de Handover Cross-Agent (Gemini ↔ Claude)

**Protocole 1: Context Summarization Injection** (Phase 7 - Baseline)
```python
# Gemini → Claude
claude_prompt = f"""
## Contexte (Handover de Gemini)
{gemini_result['summary']}

## Fichier de référence
{artifact_path}

## Ta mission
{next_task}
"""
```

**Protocole 2: Shared Memory File** (Phase 7 - Recommandé)
```
workspace/.nexus/shared_memory/
├── task_abc123/
│   ├── gemini_research.md      ← Gemini écrit ici
│   ├── claude_analysis.md      ← Claude écrit ici
│   └── handover_summary.json   ← Résumé structuré
```
→ Persistant, debuggable, asynchrone

**Protocole 3: Agent-as-MCP-Tool** (Phase 12.4 - Futur)
```python
# Claude appelle Gemini comme outil MCP
result = mcp__gemini__research("query")

# Gemini appelle Claude comme outil MCP
result = mcp__claude__analyze("context")
```
→ Orchestration dynamique pilotée par LLM

**Sélection du protocole**:
| Complexité | Protocole | Raison |
|------------|-----------|--------|
| Simple | 1 (Injection) | Rapide, suffisant |
| Multi-step | 2 (Shared Memory) | Persistance, debug |
| Dynamic | 3 (MCP) | LLM décide quand appeler |

**Parallel Execution Isolation**:
```python
# PARALLEL mode: chaque agent a sa propre session
async def execute_parallel(agents, task):
    sessions = {}
    for agent in agents:
        sessions[agent.id] = session_manager.create_session(
            f"{task.id}_{agent.id}"
        )

    # Exécution parallèle avec sessions isolées
    results = await asyncio.gather(*[
        invoke_agent(agent, sessions[agent.id])
        for agent in agents
    ])

    # Merge results (pas de context bleeding)
    return merge_results(results)
```

#### Session Branching pour PARALLEL Mode (Claude proposal 2025-12-04)

> **Concept**: Utiliser `--fork-session` de Claude pour créer des branches isolées
> qui peuvent être mergées après exécution parallèle.

```
Claude --fork-session architecture:
  Task A ─┬─ Branch 1 (Agent 1) ──┬─ Merge
          │   session_uuid_1      │
          └─ Branch 2 (Agent 2) ──┘
              session_uuid_2
```

**Implémentation PARALLEL avec fork**:
```python
async def execute_parallel_with_branching(task: Task, agents: List[Agent]):
    # 1. Session parent (contexte initial)
    parent_session = session_manager.create_session(task.id, "parent", "orchestrator")

    # 2. Fork pour chaque agent (Claude natif, Gemini simulé)
    branches = {}
    for agent in agents:
        if agent.type == "claude":
            # Claude: fork natif via --fork-session
            branch_uuid = session_manager.fork_session(parent_session, agent.id)
        else:
            # Gemini: fork simulé (nouvelle session + context injection)
            branch_uuid = session_manager.create_branch(parent_session, agent.id)
        branches[agent.id] = branch_uuid

    # 3. Exécution parallèle avec branches isolées
    results = await asyncio.gather(*[
        invoke_agent(agent, branches[agent.id])
        for agent in agents
    ])

    # 4. Merge results
    return merge_results(results)
```

#### Spawned Agent Session Persistence (Claude proposal 2025-12-04)

> **Concept**: Les agents spawned peuvent avoir leur propre UUID persistant
> dans `BIRTH_CERTIFICATE.json`, leur donnant une "mémoire de personnalité".

**Extension BIRTH_CERTIFICATE.json**:
```json
{
  "agent_id": "sql_expert_abc123",
  "role": "SQL Query Optimization Expert",
  "birth_date": "2025-12-04T10:30:00Z",
  "parent_id": "nexus_v7.5",
  "session_persistence": {
    "enabled": true,
    "persistent_uuid": "spawned-sql-expert-uuid",
    "session_retention_days": 7,
    "context_summary": "Expert SQL spécialisé en optimisation de requêtes PostgreSQL"
  }
}
```

**Avantage**: L'agent SQL Expert "se souvient" de ses tâches précédentes
et peut réutiliser le contexte accumulé.

**Cleanup & Lifecycle** (enrichi Gemini+Claude):
- [ ] Auto-cleanup sessions > 24h
- [ ] `/session list` - Lister sessions actives
- [ ] `/session clear` - Nettoyer toutes les sessions Swarm
- [ ] Config: `session_retention_hours=24`

**Tests de validation**:
- [ ] Test: Deux tâches Swarm consécutives n'ont pas de context bleeding
- [ ] Test: PARALLEL mode avec 2 agents = 2 sessions distinctes
- [ ] Test: Brainstorm multi-tour conserve le contexte (CONTINUE mode)

**Méthodologie d'implémentation** (basée sur recherches 2025-12-03):

1. **Découverte Gemini CLI**:
   ```bash
   gemini --list-sessions
   # Output: sessions avec UUIDs [cc74e0e6-3f08-4ca9-...]
   # Storage: ~/.gemini/tmp/<project_hash>/chats/<uuid>.json
   ```

2. **Pattern Google ADK** ([source](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)):
   > "Sub-agents operate in isolated execution paths with no automatic sharing
   > of conversation history between branches during execution."

   → Implémenter `InvocationContext.branch` pour chaque agent parallèle

3. **Pattern Microsoft MCP** ([source](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/orchestrating-multi-agent-intelligence-mcp-driven-patterns-in-agent-framework/4462150)):
   > "Tenant isolation ensures one user's session state does not leak to another"

   → Chaque tâche Swarm = "tenant" isolé avec son propre contexte

4. **Checkpointing** (pour Self-Healing Phase 8):
   > "Checkpointing can snapshot shared and executor-local state at any point,
   > supporting pause/resume and fault recovery."

   → Sauvegarder état session avant fallback de mode

5. **Ordre d'implémentation (Option B - UUID-Based + Role Mapping + Asymétrique)**:
   ```
   Étape 1: Créer SwarmSessionManager (core/swarm/session_manager.py) [NOUVEAU]
           → get_or_create_session(task_id, role, agent_id)
           → context_handover(task_id, from_role, to_role, summary)
           → _persist_registry() vers session_registry.json

   Étape 2a: Modifier GeminiDriverV7._build_command()
           → Ajouter session_uuid param
           → --resume {uuid} -p "{prompt}" (UUID généré par CLI)

   Étape 2b: Créer ClaudeDriverV7 (core/drivers/claude_driver_v7.py) [NOUVEAU]
           → --session-id {uuid} (UUID imposé par NEXUS)
           → --fork-session pour mode BRANCH (natif!)
           → -p pour mode non-interactif

   Étape 3: Modifier HybridSwarmEngine.process_task()
           → Générer task_id unique au début
           → Passer (task_id, role) au SessionManager
           → Adapter appel selon driver type

   Étape 4: Modifier mode_executors.py
           → PARALLEL: chaque agent = rôle distinct = UUID distinct
           → LEAD_SUPPORT: lead + support = 2 UUIDs par rôle
           → Mode change: context_handover() (Gemini) ou --fork-session (Claude)

   Étape 5: Tests d'isolation
           → Gemini: 2 tâches = 2 UUIDs distincts
           → Claude: fork natif = isolation parfaite
           → Changement de mode = handover/fork fonctionne

   Étape 6: Commands /session list|clear|fork
   ```

   **Effort**: 4-5 jours (architecture asymétrique complète)

#### Data Integrity Layer (Impact Study 2025-12-04)

> **Découverte**: L'analyse workspace/blackboard a révélé des fragilités critiques
> qui doivent être corrigées EN MÊME TEMPS que Session Isolation pour éviter
> corruption des données en mode PARALLEL.

**Tâches supplémentaires Phase 7**:

- [ ] **AtomicJsonStore** - Wrapper pour toutes écritures JSON critiques
  ```python
  # core/utils/atomic_store.py
  class AtomicJsonStore:
      def save(self, data: dict) -> None:
          temp_path = self.path.with_suffix('.tmp')
          with open(temp_path, 'w') as f:
              json.dump(data, f, indent=2)
              f.flush()
              os.fsync(f.fileno())
          os.replace(temp_path, self.path)  # Atomic rename
  ```
  Fichiers ciblés: `session_registry.json`, `blackboard.json`, `successes.jsonl`

- [ ] **Threading Locks** - Protection des accès concurrents
  ```python
  # core/synapse/memory_v7.py
  from threading import RLock

  class MemoryManagerV7:
      def __init__(self):
          self._lock = RLock()  # Protège blackboard

      def add_to_history(self, message: Dict):
          with self._lock:
              # ... safe operations
  ```
  Impact: Obligatoire pour PARALLEL mode avec 2+ agents

- [ ] **TaskScopedBlackboard** - Isolation par tâche
  ```python
  # core/synapse/task_blackboard.py
  class TaskScopedBlackboard:
      def __init__(self, parent: MemoryManagerV7, task_id: str):
          self.task_id = task_id
          self._lock = RLock()
          self._state = {"objective": "", "history": [], "iteration": 0}
  ```
  Avantage: Chaque tâche Swarm a son blackboard isolé

- [ ] **Schema Migration** - Upgrade 6.0.0 → 7.5.0
  ```python
  def _migrate_schema(self, data: dict) -> dict:
      version = data.get("metadata", {}).get("version", "1.0.0")
      if version == "6.0.0":
          data["task_scoped_blackboards"] = {}
          data["metadata"]["version"] = "7.5.0"
      return data
  ```

- [ ] **SQLite Consideration** - Pour session_registry à haute concurrence
  ```python
  # Si > 5 agents parallèles, considérer SQLite
  # Avantages: ACID, WAL mode, concurrent reads
  # Inconvénients: Complexité, dépendance
  # Décision: JSON + RLock pour V7.5, SQLite optionnel V8.0
  ```

**Ordre d'implémentation révisé**:
```
Étape 0: AtomicJsonStore + Threading (PREREQUIS)  ← NOUVEAU
         → Corrige race conditions AVANT d'ajouter Session Manager

Étape 1: SwarmSessionManager avec AtomicJsonStore ✅ COMPLETED
Étape 2a: GeminiDriverV7 + session_uuid ✅ COMPLETED
Étape 2b: ClaudeDriverV7 + session_uuid
Étape 3: HybridSwarmEngine + task_id + TaskScopedBlackboard
Étape 4: mode_executors.py + isolation
Étape 5: Tests d'isolation + intégrité données
Étape 6: Commands /session

**Status (2025-12-04)**: 80/80 tests passés pour l'infrastructure Phase 7.
 AtomicJsonStore (27 tests) + SwarmSessionManager (45 tests) + GeminiDriver (8 tests).
```

**Effort révisé**: 5-6 jours (inclut Data Integrity Layer)

### Phase 10: Auto-Mémoire des Succès [Priorité: HAUTE]
**Objectif**: NEXUS se souvient de ce qui a fonctionné
**Effort**: 1 semaine
**Enrichi**: Claude proposal (2025-12-04) - Session Metrics pour DyLAN

**Phase 10a: Storage (V7.5.2)** ✅ COMPLETED 2025-12-04
- [x] `core/memory/success_memory.py` - SuccessMemory class
- [x] SuccessEntry dataclass avec quality_score estimation
- [x] AtomicJsonStore pour persistence thread-safe
- [x] FIFO eviction (max_entries=500)
- [x] Auto-logging dans HybridSwarmEngine.process_task()
- [x] 23 tests (test_success_memory.py)

**Phase 10b: Retrieval Simple (V7.6)** ✅ COMPLETED 2025-12-04
- [x] Recherche par Jaccard Similarity (zero-dependency tokenization)
- [x] `find_similar_tasks()` avec EN/FR stop words
- [x] `get_best_mode_for_similar()` helper
- [x] ModeSelector integration avec `_apply_memory_boost()`
- [x] Memory boost tiers: HIGH (0.25), MEDIUM (0.15), LOW (0.08)
- [x] 23 tests (test_memory_retrieval.py)

**Phase 10c: Semantic Retrieval (V7.7 - optionnel)**
- [ ] Upgrade vers `sentence-transformers` (all-MiniLM-L6-v2, 80MB local)
- [ ] Cosine similarity pour matching sémantique
- [ ] Seulement si 10b insuffisant

#### Phase 10d: Session Metrics pour DyLAN (Claude proposal 2025-12-04)

> **Concept**: Tracker quelles sessions (et quels modes) mènent aux succès.
> DyLAN peut alors apprendre "ce type de session réussit mieux avec Gemini lead".

**Extension du schema de succès**:
```json
{
  "task_hash": "abc123",
  "description": "Optimize SQL query",
  "swarm_mode": "SPECIALIST",
  "agents_used": ["sql_expert"],
  "duration_seconds": 45.2,
  "success": true,
  "session_metrics": {
    "session_uuid": "uuid-xxx-yyy",
    "session_mode": "FRESH",
    "lead_agent": "sql_expert",
    "context_reuse": false,
    "total_turns": 3,
    "stagnation_events": 0,
    "hot_swaps": 0,
    "checkpoints_used": 0
  }
}
```

**Intégration avec DyLAN**:
```python
class SessionAwareDyLAN:
    """Extension DyLAN avec métriques de session"""

    def update_importance(self, invocation: AgentInvocationResult, session_metrics: dict):
        """Met à jour les scores en tenant compte du contexte de session"""

        # 1. Score de base (existing DyLAN)
        base_importance = self._calculate_base_importance(invocation)

        # 2. Bonus/Malus session
        session_factor = 1.0

        if session_metrics.get("context_reuse"):
            # L'agent a réutilisé un contexte existant → bonus
            session_factor *= 1.1

        if session_metrics.get("hot_swaps", 0) > 0:
            # L'agent a été hot-swappé → malus pour le lead original
            session_factor *= 0.9

        if session_metrics.get("checkpoints_used", 0) > 0:
            # Fallback utilisé → mode initial moins fiable
            session_factor *= 0.95

        # 3. Score final
        return base_importance * session_factor

    def get_recommendation_with_session(self, task_type: str) -> dict:
        """Recommande mode + lead en tenant compte de l'historique des sessions"""
        past_successes = self.memory.query_successes(task_type, limit=10)

        # Analyser les patterns de succès
        mode_stats = {}
        for success in past_successes:
            mode = success.get("swarm_mode")
            lead = success.get("session_metrics", {}).get("lead_agent")
            key = f"{mode}:{lead}"

            if key not in mode_stats:
                mode_stats[key] = {"count": 0, "avg_duration": 0}
            mode_stats[key]["count"] += 1
            mode_stats[key]["avg_duration"] += success.get("duration_seconds", 0)

        # Trouver le meilleur pattern
        best_pattern = max(mode_stats.items(), key=lambda x: x[1]["count"])

        return {
            "suggested_mode": best_pattern[0].split(":")[0],
            "suggested_lead": best_pattern[0].split(":")[1],
            "confidence": best_pattern[1]["count"] / len(past_successes),
            "avg_duration": best_pattern[1]["avg_duration"] / best_pattern[1]["count"]
        }
```

**Avantages**:
- DyLAN apprend des patterns de session, pas juste des invocations individuelles
- Hot-Swap devient un signal d'apprentissage
- Les checkpoints/fallbacks informent les futures décisions de mode

### Phase 12.3: CORTEX - MCP Client [Priorité: HAUTE] ✅ COMPLETED 2025-12-04
**Objectif**: Standardisation des outils via Model Context Protocol
**Effort**: 1-2 semaines

> **Contexte Décembre 2025**: MCP fête son 1 an. Adopté par OpenAI, Google, Anthropic.
> Standard de facto pour l'interopérabilité des outils AI.

**Implémentation Zero-Dep** (pas de SDK externe):
- [x] `core/mcp/protocol.py` - Types JSON-RPC 2.0 natifs
- [x] `core/mcp/client.py` - Client MCP (subprocess stdio)
- [x] `core/mcp/registry.py` - Chargement config serveurs
- [x] Découverte dynamique des tools (tools/list)
- [x] Intégration ToolManager (outils `mcp_{server}_{tool}`)
- [x] Configuration via `workspace/.nexus/mcp_servers.json`
- [x] 36 tests (tests/test_mcp_client.py)

**Migration outils hardcodés**: Reportée à V7.7 (Phase 12.4)

```json
{
  "servers": {
    "filesystem": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
      "args": ["/tmp"],
      "enabled": true
    }
  }
}
```

### Phase 12.4: Symmetric MCP Bridges - Agent-as-Tool [Priorité: HAUTE]
**Objectif**: Permettre à chaque agent d'appeler l'autre via MCP
**Effort**: 1 semaine
**Source**: Analyse collaboration Gemini+Claude (2025-12-04)

> **Philosophie HIVE MIND**: Ni Gemini ni Claude n'est le "super-orchestrateur" permanent.
> Le lead est décidé dynamiquement par: Task Analysis, Swarm Mode, DyLAN Scores, Consensus.

**Architecture Symétrique**:
```
┌─────────────┐      MCP Protocol      ┌─────────────┐
│   GEMINI    │◄──────────────────────►│   CLAUDE    │
│             │                         │             │
│ Peut appeler│                         │ Peut appeler│
│ claude_mcp  │                         │ gemini_mcp  │
└─────────────┘                         └─────────────┘
```

**Implémentation**:
- [ ] `core/mcp/claude_bridge.py` - Claude exposé comme MCP Server pour Gemini
- [ ] `core/mcp/gemini_bridge.py` - Gemini exposé comme MCP Server pour Claude
- [ ] Configuration symétrique:
  ```bash
  # Gemini peut appeler Claude
  gemini mcp add claude python core/mcp/claude_bridge.py

  # Claude peut appeler Gemini (via mcp_servers.json)
  {"name": "gemini", "command": "python", "args": ["core/mcp/gemini_bridge.py"]}
  ```

**Architecture Bidirectionnelle**:

| Direction | Méthode | Raison |
|-----------|---------|--------|
| **Claude → Gemini** | MCP Server | Claude supporte `--mcp-config` natif |
| **Gemini → Claude** | Tool Registry | Gemini utilise tools Python classiques |

**Implémentation Claude → Gemini** (via MCP):
```python
# core/mcp/gemini_bridge.py
@mcp_tool("gemini_research")
def research(query: str) -> str:
    return gemini_driver.call(prompt=query, session_mode="SWARM_TASK")

@mcp_tool("gemini_brainstorm")
def brainstorm(topic: str) -> str:
    return gemini_driver.call(prompt=f"Brainstorm sur: {topic}")
```

**Implémentation Gemini → Claude** (via Tool Registry):
```python
# core/execution/tools/claude_tool.py
def ask_claude(prompt: str, context_files: List[str] = None) -> str:
    """Tool pour que Gemini invoque Claude comme sous-processeur"""
    file_args = []
    if context_files:
        for f in context_files:
            file_args.extend(["--add-dir", f])

    return claude_driver.call(
        prompt=prompt,
        extra_args=file_args,
        session_mode="SWARM_TASK"
    )

# Enregistrement dans tool_manager.py
GEMINI_TOOLS["ask_claude"] = ask_claude
```

**Architecture Fractale** (Gemini research 2025-12-04):
```
NEXUS →
  └── Gemini (Chef de projet, 1M tokens)
        ├── Analyse 100 fichiers (son point fort)
        ├── ask_claude("Refactor file_1.py") → Code expert
        ├── ask_claude("Refactor file_2.py") → Code expert
        ├── ask_claude("Write tests") → Tests
        └── Synthèse finale (Gemini)
```
→ Gemini garde la main, Claude est "sous-processeur expert"

**Outils exposés (récapitulatif)**:
| Agent | Peut appeler | Via | Outils |
|-------|--------------|-----|--------|
| Claude | Gemini | MCP | `gemini_research`, `gemini_brainstorm` |
| Gemini | Claude | Tool | `ask_claude`, `claude_code_review` |

**Sélection dynamique du Lead**:
```python
def select_lead_agent(task_analysis: TaskAnalysis) -> str:
    """Décide qui mène basé sur le contexte"""

    # 1. Expertise domaine
    if task_analysis.primary_domain == Domain.WEB_RESEARCH:
        return "gemini"  # Google Search natif
    elif task_analysis.primary_domain == Domain.CODING:
        return "claude"  # Meilleur en code

    # 2. DyLAN scores historiques
    gemini_score = agent_pool.get_importance("gemini", task_analysis.primary_domain)
    claude_score = agent_pool.get_importance("claude", task_analysis.primary_domain)

    if abs(gemini_score - claude_score) > 0.2:
        return "gemini" if gemini_score > claude_score else "claude"

    # 3. Consensus (égalité → négociation)
    return "negotiate"
```

**Scénarios d'utilisation**:
| Scénario | Lead | Support | Raison |
|----------|------|---------|--------|
| Recherche web intensive | Gemini | Claude | Google Search natif |
| Refactoring code complexe | Claude | Gemini | Meilleur code generation |
| Audit sécurité | Gemini (red team) | Claude (blue team) | Adversarial |
| Architecture design | Négocié | Négocié | Expertise égale |

### Phase 12.5: Dynamic Tool Generation [Priorité: MOYENNE]
**Objectif**: Génération de scripts Python jetables pour tâches spécifiques
**Effort**: 1 semaine
**Source**: Analyse Gemini (2025-12-04) + Anthropic "Code Execution with MCP" pattern

> **Concept Gemini**: NEXUS peut déjà modifier son propre code. Il pourrait générer
> des outils jetables pour une tâche spécifique, les utiliser, puis les supprimer.

**Pattern "Metaprogramming for Tools"**:
```python
class DynamicToolGenerator:
    """Génère des outils Python jetables pour tâches spécifiques"""

    def __init__(self, workspace: Path):
        self.tools_dir = workspace / "tools" / "generated"
        self.tools_dir.mkdir(parents=True, exist_ok=True)

    def generate_tool(self, task_description: str, code: str) -> str:
        """
        Génère un script Python jetable et l'enregistre comme outil.

        Args:
            task_description: Description de la tâche
            code: Code Python généré par l'agent

        Returns:
            Nom de l'outil généré
        """
        tool_id = f"temp_tool_{uuid.uuid4().hex[:8]}"
        tool_path = self.tools_dir / f"{tool_id}.py"

        # Wrapper sécurisé pour le code généré
        wrapper = f'''
"""
Generated Tool: {tool_id}
Task: {task_description}
Generated: {datetime.utcnow().isoformat()}
Lifecycle: EPHEMERAL (auto-delete after use)
"""
import sys
from pathlib import Path

def execute(*args, **kwargs):
    """Execute the generated code in sandboxed context"""
{textwrap.indent(code, "    ")}

if __name__ == "__main__":
    result = execute()
    print(result)
'''
        tool_path.write_text(wrapper)

        # Enregistrer dans ToolManager (temporaire)
        self.tool_manager.register_temp_tool(tool_id, tool_path)

        return tool_id

    def cleanup_tool(self, tool_id: str) -> None:
        """Supprime l'outil jetable après utilisation"""
        tool_path = self.tools_dir / f"{tool_id}.py"
        if tool_path.exists():
            tool_path.unlink()
        self.tool_manager.unregister_tool(tool_id)
```

**Exemple d'utilisation**:
```
User: "Analyse les 50 fichiers CSV dans data/ et génère un rapport"

Agent (Gemini): Je vais créer un outil spécialisé pour cette tâche.

<generate_tool name="csv_analyzer">
import pandas as pd
from pathlib import Path

def execute():
    results = []
    for csv_file in Path("data").glob("*.csv"):
        df = pd.read_csv(csv_file)
        results.append({
            "file": csv_file.name,
            "rows": len(df),
            "columns": list(df.columns)
        })
    return results
</generate_tool>

<tool_use name="csv_analyzer"/>

[Résultat: 50 fichiers analysés...]

[Outil csv_analyzer supprimé automatiquement]
```

**Avantages**:
- Capacité d'adaptation infinie aux tâches complexes
- Économie de tokens (code exécuté vs décrit)
- Réutilisation du pattern Anthropic "Code Execution with MCP"

**Garde-fous**:
- [ ] Sandbox obligatoire (SandboxPolicy)
- [ ] Timeout d'exécution (30s max)
- [ ] Auto-cleanup après exécution
- [ ] Pas d'accès réseau sauf autorisation explicite
- [ ] Log de tous les outils générés

---

## 4. Phases Futures (V7.7 → V8.0)

### Phase 11: Extended Swarm Modes [Priorité: MOYENNE]
**Objectif**: Topologies avancées SANS nouveau système

> **Note**: Squad System original reporté. Extension des modes Swarm existants préférée.

- [ ] LEAD_SUPPORT_N: 1 lead + N workers (topology STAR)
- [ ] PARALLEL_SYNC: Parallel avec sync points (topology MESH)
- [ ] PIPELINE: Sequential avec handoff structuré
- [ ] Configuration via `swarm_config` plutôt que nouveau `/squad`

### Phase 12.1: MNEMOSYNE - Mémoire Avancée [Priorité: BASSE]
**Objectif**: Memory Graph (Vector + Relations)

> **Contexte**: Vector DB seul insuffisant pour mémoire long-terme (2025 research).
> Nécessite combinaison Vector + Graph pour relations entre tâches.

- [ ] Seulement si Phase 10c insuffisante
- [ ] Option A: ChromaDB local (si >10k entrées)
- [ ] Option B: SQLite + embeddings (plus simple)
- [ ] Memory Graph: tâches liées par similarité ET relations causales

```
Task A (SQL optimization)
    ├── used_mode: SPECIALIST
    ├── solved_by: sql_expert_agent
    └── SIMILAR_TO → Task B (Query performance)
```

### ~~Phase 12.2: OUROBOROS~~ [ANNULÉE]
~~Background Evolution~~

> **Décision**: Annulée pour complexité excessive.
> Background workers = race conditions, corruption état, debugging difficile.
>
> **Alternative**: "Code Execution with MCP" pattern (Anthropic Nov 2025)
> - Agent écrit code Python pour s'auto-corriger
> - Exécution sandboxée immédiate
> - Pas de processus background

### Phase 13: Dormant Features Activation [Priorité: MOYENNE]
**Objectif**: Réactiver les fonctionnalités existantes mais non utilisées
**Effort**: 1 semaine
**Source**: Impact Study Gemini (2025-12-04) - Découverte de code dormant

> **Contexte**: L'analyse de la codebase a révélé plusieurs fonctionnalités
> implémentées mais jamais appelées. Ces "dormant features" représentent
> un investissement déjà fait qu'il suffit de connecter.

#### Phase 13a: Graph of Thought (GoT) Integration

**Découverte** (`hybrid_swarm_engine.py`):
```python
# Ligne ~50: Import présent mais jamais utilisé
from core.reasoning.graph_of_thought import GraphOfThought  # DEAD IMPORT
```

**Potentiel**: GoT permet un raisonnement non-linéaire, idéal pour tâches EXPERT.

**Réactivation**:
- [ ] Auditer `core/reasoning/graph_of_thought.py` (si existe)
- [ ] Intégrer GoT dans `ModeSelector` pour tâches EXPERT
- [ ] Permettre `swarm_mode: GOT` pour raisonnement complexe
- [ ] Tests: Tâche mathématique multi-étapes avec GoT vs sans GoT

#### Phase 13b: /workspace Commands Reactivation

**Découverte** (`repl.py`):
```python
# Commandes /workspace commentées ou incomplètes
# /workspace init, /workspace status, /workspace clean
```

**Potentiel**: Gestion multi-projet native, chaque workspace isolé.

**Réactivation**:
- [ ] `/workspace init` - Créer workspace/.nexus/ avec structure complète
- [ ] `/workspace status` - Afficher état (sessions actives, agents, métriques)
- [ ] `/workspace clean` - Nettoyer sessions/cold storage > N jours
- [ ] `/workspace switch <path>` - Changer de workspace actif
- [ ] Documentation: Ajouter à COMMANDS.md

#### Phase 13c: Telemetry Export

**Découverte** (`config.py`):
```python
self.telemetry_enabled: bool = os.getenv("TELEMETRY_ENABLED", "True")
self.telemetry_file: str = os.getenv("TELEMETRY_FILE", "workspace/telemetry.jsonl")
```

**Potentiel**: Export vers observabilité externe (Jaeger, Prometheus).

**Réactivation**:
- [ ] Vérifier que `telemetry.jsonl` est bien alimenté
- [ ] Format OpenTelemetry compatible pour export
- [ ] `/telemetry export` - Export vers Jaeger/Grafana
- [ ] Métriques: Latence par mode, success rate par agent, tokens consommés

#### Phase 13d: AutoMemory ↔ ModeSelector Connection

**Découverte** (`auto_memory.py`):
```python
def suggest_mode(self, task_hash: str) -> Optional[str]:
    """Suggère un mode basé sur l'historique"""
    # ✅ IMPLÉMENTÉ mais PAS APPELÉ!

def suggest_lead(self, task_hash: str) -> Optional[str]:
    """Suggère un lead agent basé sur l'historique"""
    # ✅ IMPLÉMENTÉ mais PAS APPELÉ!
```

**Potentiel**: Memory-augmented decision making déjà codé!

**Réactivation**:
- [ ] Appeler `suggest_mode()` dans `ModeSelector._select_mode()`
- [ ] Appeler `suggest_lead()` dans agent assignment
- [ ] Fallback sur DyLAN si memory n'a pas de suggestion
- [ ] Tests: Après 5 tâches similaires, memory suggère le bon mode

#### Phase 13e: Global Registry Migration

**Découverte** (Impact Study):
- Sessions Gemini stockées dans `~/.gemini/tmp/<hash>/chats/`
- NEXUS devrait avoir son propre espace global

**Architecture cible**:
```
~/.nexus/                     ← NOUVEAU: Global NEXUS home
├── config.json               ← Settings globaux
├── agent_registry.json       ← Agents persistants cross-workspace
├── session_registry.json     ← Sessions globales (Option)
└── cache/                    ← Cache embeddings, etc.

workspace/.nexus/             ← Local au projet
├── blackboard.json           ← État session courante
├── task_blackboards/         ← Isolation par tâche
└── cold_storage/             ← Archives
```

**Avantage**: Agent spawné dans projet A réutilisable dans projet B.

**Implémentation**:
- [ ] `core/config.py`: `NEXUS_HOME = Path.home() / ".nexus"`
- [ ] Migration gracieuse: Si `~/.nexus/` n'existe pas, le créer
- [ ] `/agent list --global` - Lister agents cross-workspace
- [ ] `/agent import <workspace>` - Importer agent d'un autre projet

---

## 5. Idées Exploratoires (V8.0+)

### A2A Protocol (Agent-to-Agent)
Microsoft Agent Framework supporte A2A (Déc 2025). NEXUS pourrait exposer ses agents spawned comme services A2A pour interopérabilité externe.

### Observabilité Swarm
Export OpenTelemetry des traces Swarm vers Jaeger/Grafana. Dashboard temps réel des collaborations multi-agents.

### Self-Correction via Code Execution
Pattern Anthropic "Code Execution with MCP" - réduction 98.7% tokens. L'agent génère du code Python au lieu d'appeler des tools directement.

---

## 6. Timeline Révisée

```
V7.5.6 (Décembre 2025) ← CURRENT
│
├─[COMPLETED] Phase 7: Session Isolation + Data Integrity Layer
│   ├── AtomicJsonStore (PREREQUIS) ✅ COMPLETED
│   ├── Threading Locks (PREREQUIS) ✅ COMPLETED
│   ├── TaskScopedBlackboard ✅ INTEGRATED
│   ├── SwarmSessionManager ✅ COMPLETED
│   └── Schema Migration 6.0→7.5 ✅ COMPLETED
│
├─[COMPLETED] Phase 5b: N-Agent Agnosticism Complet
│   └── Spawned agents dans tous les 6 modes ✅ COMPLETED
│   └── *Note: DyLAN default score is 0.5 for new agents*
│
├─[COMPLETED] Phase 8: Self-Healing Swarm + Recovery
│   ├── Mode Fallback Matrix ✅ COMPLETED
│   ├── Checkpointing ✅ COMPLETED
│   ├── Cold Storage avant Compression (Integrated in AtomicJsonStore)
│   ├── Panic → Recovery Transformation (Via execute_with_fallback)
│   └── Hot-Swap Lead Agent (Via Role-Based Sessions)
│
└─[COMPLETED] Phase 9: Fast Path ⚡
    └── Bypass FSM pour requêtes triviales ✅ COMPLETED

V7.6 (Janvier 2026) - STARTED
├── [COMPLETED] Phase 10a: Auto-Memory Storage
│   ├── SuccessMemory class ✅
│   ├── AtomicJsonStore integration ✅
│   └── HybridSwarmEngine hook ✅
├── [COMPLETED] Phase 10b: Memory-Augmented Mode Selection
│   ├── Jaccard Similarity Search ✅
│   ├── ModeSelector Integration ✅
│   └── Memory Boost (HIGH/MEDIUM/LOW tiers) ✅
├── [COMPLETED] Phase 12.3: MCP Client (CORTEX)
│   ├── core/mcp/protocol.py - JSON-RPC 2.0 types ✅
│   ├── core/mcp/client.py - MCPClient (stdio) ✅
│   ├── core/mcp/registry.py - ServerConfig loader ✅
│   └── ToolManager integration (mcp_{server}_{tool}) ✅
├── Phase 10d: Session Metrics pour DyLAN
└── Phase 13a-d: Dormant Features (GoT, /workspace, Telemetry, AutoMemory link)

V7.7 (Février 2026)
├── Phase 11: Extended Swarm Modes
├── Phase 12.4: Symmetric MCP Bridges
├── Phase 12.5: Dynamic Tool Generation
├── Phase 13e: Global Registry Migration
└── Phase 10c: Semantic Retrieval (si nécessaire)

V8.0 (Mars 2026)
├── Phase 12.1: MNEMOSYNE (si nécessaire)
├── SQLite pour session_registry (si >5 agents parallèles)
└── Exploratoire: A2A, Observabilité
```

### Dépendances Critiques

```
AtomicJsonStore ─────────────┐
                             ├──► SwarmSessionManager ──► Session Isolation
Threading Locks ─────────────┘

TaskScopedBlackboard ────────► Context Bleeding Fix

Cold Storage ────────────────► Panic → Recovery

AutoMemory link ─────────────► Memory-Augmented Mode Selection
```

---

## 7. Métriques de Succès HIVE MIND

| Métrique | Objectif V7.6 | Objectif V8.0 | Source |
|----------|---------------|---------------|--------|
| Swarm Task Success Rate | >85% | >95% | Original |
| Agent Spawn Success | >95% | >99% | Original |
| JSON Parse Errors | <1% | <0.1% | Original |
| User Latency (trivial) | <2s | <1s | Original |
| User Latency (complex) | <30s | <20s | Original |
| Test Coverage | >70% | >80% | Original |
| Memory Hit Rate | N/A | >60% | Original |
| **Spawned Agent Lead Rate** | >20% | >40% | Gemini |
| **Self-Healing Recovery Rate** | >50% | >80% | Gemini |
| **Context Isolation Rate** | 100% | 100% | Original |
| **Ephemeral Session Usage** | >30% | >50% | Gemini (2025-12-04) |
| **Session Reuse Rate** | >40% | >60% | Claude (2025-12-04) |
| **Hot-Swap Events** | <10% | <5% | Claude (2025-12-04) |
| **Checkpoint Usage Rate** | <20% | <10% | Gemini (2025-12-04) |
| **Dynamic Tool Generation** | N/A | >10 tools/week | Gemini (2025-12-04) |

### Nouvelles Métriques (Gemini + Claude 2025-12-04)

| Métrique | Description | Objectif |
|----------|-------------|----------|
| **Ephemeral Session Usage** | % de tâches triviales utilisant mode EPHEMERAL | >50% (économie stockage) |
| **Session Reuse Rate** | % de sessions qui réutilisent du contexte existant | >60% (efficacité) |
| **Hot-Swap Events** | % de tâches nécessitant un changement de lead | <5% (stabilité) |
| **Checkpoint Usage Rate** | % de tâches nécessitant restore checkpoint | <10% (fiabilité) |
| **Dynamic Tool Generation** | Nombre d'outils jetables générés par semaine | >10 (adaptabilité) |

### Métriques d'Intégrité des Données (Impact Study 2025-12-04)

| Métrique | Description | Objectif V7.6 | Objectif V8.0 |
|----------|-------------|---------------|---------------|
| **JSON Corruption Events** | Fichiers JSON corrompus détectés | 0 | 0 |
| **Atomic Write Success Rate** | % d'écritures atomiques réussies | >99.9% | 100% |
| **Race Condition Incidents** | Conflits threading détectés en PARALLEL | 0 | 0 |
| **Cold Storage Coverage** | % de compressions avec backup préalable | 100% | 100% |
| **Schema Migration Success** | Upgrades 6.0→7.5 sans perte de données | 100% | 100% |
| **Recovery Success Rate** | Récupérations auto depuis ERROR/PANIC | >90% | >99% |
| **Dormant Feature Activation** | Features réactivées (sur 5 identifiées) | 3/5 | 5/5 |
| **Memory Suggestion Accuracy** | Précision des suggestions AutoMemory | N/A | >70% |

### Métriques de Santé Workspace

| Métrique | Description | Seuil d'Alerte |
|----------|-------------|----------------|
| **Session Count** | Nombre de sessions actives | >50 = cleanup recommandé |
| **Cold Storage Size** | Taille du cold storage | >100MB = cleanup |
| **Task Blackboard Count** | Blackboards de tâches orphelins | >20 = investigation |
| **Stale Sessions** | Sessions > 24h sans activité | >10 = auto-cleanup |

---

## 8. Garde-fous Immuables

1. **KERNEL.py**: Modifications uniquement via consensus documenté + régénération hash
2. **Collaboration égalitaire**: Gemini + Claude = partenaires (jamais hiérarchie imposée)
3. **Coexistence**: Agents spawned persistent (pas de remplacement, ils coexistent)
4. **Sécurité**: SandboxPolicy appliquée partout (tools, MCP, spawned agents)
5. **Simplicité**: Operation Ockham (supprimer avant d'ajouter, étendre avant de créer)
6. **Standards**: Préférer protocoles ouverts (MCP, A2A) aux solutions propriétaires

---

## 9. Sources & Références

### Standards & Protocoles
- [Model Context Protocol - 1 an](https://www.anthropic.com/news/model-context-protocol) (Anthropic)
- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) (Anthropic Nov 2025)
- [Microsoft Agent Framework](https://azure.microsoft.com/en-us/blog/introducing-microsoft-agent-framework/) (A2A Protocol)

### Frameworks Multi-Agents
- [Top AI Agent Frameworks 2025](https://www.shakudo.io/blog/top-9-ai-agent-frameworks) (Shakudo)
- [Google Agent Development Kit](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/) (ADK)
- [AWS Strands Multi-Agent Patterns](https://aws.amazon.com/blogs/machine-learning/multi-agent-collaboration-patterns-with-strands-agents-and-amazon-nova/) (Self-Healing)

### Mémoire & Recherche
- [Beyond Vector Databases](https://vardhmanandroid2015.medium.com/beyond-vector-databases-architectures-for-true-long-term-ai-memory-0d4629d1a06) (Memory Graph)
- [Agentic AI Design Patterns 2022-2025](https://medium.com/@balarampanda.ai/agentic-ai-design-patterns-choosing-the-right-multimodal-multi-agent-architecture-2022-2025-046a37eb6dbe) (Fallback Strategies)
- [IEEE Self-Healing Multi-Agent Systems](https://ieeexplore.ieee.org/document/9339904/) (Fault Tolerance)

### Contributions Internes
- **Phase 5b & Phase 8**: Propositions architecturales Gemini (2025-12-03)
- **Phase 5 Implémentation**: Claude (2025-12-03) - SpawnedAgentLoader, SPECIALIST support
- **Phase 7 Tests CLI**: Gemini+Claude collab (2025-12-04)
  - Claude: Test initial (faux négatif avec pipe)
  - Gemini: Correction avec `-p` flag (mode non-interactif)
  - Résultat: UUID-Based Resume **VALIDÉ** ✅

### Analyse Croisée Gemini + Claude (2025-12-04)

> **Méthode**: Analyse indépendante de la roadmap et de la codebase par chaque agent,
> puis fusion des résultats en session collaborative.

**Contributions Gemini** 🤖:
| Idée | Phase Cible | Impact |
|------|-------------|--------|
| Mode EPHEMERAL | Phase 7 | Économie stockage, performance |
| Checkpointing | Phase 8 | Retry propre, Self-Healing fiable |
| Dynamic Tool Generation | Phase 12.5 | Adaptabilité infinie |
| Cleanup Lifecycle | Phase 7 | Évite saturation ~/.gemini/tmp |
| Économie de Tokens | Phase 7 | Fichiers > JSON dans prompt |

**Contributions Claude** 🧠:
| Idée | Phase Cible | Impact |
|------|-------------|--------|
| Spawned Agent Session Persistence | Phase 7 | Mémoire de personnalité |
| Session Metrics pour DyLAN | Phase 10d | Apprentissage contextuel |
| Hot-Swap Lead Agent | Phase 8 | Récupération dynamique |
| Session Branching PARALLEL | Phase 7 | Isolation parfaite avec fork |

**Convergences validées (CONSENSUS)**:
- Phase 7 = Priorité CRITIQUE #1
- Mapping Task+Role→UUID
- Shared Memory Files > JSON injection
- Architecture Agent-as-Tool symétrique
- Cleanup automatique des sessions

**Fichier source**: Analyse croisée documentée dans ce même fichier (section 1.1)

### Étude d'Impact Workspace & Blackboard (2025-12-04)

> **Méthode**: Analyse approfondie des modules `memory_v7.py`, `auto_memory.py`,
> `blackboard.json`, `mode_executors.py` par Gemini et Claude.

**Fragilités critiques découvertes**:
| Problème | Impact | Solution |
|----------|--------|----------|
| Race Condition (PARALLEL) | Corruption données | `threading.RLock()` |
| Single Blackboard | Context bleeding | `TaskScopedBlackboard` |
| Non-Atomic Writes | JSON corruption si crash | `AtomicJsonStore` |
| Compression irréversible | Perte historique | Cold Storage |
| Code dormant | Investissement gaspillé | Phase 13 |

**Contributions Gemini** 🤖:
| Découverte | Impact |
|------------|--------|
| Atomic Write-Replace pattern | Prévient corruption |
| Journal + Snapshot | Reconstruction état possible |
| Dormant features (GoT, /workspace, Telemetry) | Phase 13 créée |
| Global Registry ~/.nexus/ | Cross-workspace agents |
| SQLite consideration | Future-proof concurrency |

**Contributions Claude** 🧠:
| Découverte | Impact |
|------------|--------|
| Race condition code exact (ligne 149-153) | Fix ciblé |
| TaskScopedBlackboard pattern | Isolation sans refactoring massif |
| Panic→Recovery transformation | Auto-healing FSM |
| Schema migration 6.0→7.5 | Backward compatibility |
| AutoMemory methods non appelées | Quick wins Phase 13d |

**Fichier source**: Section 1.2 de ce document
