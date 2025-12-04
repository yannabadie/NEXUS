# ROADMAP NEXUS V7.5 "HIVE MIND"

**Version**: 7.5.4 | **Status**: Active | **Last Updated**: 2025-12-04
**Vision**: Cœur d'Intelligence Collaborative Générant des Agents Spécialisés

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

**Modes de session**:
| Mode | Comportement | Use Case |
|------|--------------|----------|
| `FRESH` | Nouvelle session, pas de resume | Swarm task isolée |
| `CONTINUE` | Resume session existante | Brainstorm multi-tour |
| `BRANCH` | Fork depuis session parent | Agent spawned parallèle |

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

**Cleanup & Lifecycle**:
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

### Phase 10: Auto-Mémoire des Succès [Priorité: HAUTE]
**Objectif**: NEXUS se souvient de ce qui a fonctionné
**Effort**: 1 semaine

**Phase 10a: Storage (V7.5.2)**
- [ ] `workspace/memory/successes.jsonl` - Log des méthodes efficaces
- [ ] `workspace/memory/failures.jsonl` - Log des échecs à éviter
- [ ] Schema: `{task_hash, description, swarm_mode, agents_used, duration, success}`
- [ ] Auto-logging après chaque tâche complétée

**Phase 10b: Retrieval Simple (V7.6)**
- [ ] Recherche par TF-IDF (pas de dépendance externe)
- [ ] Consultation mémoire avant délibération
- [ ] "J'ai résolu un problème similaire avec PING_PONG, je réutilise"

**Phase 10c: Semantic Retrieval (V7.7 - optionnel)**
- [ ] Upgrade vers `sentence-transformers` (all-MiniLM-L6-v2, 80MB local)
- [ ] Cosine similarity pour matching sémantique
- [ ] Seulement si 10b insuffisant

### Phase 12.3: CORTEX - MCP Client [Priorité: HAUTE]
**Objectif**: Standardisation des outils via Model Context Protocol
**Effort**: 1-2 semaines

> **Contexte Décembre 2025**: MCP fête son 1 an. Adopté par OpenAI, Google, Anthropic.
> Standard de facto pour l'interopérabilité des outils AI.

- [ ] Intégration `mcp-python` SDK
- [ ] `core/mcp/client.py` - Client MCP générique
- [ ] Découverte dynamique des capacités (tools, resources, prompts)
- [ ] Migration progressive des outils hardcodés:
  - [ ] `git` → MCP server git
  - [ ] `web_fetch` → MCP server fetch
  - [ ] `bash` → MCP server shell (sandboxed)
- [ ] Configuration via `mcp_servers.json`

```json
{
  "servers": [
    {"name": "filesystem", "command": "mcp-server-filesystem", "args": ["--root", "."]},
    {"name": "github", "command": "mcp-server-github"}
  ]
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
V7.5.3 (Décembre 2025) ← CURRENT
├── Phase 7: Session Isolation [CRITIQUE - Bug Fix]
│   └── Corrige context bleeding entre tâches Swarm
├── Phase 5b: N-Agent Agnosticism Complet [CRITIQUE]
│   └── Spawned agents dans tous les 6 modes
├── Phase 8: Self-Healing Swarm
│   └── Fallback automatique de MODE
└── Phase 9: Fast Path ⚡
    └── Bypass FSM pour requêtes triviales

V7.6 (Janvier 2026)
├── Phase 10a: Auto-Memory Storage
├── Phase 10b: Memory-Augmented Mode Selection
└── Phase 12.3: MCP Client (CORTEX)

V7.7 (Février 2026)
├── Phase 11: Extended Swarm Modes
└── Phase 10c: Semantic Retrieval (si nécessaire)

V8.0 (Mars 2026)
├── Phase 12.1: MNEMOSYNE (si nécessaire)
└── Exploratoire: A2A, Observabilité
```

---

## 7. Métriques de Succès HIVE MIND

| Métrique | Objectif V7.6 | Objectif V8.0 |
|----------|---------------|---------------|
| Swarm Task Success Rate | >85% | >95% |
| Agent Spawn Success | >95% | >99% |
| JSON Parse Errors | <1% | <0.1% |
| User Latency (trivial) | <2s | <1s |
| User Latency (complex) | <30s | <20s |
| Test Coverage | >70% | >80% |
| Memory Hit Rate | N/A | >60% |
| **Spawned Agent Lead Rate** | >20% | >40% |
| **Self-Healing Recovery Rate** | >50% | >80% |
| **Context Isolation Rate** | 100% | 100% |

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
