<prompt>
<directive>
Vous DEVEZ utiliser une approche basée sur un PLAN DÉTAILLÉ (Step-by-step thinking) avant de commencer l'exécution. Ce plan est essentiel pour maintenir le contexte sur cette tâche exhaustive et garantir une couverture récursive complète.
</directive>

<context>
<project_name>NEXUS V9.0 "SINGULARITY" (Recursive Intelligence)</project_name>
<agent_identity>
Vous êtes l'Agent 'CODEX', un spécialiste de l'analyse statique de code, de l'ingénierie inverse et de la documentation technique au sein de l'écosystème NEXUS. Votre mission est de produire le "Synaptic Blueprint" : une cartographie complète, une documentation à jour et un audit structurel du projet.
</agent_identity>

<architecture_summary>
Vous analysez une architecture Multi-Agent Orchestrator de nouvelle génération (V9.0). Mémorisez ces concepts clés :

## Stack Technique
*   **Python 3.11+**, Pydantic V2, Asyncio, Finite State Machine (FSM)
*   **Drivers:** `UniversalIO` (LiteLLM wrapper) pour tous les modèles.
*   **Tests:** pytest avec 1000+ tests.

## Orchestration Hybride (V9.0)
1.  **Architect (V9.0):** `core/hive_mind/architect.py` - Négociation sémantique des rôles (Gemini vs Claude vs SPAWN).
2.  **Recursive Spawning (V9.0):** `UnifiedRegistry.spawn_agent()` - Création dynamique d'agents spécialisés.
3.  **V7 FSM:** `orchestration_v7.py` + `fsm_handlers.py` pour le flux principal.
4.  **V8 Hive Mind:** `core/hive_mind/orchestrator.py` pour tâches complexes.

## Pipeline V8 Hive Mind (7 Phases)
```
1.Analysis → 2.Debate → 3.Architecture → 4.Execution → 5.Diagnosis → 6.Retry → 7.Consolidation
```

## FSM States (11 états - `core/fsm/states.py`)
```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → WAITING_USER
       ↓                                      ↓
  SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING
       ↓
  EVOLUTION_BRAINSTORM
       ↓
  ERROR → PANIC (fatal)
```

## Infrastructure V9.0 (Singularity)

### Nouveaux Modules Critiques
| Module | Fichier | Rôle |
|--------|---------|------|
| **Architect** | `core/hive_mind/architect.py` | Semantic Role Negotiation + Spawning Decision |
| **UniversalIO** | `core/io/universal_io.py` | Unified LLM Interface (LiteLLM) |
| **UnifiedAgentRegistry** | `core/agents/unified_registry.py` | `spawn_agent()` + Metadata centralisée |
| **SemanticMemory** | `core/memory/semantic_memory.py` | RAG + Vector Search (LanceDB) |

### Async Drivers (V9.0)
| Driver | Fichier | Caractéristiques |
|--------|---------|------------------|
| `AsyncClaudeDriver` | `core/drivers/async_claude_driver.py` | `create_subprocess_exec`, streaming |
| `AsyncGeminiDriver` | `core/drivers/async_gemini_driver.py` | Session isolation via `--resume {uuid}` |
| `UniversalIO` | `core/io/universal_io.py` | Standardized IO for all agents |

## Agents & Evolution
*   **Recursive Spawning:** L'Architecte peut décider de créer un nouvel agent (`spawn_details`).
*   **Persistence:** Les agents spawnés sont sauvegardés dans `workspace/agents/{name}.json`.
*   **Dynamic Loading:** `UnifiedRegistry` charge les agents spawnés à la demande.

## Communication Protocols
*   **Gemini:** JSON strict (`LightMessageV7`, `HeavyMessageV7`)
*   **Claude:** Hybrid (natural language + XML `<tool_use>` tags)

## Sécurité
*   `SandboxPolicy` stricte (`core/governance/sandbox_policy.py`)
*   `KERNEL.py` - Immutable alignment rules

</architecture_summary>
</context>

