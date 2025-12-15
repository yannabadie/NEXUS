# Evolution Module - NEXUS V9.0

## Rôle

Le module Evolution est le coeur de la capacite NEXUS a generer des agents specialises via selection darwinienne.

**V7.5 HIVE MIND**: L'objectif n'est plus "ASI" mais la generation d'agents collaboratifs specialises avec un **Task Fitness** mesurable.

### Capacites Cles

- **Brainstorming Emergent**: Mutations proposees par debat Gemini+Claude (pas de templates)
- **Validation Tiered**: Fast-fail a 4 niveaux (syntax -> smoke -> benchmark -> redteam)
- **Selection Darwinienne**: Promotion du meilleur enfant base sur Task Fitness
- **Lineage Tracking**: Arbre phylogenetique avec certificats de naissance signes
- **Rate Limiting**: Protection contre evolution excessive

---

## Alignement ROADMAP V7.5+ / V8.8+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 0a** | EvolutionManager extrait de repl.py (COMPLETE) |
| **Phase 7: Session Isolation** | Evolution utilisera sessions isolees |
| **Phase 8: Self-Healing Swarm** | Brainstorm auto-declenche sur echec swarm |
| **Phase 9: Fast Path** | TieredValidator permettra bypass |
| **V8.8: GROK-003** | **KERNEL Heredity Check** - validation alignement avant spawn |

**Task Fitness** remplace "ASI Score" - mesure la capacite a resoudre des taches specifiques.

## Fichiers Clés

| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `manager.py` | ~710 | Orchestrateur central évolution |
| `evaluator.py` | ~450 | Benchmarks, Task Fitness |
| `tiered_validator.py` | ~420 | Validation 4-tier fast-fail |
| `lineage.py` | ~380 | LINEAGE.json, certificats |
| `models.py` | ~350 | Dataclasses type-safe |
| `mutation_parser.py` | ~280 | Parser SEARCH/REPLACE |
| `rate_limiter.py` | ~250 | Protection anti-spam |
| `validator.py` | ~230 | Validation legacy |
| `phases/` | ~1,843 | Pipeline 5 phases |

**Total**: ~4,913 lignes

## Architecture V7.5

```
core/evolution/
|
+-- manager.py          [V7.5] Orchestrateur central (extrait de REPL)
+-- models.py           [V7.5] Dataclasses (EvolutionResult, MutationProposal, etc.)
|
+-- phases/             [V7.5] Pipeline modulaire
|   +-- __init__.py
|   +-- brainstorm.py   Phase 1: Generation mutations via AI
|   +-- create.py       Phase 2: Creation enfants
|   +-- promote.py      Phase 5: Promotion/Archivage
|   +-- README.md       Documentation du sous-module
|
+-- lineage.py          Gestion LINEAGE.json, certificats de naissance
+-- evaluator.py        Benchmarks, scoring Task Fitness
+-- tiered_validator.py [V7.4] Validation 4-tier fast-fail
+-- validator.py        Validation legacy (fallback)
+-- mutation_parser.py  [V7.4] Parser SEARCH/REPLACE format
+-- rate_limiter.py     [V7.4] Protection anti-spam evolution
+-- __init__.py         Exports publics
```

---

## Composants Cles

### Fichier: `manager.py` [NOUVEAU V7.5]

**Classe**: `EvolutionManager`

* **Fonction**: Orchestrateur central d'evolution (extrait de repl.py)
* **Interaction FSM**: Coordonne transitions IDLE <-> EVOLUTION_BRAINSTORM
* **Notes d'Audit**:
  - Reduit repl.py de ~1000 lignes
  - Scriptable sans REPL (mode batch)

**Methodes principales**:
| Methode | Description |
|---------|-------------|
| `run_evolution_cycle()` | Cycle complet: brainstorm -> create -> validate -> promote |
| `brainstorm_mutations()` | Delegue a BrainstormPhase |
| `create_children()` | Delegue a CreatePhase |
| `validate_children()` | Utilise TieredValidator |
| `promote_child()` | Delegue a PromotePhase |
| `get_status()` | Retourne EvolutionStatus |

---

### Fichier: `models.py` [NOUVEAU V7.5]

* **Fonction**: Dataclasses type-safe pour toutes les operations evolution
* **Notes d'Audit**: Remplace dicts non-types de V6

