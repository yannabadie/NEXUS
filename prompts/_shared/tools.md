## OUTILS DISPONIBLES (16+ outils - TOUS accessibles aux deux agents)

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

### Swarm Delegation (V8.3.1)
| Outil | Description |
|-------|-------------|
| `swarm_delegate` | Déléguer une sous-tâche au Swarm Engine |

**Modes disponibles:** `parallel`, `sequential`, `lead_support`, `ping_pong`, `specialist`, `red_blue`

**Arguments:**
- `task` (requis): Description de la sous-tâche
- `mode` (optionnel, défaut: "specialist"): Mode de collaboration
- `phase` (optionnel): Phase HiveMind actuelle (pour validation guardrails)
- `context_categories` (optionnel): Catégories de contexte à inclure

**Exemples:**

```json
{
  "tool_name": "swarm_delegate",
  "arguments": {
    "task": "Analyser auth.py et security.py en parallèle",
    "mode": "parallel"
  }
}
```

```json
{
  "tool_name": "swarm_delegate",
  "arguments": {
    "task": "Débattre de l'approche d'authentification",
    "mode": "red_blue",
    "phase": "debate"
  }
}
```

**⚠️ Anti-Recursion:** Limité à `MAX_SWARM_DEPTH = 2` pour éviter les boucles infinies.
- Niveau 0: Invocation directe → OK
- Niveau 1: Sub-agent invoque swarm_delegate → OK
- Niveau 2: Sub-sub-agent tente swarm_delegate → BLOQUÉ

**Quand utiliser:**
- ✅ Tâches pouvant bénéficier de collaboration multi-agents
- ✅ Debates adversariaux (red_blue)
- ✅ Analyses parallèles indépendantes
- ❌ Tâches simples (overhead inutile)
- ❌ Depuis un agent déjà spawné par Swarm (risque récursion)
