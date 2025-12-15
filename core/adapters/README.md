# Adapters Module - NEXUS V9.0

## Rôle

Fournit des adaptateurs bidirectionnels entre les types d'analyse utilisés dans les pipelines Swarm et HiveMind. Permet l'interopérabilité entre sous-systèmes sans couplage fort.

## Fichiers Clés

| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `analysis_adapter.py` | ~238 | Conversion TaskAnalysis ↔ IndependentAnalysis |
| `__init__.py` | ~14 | Exports publics |

## API Publique

```python
from core.adapters import AnalysisAdapter

# HiveMind → Swarm
task_analysis = AnalysisAdapter.to_task_analysis(independent_analysis, raw_input)

# Swarm → HiveMind
independent = AnalysisAdapter.to_independent_analysis(task_analysis, agent_id)

# Helpers
complexity_str = AnalysisAdapter.complexity_to_string(TaskComplexity.COMPLEX)
complexity_enum = AnalysisAdapter.string_to_complexity("complex task")
```

## Flux de Données

```
┌─────────────────┐                          ┌──────────────────┐
│  HiveMind       │                          │  Swarm           │
│  Pipeline       │                          │  Engine          │
│                 │                          │                  │
│ IndependentAna- │  ──to_task_analysis()──► │ TaskAnalysis     │
│ lysis           │                          │                  │
│                 │  ◄─to_independent_ana─── │                  │
└─────────────────┘       lysis()            └──────────────────┘
```

### Mapping des Champs

**HiveMind → Swarm** (perte de données):
- `complexity_assessment` → `complexity` (fuzzy match)
- `confidence` → `confidence`
- `task_understanding` → `raw_input` (fallback)
- **LOST**: `agent_id`, `reasoning`, `required_capabilities`, `potential_risks`

**Swarm → HiveMind** (perte de données):
- `complexity` → `complexity_assessment` (enum name)
- `raw_input` → `task_understanding`
- `confidence` → `confidence`
- **LOST**: `domains`, `requires_*`, `fit_scores`, `detected_keywords`

## Dépendances

**Importe**:
- `core/swarm/task_analyzer.py`: TaskAnalysis, TaskComplexity, TaskDomain
- `core/hive_mind/types.py`: IndependentAnalysis

**Importé par**:
- `tests/test_analysis_adapter.py:15`

## Configuration

Aucune configuration externe. Les mappings sont définis en constantes:

| Constante | Description |
|-----------|-------------|
| `COMPLEXITY_MAP` | Fuzzy string → TaskComplexity |
| `DOMAIN_PATTERNS` | Keywords → TaskDomain |

## Tests

- `tests/test_analysis_adapter.py`

## Notes

- Conversion **NON lossless** - certains champs n'ont pas d'équivalents
- Voir `IMPACT_ANALYSIS_V8.2.md` pour détails du mapping
- Ajouté en V8.2.0a pour unifier les pipelines Swarm/HiveMind
