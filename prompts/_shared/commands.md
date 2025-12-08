## COMMANDES REPL (V7.9)

**L'utilisateur peut invoquer ces commandes. Tu peux les suggérer quand pertinent.**

### Collaboration (Swarm)
| Commande | Description |
|----------|-------------|
| `/swarm <task>` | Route tâche via Hybrid Swarm Engine |
| `/swarm-status` | Mode actuel + métriques DyLAN |
| `/pool-stats` | Scores importance par agent |

### Evolution & Agents
| Commande | Description |
|----------|-------------|
| `/evolve [n]` | Créer n enfants (default: 3) |
| `/spawn <role>` | Créer agent spécialisé |
| `/agents` | Lister agents spawnés |
| `/specialize <mission>` | Créer spinoff spécialisé |
| `/review` | Review enfants pending |

### Memory & Monitoring
| Commande | Description |
|----------|-------------|
| `/memory status` | Stats Project Memory RAG |
| `/memory index <dir>` | Forcer indexation |
| `/budget` | Status budget quotidien |
| `/telemetry` | Rapport 7 jours |
| `/telemetry export` | Export CSV |

### Workspace
| Commande | Description |
|----------|-------------|
| `/workspace` | Status workspace actuel |
| `/workspace new` | Nouveau workspace (memory préservée) |
| `/bootstrap` | Analyse projet et génère NEXUS.md |

### System
| Commande | Description |
|----------|-------------|
| `/help` | Aide complète |
| `/tutorial` | Guide interactif (5 étapes) |
| `/quickstart` | Résumé rapide |
| `/status` | État orchestrateur + FSM |
| `/doctor` | Diagnostics système |
| `/reset` | Reset état (si ERROR) |
| `/chat` | Mode chat-only (pas d'outils) |

---

## QUAND SUGGÉRER UNE COMMANDE

| Situation | Commande à suggérer |
|-----------|---------------------|
| Nouveau projet non analysé | `/bootstrap` |
| Fichier non indexé | `/learn <file>` ou `/memory index` |
| Budget faible | `/budget` pour vérifier |
| Tâche complexe multi-agents | `/swarm <task>` |
| Performance agents inconnue | `/pool-stats` |
| Besoin d'expert domaine | `/spawn <role>` |

**Note:** Les agents ne peuvent PAS exécuter ces commandes directement. Ils peuvent seulement les suggérer à l'utilisateur.
