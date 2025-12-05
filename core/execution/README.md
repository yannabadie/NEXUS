# Module: Execution - Tool Dispatch Layer

**Version**: 7.8 (ADAPTIVE EVOLUTION)
**Last Updated**: 2025-12-05

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
| **Phase 12.5: Dynamic Tools** ✅ | Agents peuvent creer leurs propres outils |

---

## Composants Cles

### Fichier: `tool_manager.py`

**Classe**: `ToolManager`

* **Fonction**: Dispatcher central pour les 15 outils NEXUS (11 core + 4 dynamic)
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
| `create_tool` | Creer outil dynamique (V7.8) | Workspace only |
| `delete_tool` | Supprimer outil dynamique | Workspace only |
| `list_dynamic_tools` | Lister outils crees | Toujours autorise |
| `run_dynamic_tool` | Executer outil dynamique | Workspace only |

---

### Fichier: `__init__.py`

* **Fonction**: Exports publics (ToolManager)
* **Notes d'Audit**: OK

### Fichier: `dynamic_tools.py` (V7.8 Phase 12.5)

**Classe**: `DynamicToolManager`

* **Fonction**: Permet aux agents de creer des outils Python a la volee
* **Securite**: Code valide via AST + execution subprocess isolee
* **Notes d'Audit**: OK - 52 tests (30 securite + 22 fonctionnels)

**Outils Dynamiques (4 nouveaux outils)**:

| Outil | Description | Permissions |
|-------|-------------|-------------|
| `create_tool` | Cree un outil Python avec code valide | Workspace only |
| `delete_tool` | Supprime un outil dynamique | Workspace only |
| `list_dynamic_tools` | Liste les outils crees | Toujours autorise |
| `run_dynamic_tool` | Execute un outil dynamique | Workspace only |

**Workflow de creation d'outil**:
```
Agent Request: create_tool(name, code, description)
     |
     v
CodeValidator.validate_code() [AST Analysis]
     |
     +--[UNSAFE]--> ValidationError (violations listees)
     |
     +--[SAFE]--> Tool File Created (workspace/tools/generated/{name}.py)
                  Metadata Saved ({name}.meta.json)
                  Tool Registered
```

**Workflow d'execution**:
```
Agent Request: run_dynamic_tool(name, args)
     |
     v
subprocess.run(python, tool.py, json.dumps(args))
     |
     +--[TIMEOUT 30s]--> TimeoutError
     |
     +--[SUCCESS]--> JSON Output parsed
     |
     +--[ERROR]--> Error captured from stderr
```

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

**Fichier**: `tests/test_dynamic_tools.py` (V7.8)

52 tests couvrant:
- **TestCodeValidatorSecurity** (30 tests): AST validation, patterns bloques
- **TestDynamicToolManager** (15 tests): CRUD outils, execution, timeout
- **TestDynamicToolsIntegration** (3 tests): End-to-end lifecycle
- **TestEdgeCases** (4 tests): Unicode, erreurs, noms invalides

```bash
# Executer les tests
python -m pytest tests/test_dynamic_tools.py -v
```