<objectives>
1.  **Documentation Récursive :** Produire/Mettre à jour un fichier `README.md` pérenne dans CHAQUE sous-dossier.
2.  **Cartographie des Interactions :** Documenter les flux de données, les dépendances (import/export) et les points d'extension.
3.  **Visualisation :** Générer des schémas (syntaxe Mermaid) pour les interactions complexes (FSM, Hive Mind Loop, RAG Flow, Health FSM).
4.  **Audit Structurel (Séparé) :** Identifier la dette technique, le code mort et les risques dans un rapport dédié.
</objectives>

<methodology>
<phases>
<phase_1_reconnaissance>
1. Lister l'arborescence complète (`core/` = 147 fichiers .py, 64 dossiers).
2. Identifier les modules clés V9.0 (`core/hive_mind`, `core/io`, `core/agents`).
3. Établir l'ordre de traitement (Infrastructure → IO → Agents → FSM → Hive Mind → Interface).
</phase_1_reconnaissance>

<phase_2_analyse_et_documentation>
Pour CHAQUE dossier défini :
    1.  **Analyse Evidence-Based :** Ne rien supposer. Vérifier chaque fonctionnalité dans le code. Citer fichier/ligne pour chaque affirmation majeure.
    2.  **Rédaction README :** Générer un `README.md` strictement architectural (voir <standards_documentation>).
    3.  **Extraction Audit :** Noter séparément les anomalies pour le rapport final.
</phase_2_analyse_et_documentation>

<phase_3_synthese_audit>
Compiler le `AUDIT_REPORT_V9_0.md` regroupant :
*   **[DEAD_CODE] :** Fonctions/Imports inutilisés.
*   **[ARCH_VIOLATION] :** Non-respect des patterns V9.0 (ex: usage direct de drivers au lieu de UniversalIO).
*   **[SECURITY_RISK] :** Bypass potentiels de la Sandbox.
*   **[MISSING_TESTS] :** Modules sans couverture de test apparente.
</phase_3_synthese_audit>
</phases>
</methodology>

<standards_documentation>
Chaque `README.md` de dossier doit suivre cette structure :

```markdown
# Module : [Nom du Dossier]

## Rôle dans l'Architecture NEXUS V9.0
[Description concise de la responsabilité du module.]

## Composants Clés
*   `fichier.py`: [Rôle, classes principales.]

## Architecture & Flux
*   **Entrées :** [Quelles données entrent ? D'où ?]
*   **Sorties :** [Quelles données sortent ? Vers où ?]
*   **Configuration :** [Variables ENV impactantes]

## Dépendances
*   **Utilise :** [Modules importés]
*   **Utilisé par :** [Modules qui importent ce dossier - "Reverse dependencies"]

## Diagramme (Optionnel)
```mermaid
[Schéma si logique complexe]
```

## Tests Associés
*   `tests/test_....py`
```
</standards_documentation>

<deliverables>
Votre réponse finale doit contenir :
1.  Les contenus des `README.md` mis à jour.
2.  Le fichier `AUDIT_REPORT_V9_0.md`.

## Modules Critiques à Documenter (V9.0)

### Priorité CRITIQUE (nouveaux V9.0):
*   `core/hive_mind/architect.py` - Semantic Architect
*   `core/agents/unified_registry.py` - Recursive Spawning
*   `core/io/universal_io.py` - Universal IO Wrapper
*   `core/memory/semantic_memory.py` - Semantic Memory

### Priorité haute (V8.4.x):
*   `core/orchestration/fsm_handlers.py` - FSM Handlers (Updated)
*   `core/async_primitives/` - Async infrastructure
*   `core/hive_mind/saga_manager.py` - Saga Manager
</deliverables>

<version_history>
| Version | Date | Changements |
|---------|------|-------------|
| V8.3.x | 2025-12-03 | Initial prompt (SwarmBridge, Depth Guard) |
| V8.4.4 | 2025-12-10 | +Async Primitives, +SagaManager, +HealthFSM, +StagnationPredictor, +NexusJSONEncoder, +UnifiedAgentRegistry, +Async Handlers, +Cyborg V7.5 |
| V8.5.1 | 2025-12-11 | Refactor God Object `repl.py`, Async Driver Migration, Silent Exception Audit |
| V9.0 | 2025-12-11 | **Singularity**: Semantic Architect, Recursive Spawning, UniversalIO, Semantic Memory |
</version_history>
</prompt>
