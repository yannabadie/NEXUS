# Module: Bootstrap - Project Analysis & Agent Discovery

**Version**: 7.5 (HIVE MIND)
**Last Updated**: 2025-12-04

---

## Role Architectural

Le module Bootstrap gere l'initialisation de NEXUS dans un nouvel environnement:

1. **Auto-Bootstrap**: Analyse un projet existant pour generer `NEXUS.md`
2. **Agent Discovery**: Decouvre les agents spawnes pour integration au Swarm

---

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 5: Agent Factory** | `agent_loader.py` integre agents spawnes au Swarm |
| **Phase 5b: N-Agent Agnosticism** | Agent loader supportera N providers |

**Vision HIVE MIND**: Ce module permet a NEXUS de s'adapter automatiquement a tout projet ET de charger dynamiquement les agents specialises crees via `/spawn`.

---

## Composants Cles

### Fichier: `auto_bootstrap.py`

**Classe**: `AutoBootstrap`

* **Fonction**: Analyse automatique de projet et generation NEXUS.md
* **Interaction FSM**: Aucune directe (utilitaire)
* **Notes d'Audit**: OK - Implementation complete

**Capacites de detection**:
| Type | Exemples |
|------|----------|
| Langages | Python, JavaScript, TypeScript, Go, Rust, Java, C#, Ruby, PHP |
| Frameworks | FastAPI, Django, Flask, React, Next.js, Vue, Express |
| Databases | PostgreSQL, MySQL, MongoDB, Redis |
| Outils | pytest, npm, make, docker-compose |

**Dataclass**: `ProjectAnalysis`
- `languages`, `frameworks`, `databases`, `tools`
- `directories`, `key_files`, `commands`
- `has_tests`, `has_docs`, `has_ci`

**Usage**:
```python
bootstrap = AutoBootstrap(project_path)
analysis = bootstrap.analyze()
nexus_md = bootstrap.generate_nexus_md(analysis)
bootstrap.save(nexus_md)
```

---

### Fichier: `agent_loader.py` [NOUVEAU V7.5]

**Classe**: `SpawnedAgentLoader`

* **Fonction**: Decouverte et chargement des agents spawnes depuis `workspace/agents/`
* **Interaction FSM**: Appele au demarrage par OrchestratorV7
* **Protocoles Utilises**:
  - `BIRTH_CERTIFICATE.json` pour config agent
  - `system_prompt.md` pour prompt specialise
  - `AgentProfile` pour integration AgentPool
* **Notes d'Audit**: Implemente Phase 5 (Agent Factory)

**Dataclass**: `SpawnedAgentConfig`
- `agent_id`, `role`, `mission`
- `domains`, `tools_priority`
- `system_prompt_path`

**Methodes principales**:
| Methode | Description |
|---------|-------------|
| `discover_spawned_agents()` | Scanne workspace/agents/ et retourne List[AgentProfile] |
| `load_agent_config()` | Charge config d'un agent specifique |
| `load_system_prompt()` | Charge prompt specialise |
| `get_agent_workspace()` | Retourne workspace de l'agent |

**Fonction utilitaire**: `discover_and_register_spawned_agents()`

**Usage**:
```python
from core.bootstrap.agent_loader import SpawnedAgentLoader

loader = SpawnedAgentLoader(workspace_path)
agents = loader.discover_spawned_agents()

for profile in agents:
    agent_pool.register(profile)
```

---

### Fichier: `__init__.py`

* **Fonction**: Exports publics du module
* **Notes d'Audit**: OK

---

## Structure Agent Spawne

Chaque agent spawne via `/spawn` cree cette structure:

```
workspace/agents/<agent_id>/
+-- BIRTH_CERTIFICATE.json   # Config obligatoire
+-- system_prompt.md         # Prompt specialise (optionnel)
+-- workspace/               # Espace de travail agent
```

**Format BIRTH_CERTIFICATE.json**:
```json
{
  "agent_id": "sql_expert",
  "role": "SQL Expert",
  "created_at": "2025-12-04T10:00:00Z",
  "parent": "NEXUS_V7.5",
  "specialization": {
    "mission": "Optimize SQL queries",
    "domains": ["DATABASE", "OPTIMIZATION"],
    "tools_priority": ["read", "bash", "edit"]
  }
}
```

---

## Dependances et Interactions (Synapses)

```
                     OrchestratorV7.__init__()
                           |
                           v
                    SpawnedAgentLoader
                           |
                           v
                    AgentPool.register()
                           |
                           v
                    ModeSelector.select_mode()
                    (inclut agents spawnes)
```

**Imports**:
- `core.swarm.agent_metrics.AgentProfile`
- Standard library: `json`, `pathlib`, `dataclasses`

---

## Usage REPL

```bash
# Bootstrap nouveau projet
nexus7> /bootstrap .
# Genere NEXUS.md adapte au projet

# Les agents spawnes sont charges automatiquement au demarrage
# Visible via:
nexus7> /pool-stats
# Affiche Gemini, Claude, ET agents spawnes
```

---

## Tests

**Recommandes**:
- `test_auto_bootstrap_detects_python()`
- `test_agent_loader_discovers_spawned()`
- `test_agent_loader_handles_missing_cert()`
