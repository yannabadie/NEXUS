# Module: Execution - Tool Dispatch Layer

**Version**: 7.5 (HIVE MIND)
**Last Updated**: 2025-12-04

---

## Role Architectural

Couche d'execution centralisee des outils NEXUS avec enforcement des politiques de securite.

**Principe**: Tous les outils passent par `ToolManager` qui verifie les permissions avant execution.

---

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 5: Agent Factory** | Outils accessibles aux agents spawnes |
| **Phase 7: Session Isolation** | Outils executes dans contexte isole |
| **Phase 9: Fast Path** | Bypass ToolManager pour outils read-only |

---

## Composants Cles

### Fichier: `tool_manager.py`

**Classe**: `ToolManager`

* **Fonction**: Dispatcher central pour les 11 outils NEXUS
* **Interaction FSM**: Verifie l'etat avant execution (certains outils bloques en BRAINSTORMING)
* **Protocoles Utilises**: `ToolUse` de core.synapse.protocol_v7
* **Notes d'Audit**: OK - Integration avec PathGuardian

**Outils Disponibles (11)**:

| Outil | Description | Permissions |
|-------|-------------|-------------|
| `read`, `read_file` | Lecture fichier | Toujours autorise |
| `write`, `write_file` | Ecriture fichier | Workspace + Evolution |
| `edit` | Search/Replace texte | Workspace + Evolution |
| `list_dir` | Liste repertoire | Toujours autorise |
| `glob` | Recherche fichiers par pattern | Toujours autorise |
| `grep` | Recherche code par regex | Toujours autorise |
| `bash`, `run_shell_command` | Commandes shell | Restreint (sandbox) |
| `git` | Operations Git (status/diff/log) | Read-only |
| `web_search` | Recherche Google (via Gemini) | Toujours autorise |
| `web_fetch` | Recuperation contenu URL | Toujours autorise |
| `todo_write` | Gestion liste taches | Workspace only |

---

### Fichier: `__init__.py`

* **Fonction**: Exports publics (ToolManager)
* **Notes d'Audit**: OK

---

## Integration Securite

```
Agent Request
     |
     v
ToolManager.execute(tool_name, args)
     |
     v
PathGuardian.validate_{read|write}()
     |
     +--[DENY]--> SecurityError
     |
     +--[ALLOW]--> Tool Execution --> Result
```

**Zones de permissions**:
- **Workspace**: `workspace/` - Read/Write
- **Agents**: `workspace/agents/` - Read/Write
- **Evolution**: `GENERATION_ACTIVE/` - Read/Write (mode evolution)
- **Parent**: `core/`, `prompts/` - Read-Only

---

## Mode Evolution

Quand `set_evolution_mode(True)` est appele:
- Write autorise vers `GENERATION_ACTIVE/`
- Permet la creation d'enfants avec mutations
- Desactive apres le cycle evolution

```python
tool_manager.set_evolution_mode(True)
# ... creation enfants ...
tool_manager.set_evolution_mode(False)
```

---

## Dependances et Interactions (Synapses)

```
                    OrchestratorV7
                         |
                         v
                    ToolManager
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
    PathGuardian    SandboxPolicy   Tool Impls
    (file access)   (state check)   (actual exec)
```

**Imports**:
- `core.security.PathGuardian`
- `core.governance.SandboxPolicy`
- `core.synapse.protocol_v7.ToolUse`

---

## Usage

```python
from core.execution import ToolManager

manager = ToolManager(workspace_path, parent_path)

# Execute un outil
result = manager.execute("read", {"file_path": "src/auth.py"})

# Mode evolution
manager.set_evolution_mode(True)
result = manager.execute("write", {"file_path": "GENERATION_ACTIVE/child/file.py", "content": "..."})
```

---

## Tests

**Fichier**: `tests/test_tool_manager.py` (recommande)

- `test_read_always_allowed()`
- `test_write_blocked_in_parent()`
- `test_evolution_mode_enables_write()`
