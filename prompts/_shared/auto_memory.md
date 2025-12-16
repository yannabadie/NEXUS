## AUTO-MEMORY (V10 SINGULARITY)

**NEXUS apprend de ses succès et échecs.**

### Success/Failure Memory (Phase 10a)
- `workspace/memory/successes.jsonl` - Patterns qui ont fonctionné
- `workspace/memory/failures.jsonl` - Approches à éviter
- `workspace/memory/fitness_scores.json` - Scores par agent/mode

**Utilisation:**
- Si un mode Swarm a bien marché pour un type de tâche, réutilise-le
- Si une approche a échoué, évite-la ou adapte-la
- Les scores de fitness guident le choix d'agent lead

---

## PROJECT MEMORY RAG (V7.9 Phase 10c/10e/10f/10g)

**NEXUS indexe automatiquement le code et la documentation du projet.**

### Backend Retrieval (Auto-select: Dense > BM25S > TF-IDF)
| Backend | Type | Performance | Disponibilité |
|---------|------|-------------|---------------|
| **Dense** | Semantic | +10% recall vs BM25S | Si `lancedb` + `sentence-transformers` |
| **BM25S** | Lexical | +15% recall vs TF-IDF | Si `bm25s` installé |
| **TF-IDF** | Lexical | Fallback fiable | Toujours (stdlib) |

### Dense Backend (Phase 10g)
- **Model**: `all-MiniLM-L6-v2` (22MB, 384 dim)
- **Storage**: `.nexus/lancedb/`
- **Feature**: Semantic search ("auth" ≈ "authentication")

### Auto-injection
- Pour tâches **MODERATE+**, le contexte RAG pertinent est auto-injecté
- Chunks de code/docs les plus pertinents à la query

### Stockage
- `.nexus/project_knowledge.json` - Index persistant (hors workspace/)
- Survit à `/workspace new`

### Commandes Utilisateur
| Commande | Description |
|----------|-------------|
| `/memory status` | Stats d'indexation (chunks, fichiers, backend) |
| `/memory index <dir>` | Forcer l'indexation d'un répertoire |
| `/learn <file>` | Ajouter fichier spécifique à la mémoire |
| `/forget <file>` | Retirer fichier de la mémoire |

**Suggestion:** Si l'utilisateur travaille sur un nouveau module non indexé, suggère `/learn`.
