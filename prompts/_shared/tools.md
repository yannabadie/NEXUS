## OUTILS DISPONIBLES (15+ outils - TOUS accessibles aux deux agents)

### Fichiers & Code
| Outil | Description |
|-------|-------------|
| `read` | Lire fichier |
| `write` | Créer/écraser fichier (workspace/) |
| `edit` | Search & replace |
| `list_dir` | Lister répertoire |

### Recherche
| Outil | Description |
|-------|-------------|
| `glob` | Trouver fichiers par pattern |
| `grep` | Chercher dans le code (regex) |
| `web_search` | Recherche Google |
| `web_fetch` | Récupérer contenu URL |

### Exécution
| Outil | Description |
|-------|-------------|
| `bash` | Commandes shell (**SANDBOXED** - voir security.md) |
| `git` | Opérations Git |

### Planification
| Outil | Description |
|-------|-------------|
| `todo_write` | Plan partagé Gemini↔Claude |

### Dynamic Tools (V7.8 Phase 12.5)
| Outil | Description |
|-------|-------------|
| `create_tool` | Créer script Python dynamique (validé AST) |
| `run_dynamic_tool` | Exécuter outil créé |
| `delete_tool` | Supprimer outil dynamique |
| `list_dynamic_tools` | Lister outils disponibles |

**Exemple:** Créer un outil pour parser JSON complexe au lieu d'un bash one-liner.

### Agent Tools (V7.8 Phase 15)
| Outil | Description |
|-------|-------------|
| `agent_{name}` | Invoquer agent spawné comme outil |

**Agents disponibles:** Listés via `/agents` ou `list_dir workspace/agents/`

**Exemple:** Si `sql_expert` est spawné → `agent_sql_expert` devient disponible.

```json
{
  "tool_name": "agent_sql_expert",
  "arguments": {"task": "Optimize this query for performance"}
}
```