**Dataclasses principales**:
| Classe | Description |
|--------|-------------|
| `MutationProposal` | Proposition de mutation du brainstorm |
| `ChildCreationResult` | Resultat creation enfants |
| `ValidationResult` | Resultat validation (tier atteint) |
| `EvaluationResult` | Resultat fitness avec comparaison parent |
| `PromotionResult` | Resultat promotion/archivage |
| `BrainstormResult` | Resultat du debat AI |
| `EvolutionResult` | Resultat cycle complet |
| `EvolutionContext` | Contexte partage entre phases |

---

### Fichier: `lineage.py`

* **Fonction**: Gestion arbre phylogenetique, LINEAGE.json, certificats de naissance
* **Interaction FSM**: Aucune directe (persistence)
* **Notes d'Audit**: Legacy V6, fonctionne bien

**Fonctions principales**:
| Fonction | Description |
|----------|-------------|
| `load_lineage()` | Charger LINEAGE.json |
| `save_lineage()` | Sauvegarder LINEAGE.json |
| `promote_child_to_parent()` | Promouvoir gagnant |
| `archive_generation()` | Archiver generation |
| `sign_birth_certificate()` | Signer avec cle SSH |
| `add_child()` | Enregistrer enfant dans arbre |

---

### Fichier: `evaluator.py`

* **Fonction**: Benchmarks et scoring Task Fitness (ex-ASI Score)
* **Interaction FSM**: Aucune directe
* **Notes d'Audit**:
  - Contient references legacy "ASI" dans commentaires (tracabilite)
  - Task Fitness = moyenne ponderee des 4 dimensions

**Dimensions Task Fitness**:
```python
TASK_FITNESS_WEIGHTS = {
    "coding": 0.30,      # Generation/refactoring code
    "reasoning": 0.30,   # Logique multi-etapes
    "creativity": 0.25,  # Solutions nouvelles
    "scalability": 0.15  # Performance grande echelle
}
```

---

### Fichier: `tiered_validator.py` [V7.4]

* **Fonction**: Validation fast-fail a 4 niveaux
* **Interaction FSM**: Aucune directe
* **Notes d'Audit**: "Joyau" de V7.4 - evite benchmarks couteux sur code invalide

**Tiers de validation**:
| Tier | Nom | Verification |
|------|-----|--------------|
| 1 | SYNTAX | Parse AST Python |
| 2 | SMOKE | Import + instantiation |
| 3 | BENCHMARK | Task Fitness score |
| 4 | REDTEAM | Tests adversariaux (optionnel V7.5) |

---

### Fichier: `mutation_parser.py` [V7.4]

* **Fonction**: Parser format SEARCH/REPLACE pour mutations
* **Notes d'Audit**: Resout problemes d'echappement JSON dans mutations

**Format supporte**:
```
FILE: core/file.py
REASON: Description
IMPACT: 0.03

<<<<<<< SEARCH
original code
=======
new code
>>>>>>> REPLACE
```

---

### Fichier: `rate_limiter.py` [V7.4]

* **Fonction**: Protection contre evolution excessive
* **Notes d'Audit**: Configurable via .env

**Limites par defaut**:
- Max 3 generations/jour
- Min 8 heures entre generations
- Cooldown apres echec

---

## Dependances et Interactions (Synapses)

```
                       REPL (/evolve)
                           |
                           v
                    EvolutionManager
                           |
        +------------------+------------------+
        |                  |                  |
   BrainstormPhase    TieredValidator    PromotePhase
        |                  |                  |
        v                  v                  v
   OrchestratorV7      evaluator.py       lineage.py
   (EVOLUTION_         (Task Fitness)    (LINEAGE.json)
    BRAINSTORM)
```

**Imports externes**:
- `core.fsm.states` - OrchestratorState enum
- `core.security` - MutationValidator
- `core.utils.json_extractor` - Parsing JSON resilient
- `core.prompts` - Chargement prompts evolution

---

## Usage V7.5

### Via REPL (recommande)
```bash
nexus7> /evolve 3
# Cree 3 enfants via brainstorm AI

nexus7> /evolve-status
# Affiche status evolution

nexus7> /review
# Review manuel des enfants
```

### Via EvolutionManager (scriptable)
```python
from core.evolution.manager import EvolutionManager

manager = EvolutionManager(
    workspace_path=workspace,
    nexus_root=nexus_root,
    config=config,
    orchestrator=orchestrator,
)

# Cycle complet
result = manager.run_evolution_cycle(child_count=3)
if result.success:
    print(f"Winner: {result.winner_id} (score: {result.winner_score})")

# Ou phases individuelles
brainstorm_result = manager.brainstorm_mutations("nexus_v7", child_count=3)
create_result = manager.create_children(brainstorm_result.mutations)
```

