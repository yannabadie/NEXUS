# ROADMAP NEXUS V7.5 "HIVE MIND"

**Version**: 7.5.3 | **Status**: Active | **Last Updated**: 2025-12-03
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
├── Phase 5b: N-Agent Agnosticism Complet [CRITIQUE]
├── Phase 8: Self-Healing Swarm
└── Phase 9: Fast Path ⚡

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
