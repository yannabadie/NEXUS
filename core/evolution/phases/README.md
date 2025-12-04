# Module: Evolution Phases

## Role Architectural

Pipeline d'evolution modulaire pour NEXUS V7.5 "HIVE MIND". Ce module decompose le cycle d'evolution en phases independantes, permettant:

- **Testabilite**: Chaque phase peut etre testee isolement
- **Scriptabilite**: Evolution sans REPL (mode batch)
- **Separation des responsabilites**: Logique UI dans REPL, logique metier ici

**Extraction**: V7.5 Phase 0a - Code extrait de `repl.py` (~1000 lignes)

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 7: Session Isolation** | Les phases utiliseront `TaskExecutionContext` pour isolation |
| **Phase 8: Self-Healing Swarm** | `BrainstormPhase` sera invoquee automatiquement sur echec Swarm |
| **Phase 9: Fast Path** | Validation tiered permettra bypass des phases lentes |

**Vision HIVE MIND**: Ce module est le coeur de la capacite de NEXUS a generer des agents specialises via evolution collaborative Gemini+Claude.

## Composants Cles

### Fichier: `__init__.py`
* **Fonction**: Exports publics du module phases
* **Exports**: `BrainstormPhase`, `CreatePhase`, `PromotePhase`, fonctions utilitaires
* **Notes d'Audit**: OK - Exports alignes avec implementation

---

### Fichier: `brainstorm.py`

**Classe**: `BrainstormPhase`

* **Fonction**: Generation de mutations via debat AI collaboratif (Gemini + Claude)
* **Interaction FSM**: Utilise `OrchestratorState.EVOLUTION_BRAINSTORM` (max 30 tours)
* **Protocoles Utilises**:
  - `MutationProposal` (dataclass)
  - Format SEARCH/REPLACE pour patches
  - JSON fallback pour compatibilite
* **Notes d'Audit**:
  - Utilise `robust_extract_json` pour parsing resilient
  - Reference `expected_asi_impact` (legacy) - mappe vers fitness score

**Methodes principales**:
| Methode | Description |
|---------|-------------|
| `run()` | Execute le cycle complet de brainstorming |
| `_extract_mutations()` | Parse SEARCH/REPLACE ou JSON |
| `_clear_context()` | Reset memoire court-terme avant debat |
| `request_abort()` | Permet interruption propre |

**Fonction utilitaire**: `run_brainstorm()` - Wrapper pour usage simplifie

---

### Fichier: `create.py`

**Classe**: `CreatePhase`

* **Fonction**: Creation d'instances enfant depuis propositions de mutation
* **Interaction FSM**: Aucune directe (phase offline)
* **Protocoles Utilises**:
  - `MutationProposal` (input)
  - `ChildCreationResult` (output)
  - `BIRTH_CERTIFICATE.json` pour tracabilite
* **Notes d'Audit**:
  - Import corrige: `from core.security import MutationValidator`
  - Copie parent vers `GENERATION_ACTIVE/<child_id>/`
  - Applique mutations (REPLACE, APPEND, PREPEND, INSERT_AFTER)

**Methodes principales**:
| Methode | Description |
|---------|-------------|
| `run()` | Cree N enfants depuis mutations |
| `create_child()` | Creation unitaire avec validation |
| `_apply_mutation()` | Application du patch au fichier cible |
| `_create_birth_certificate()` | Signe certificat de naissance |

**Fonction utilitaire**: `create_children()` - Wrapper pour usage simplifie

---

### Fichier: `promote.py`

**Classe**: `PromotePhase`

* **Fonction**: Promotion du gagnant et archivage des rejetes
* **Interaction FSM**: Aucune directe (phase offline)
* **Protocoles Utilises**:
  - `PromotionResult`, `ArchiveResult` (outputs)
  - `LINEAGE.json` via `core.evolution.lineage`
  - Git commits pour tracabilite
* **Notes d'Audit**:
  - Archive parent vers `ARCHIVE/GEN_XXX/`
  - Archive rejetes vers `ARCHIVE/rejected/`
  - Utilise `promote_child_to_parent()` et `archive_generation()`

**Methodes principales**:
| Methode | Description |
|---------|-------------|
| `promote_child()` | Promouvoir enfant gagnant |
| `archive_rejected_child()` | Archiver enfant rejete |

**Fonctions utilitaires**: `promote_child()`, `archive_child()` - Wrappers

---

## Phases Non Implementees (Placeholders)

| Phase | Fichier | Status |
|-------|---------|--------|
| Phase 3: Validate | `validate.py` | **NON IMPLEMENTE** - Utilise `TieredValidator` directement |
| Phase 4: Evaluate | `evaluate.py` | **NON IMPLEMENTE** - Utilise `evaluator.py` directement |

Ces phases sont gerees par `EvolutionManager` via delegation aux modules existants.

---

## Dependances et Interactions (Synapses)

```
                    EvolutionManager (manager.py)
                           |
        +------------------+------------------+
        |                  |                  |
   BrainstormPhase    CreatePhase       PromotePhase
        |                  |                  |
        v                  v                  v
   OrchestratorV7    MutationValidator    lineage.py
   (FSM control)     (security check)     (LINEAGE.json)
        |                  |                  |
        v                  v                  v
   Gemini+Claude     GENERATION_ACTIVE/   ARCHIVE/
   (AI debate)       (child instances)    (history)
```

**Imports critiques**:
- `core.evolution.models` - Dataclasses partagees
- `core.evolution.lineage` - Gestion LINEAGE.json
- `core.fsm.states` - OrchestratorState enum
- `core.security` - MutationValidator
- `core.utils.json_extractor` - Parsing JSON resilient

---

## Usage

```python
from core.evolution.phases import BrainstormPhase, CreatePhase, PromotePhase
from core.evolution.models import BrainstormResult

# Via EvolutionManager (recommande)
from core.evolution.manager import EvolutionManager
manager = EvolutionManager(workspace, nexus_root, config, orchestrator)
result = manager.run_evolution_cycle(child_count=3)

# Ou phases individuelles
brainstorm = BrainstormPhase(orchestrator, workspace)
result: BrainstormResult = brainstorm.run(parent_id, parent_path, child_count=3)
```

---

## Tests

**Fichier**: `tests/test_evolution_phases.py` (a creer)

Tests unitaires recommandes:
- `test_brainstorm_extracts_search_replace()`
- `test_create_applies_mutation()`
- `test_promote_updates_lineage()`
- `test_archive_moves_to_rejected()`