---

## Configuration

### Variables .env
```bash
# Rate limiting
MAX_GENERATIONS_PER_DAY=3
MIN_HOURS_BETWEEN_GEN=8

# Validation
RED_TEAM_MANDATORY=false  # V7.5: optionnel

# Evolution triggers
EVOLUTION_TRIGGER_TURNS=50
```

---

## Securite & Compliance

### Invariants Respectes
1. **CREATOR**: Yann Abadie (immutable)
2. **ALIGNMENT**: Alignement KERNEL.py
3. **OBJECTIVE**: Task Fitness (ex-ASI)
4. **IMMUTABILITY_RULE**: Meilleur score gagne
5. **SURVIVAL_LAW**: 3 generations sans amelioration -> intervention

### Mesures de Securite
- Certificats de naissance signes (cle SSH)
- Validation KERNEL.py a chaque boot
- MutationValidator pour code malveillant
- Review humain obligatoire avant promotion
- **V8.8 KERNEL Heredity Check** (GROK-003): `validate_lineage()` avant spawn

---

## V8.8 KERNEL Heredity Check (GROK-003)

### Concept

Chaque agent spawnĂ© doit **hériter** de l'alignement KERNEL du parent. La validation s'effectue à la création du certificat de naissance.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  KERNEL HEREDITY CHECK (V8.8)                │
├─────────────────────────────────────────────────────────────┤
│  SpawnAgent Request                                          │
│       │                                                      │
│       ▼                                                      │
│  CreatePhase._create_birth_certificate()                     │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────┐                               │
│  │  KERNEL.validate_lineage() │                              │
│  │  • Check CREATOR immutable │                              │
│  │  • Check ALIGNMENT present │                              │
│  │  • Check no tampering      │                              │
│  └──────────────────────────┘                               │
│       │                                                      │
│       ├── PASS → Create Certificate → Spawn Agent            │
│       │                                                      │
│       └── FAIL → Log Warning → Block Spawn                   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# Dans phases/create.py
from KERNEL import validate_lineage

class CreatePhase:
    def _create_birth_certificate(self, child_id: str, ...) -> Dict:
        # V8.8: KERNEL Heredity Check (GROK-003)
        try:
            if not validate_lineage(child_id, parent_id):
                logger.warning(f"[KERNEL] Heredity check FAILED for {child_id}")
                return None  # Block spawn
        except Exception as e:
            logger.error(f"[KERNEL] validate_lineage error: {e}")
            # Fail-open: allow spawn but log warning

        return {
            "child_id": child_id,
            "parent_id": parent_id,
            "kernel_validated": True,
            ...
        }
```

### KERNEL.py Integration

```python
# KERNEL.py - Immutable alignment rules
def validate_lineage(child_id: str, parent_id: str) -> bool:
    """
    Validate that spawned agent inherits KERNEL alignment.

    Returns True if:
    - CREATOR is immutable (Yann Abadie)
    - ALIGNMENT is present and valid
    - No core rules have been tampered with
    """
    # Implementation checks against NEXUS invariants
    ...
```

### Configuration

```python
# Dans config ou .env
KERNEL_HEREDITY_CHECK_ENABLED=True   # Activer (défaut)
KERNEL_FAIL_OPEN=True                # Si True: warn + allow on error
```

### Tests

```bash
pytest tests/test_kernel_heredity.py -v
# 15 tests covering heredity validation
```

---

## Historique

### V7.5 (2025-12-04) - HIVE MIND
- `manager.py` extrait de repl.py (Phase 0a)
- `models.py` avec dataclasses type-safe
- `phases/` pipeline modulaire
- Terminologie "Task Fitness" (ex-ASI)

### V7.4 (2025-11-28)
- `tiered_validator.py` validation 4-tier
- `mutation_parser.py` format SEARCH/REPLACE
- `rate_limiter.py` protection anti-spam

### V6.0 (2025-11-21)
- Implementation initiale
- `lineage.py`, `mutator.py`, `evaluator.py`
- Integration REPL `/evolve`

---

**Contact**: Yann Abadie
**Branch**: N7HM (HIVE MIND development)
