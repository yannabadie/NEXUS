# Module : Memory - NEXUS V7.8 "HIVE MIND"

Le "Cortex" de NEXUS - Apprentissage opérationnel + Connaissance projet (Phase 10).

## Rôle dans l'Architecture NEXUS V7.8

Le module Memory implémente **deux systèmes de mémoire complémentaires** :

| Système | Phase | Fonction | Persistance |
|---------|-------|----------|-------------|
| **AutoMemory** | 10a/10b | Apprentissage des succès/échecs Swarm | `workspace/memory/` |
| **ProjectMemory** | 10c | RAG sur le codebase projet | `.nexus/project_knowledge.json` |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MEMORY MODULE V7.8                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────────────┐    ┌──────────────────────────┐         │
│   │      AUTO-MEMORY         │    │    PROJECT MEMORY        │         │
│   │      (Phase 10a/b)       │    │      (Phase 10c)         │         │
│   ├──────────────────────────┤    ├──────────────────────────┤         │
│   │ • Success patterns       │    │ • TF-IDF RAG indexing    │         │
│   │ • Failure avoidance      │    │ • Code chunking          │         │
│   │ • Mode recommendations   │    │ • Context injection      │         │
│   │ • Agent fitness scores   │    │ • /learn, /forget cmds   │         │
│   └───────────┬──────────────┘    └───────────┬──────────────┘         │
│               │                               │                         │
│               ▼                               ▼                         │
│   ┌──────────────────────────┐    ┌──────────────────────────┐         │
│   │  workspace/memory/       │    │  .nexus/                 │         │
│   │  ├─ successes.jsonl      │    │  └─ project_knowledge.json│        │
│   │  ├─ failures.jsonl       │    │     (survit /workspace new)│       │
│   │  └─ fitness_scores.json  │    └──────────────────────────┘         │
│   └──────────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Composants Principaux

| Fichier | Rôle | Classes/Fonctions clés |
|---------|------|------------------------|
| `auto_memory.py` | Apprentissage opérationnel | `AutoMemory`, `MemoryEntry`, `get_auto_memory()` |
| `success_memory.py` | Stockage patterns de succès | `SuccessMemory`, `SuccessEntry` |
| `project_memory.py` | **[V7.8]** RAG TF-IDF sur codebase | `ProjectMemory`, `Chunk`, `IndexStats` |
| `__init__.py` | Exports module | `get_auto_memory()`, `ProjectMemory`, `Chunk` |

## Phase Status

| Phase | Feature | Status | Version |
|-------|---------|--------|---------|
| **10a** | Success Memory | COMPLETE | V7.5 |
| **10b** | Memory-Augmented Mode Selection | COMPLETE | V7.6 |
| **10c** | Project Memory RAG | COMPLETE | V7.8 |

---

## 1. AutoMemory (Phase 10a/10b)

Système d'apprentissage des patterns opérationnels.

### Fonctionnement

```python
from core.memory import get_auto_memory

memory = get_auto_memory()

# 1. Enregistrer un succès
memory.record_success(
    task_type="code_review",
    task_description="Review auth module",
    swarm_mode="PING_PONG",
    lead_agent="claude",
    duration_seconds=45.0,
    score=0.9
)

# 2. Obtenir une recommandation
rec = memory.get_recommendation(task_type="code_review")
# {"suggested_mode": "PING_PONG", "confidence": 0.8, "modes_to_avoid": ["PARALLEL"]}

# 3. Vérifier les modes à éviter
should_avoid = memory.should_avoid("security_audit", "PARALLEL")  # True
```

### Stockage (workspace/memory/)

| Fichier | Format | Contenu |
|---------|--------|---------|
| `successes.jsonl` | JSONL | Patterns de tâches réussies |
| `failures.jsonl` | JSONL | Anti-patterns (échecs) |
| `fitness_scores.json` | JSON | Scores fitness par agent/type |

---

## 2. ProjectMemory (Phase 10c) **[NOUVEAU V7.8]**

Système RAG (Retrieval-Augmented Generation) zero-dependency pour indexer et récupérer des connaissances projet.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ProjectMemory RAG                            │
├─────────────────────────────────────────────────────────────────┤
│  Indexing:                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  File    │ -> │  Chunk   │ -> │  Terms   │ -> │  Store   │  │
│  │  Read    │    │  Split   │    │  Extract │    │  JSON    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  Retrieval:                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Query   │ -> │  Terms   │ -> │ TF-IDF   │ -> │  Top K   │  │
│  │  Input   │    │  Extract │    │  Score   │    │  Chunks  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Stratégies de Chunking

| Type fichier | Stratégie | Description |
|--------------|-----------|-------------|
| `.py` | Function/Class | Split sur `def`, `class`, `async def` |
| `.md` | Section | Split sur headers (`#`, `##`, etc.) |
| Autres | Lines | 50 lignes avec 10 lignes overlap |

### Scoring : TF-IDF Weighted Jaccard

```
Score = Σ(IDF[term] for term ∈ query ∩ chunk) / Σ(IDF[term] for term ∈ query)

IDF(term) = log(N / (1 + df(term)))
```

### Utilisation

```python
from core.memory import ProjectMemory

# Initialisation (stockage à NEXUS_ROOT/.nexus/)
memory = ProjectMemory(nexus_root=Path("/path/to/project"))

# Indexer des fichiers
memory.index_file(Path("core/orchestration_v7.py"))
memory.index_directory(Path("core/"), extensions=[".py", ".md"])

# Récupérer des chunks pertinents
chunks = memory.retrieve("FSM state handling", limit=5)

# Formater pour contexte agent
context = memory.format_chunks_for_context(chunks, max_chars=3000)

# Oublier un fichier
memory.forget(Path("core/deprecated.py"))

# Statistiques
stats = memory.get_stats()
# IndexStats(total_files=15, total_chunks=127, total_terms=843)
```

### Commandes REPL

| Commande | Description |
|----------|-------------|
| `/learn [path]` | Indexer fichier/dossier (défaut: `core/`) |
| `/forget [path]` | Retirer de l'index |
| `/memory-status` | Afficher stats mémoire |

### Persistance

**Emplacement :** `.nexus/project_knowledge.json` (à NEXUS_ROOT, PAS dans workspace/)

**Pourquoi ?** La mémoire projet survit à `/workspace new` car la connaissance factuelle du codebase est indépendante des sessions de travail.

### Injection Automatique

Pour les tâches de complexité **MODERATE+**, `ContextBuilder` injecte automatiquement les chunks pertinents :

```python
# Dans context_builder.py
def _get_project_knowledge(self) -> str:
    if complexity.value < TaskComplexity.MODERATE.value:
        return ""  # Pas d'injection pour TRIVIAL/SIMPLE

    chunks = self._orch.project_memory.retrieve(objective, limit=3)
    return self._orch.project_memory.format_chunks_for_context(chunks)
```

---

## Interactions et Flux de Données

```mermaid
graph TB
    subgraph "Memory Module"
        AM[AutoMemory]
        PM[ProjectMemory]
    end

    subgraph "Consumers"
        MS[ModeSelector]
        CB[ContextBuilder]
        REPL[REPL Commands]
    end

    subgraph "Storage"
        WM[workspace/memory/]
        NX[.nexus/project_knowledge.json]
    end

    AM -->|recommendations| MS
    AM -->|save/load| WM

    PM -->|inject context| CB
    PM -->|save/load| NX

    REPL -->|/learn, /forget| PM

    MS -->|mode selection| HSE[HybridSwarmEngine]
    CB -->|enriched context| HSE
```

## Différence Logging vs Memory

| Aspect | Logging | AutoMemory | ProjectMemory |
|--------|---------|------------|---------------|
| **Tracks** | Événements techniques | Résultats fonctionnels | Connaissance code |
| **Purpose** | Debug/Observabilité | Optimisation modes | Contexte RAG |
| **Persistence** | Logs rotatifs | JSONL permanent | JSON permanent |
| **Used by** | Développeurs | ModeSelector | ContextBuilder |

## Notes d'Audit Local

### [V7.8] Nouveautés Phase 10c
- `project_memory.py` ajouté (685 lignes)
- Exports mis à jour dans `__init__.py`
- Intégration ContextBuilder pour injection auto
- 50 tests unitaires (`tests/test_project_memory.py`)

### Points d'attention
- **MAX_CHUNKS = 5000** : Limite globale pour éviter explosion mémoire
- **MIN_CHUNK_SIZE = 50** : Fichiers < 50 chars ignorés
- **Excluded dirs** : `__pycache__`, `.git`, `venv`, `workspace`

## Voir Aussi

- [core/swarm/README.md](../swarm/README.md) - Utilise AutoMemory pour sélection modes
- [core/orchestration/README.md](../orchestration/README.md) - Intègre ProjectMemory via ContextBuilder
- [docs/phases/PHASE_10c_PROJECT_MEMORY.md](../../docs/phases/PHASE_10c_PROJECT_MEMORY.md) - Documentation détaillée Phase 10c
