# AUDIT GLOBAL : PROJET NEXUS (2025-11-28)

**Document de Référence - État Réel du Codebase**
*Généré par l'Agent d'Audit V7*

Ce document recense l'état exact du projet NEXUS, dossier par dossier, en distinguant le code actif, les reliquats legacy, et les documents de vision.

---

## 1. RACINE `20_NEXUS/`

Lieu de déploiement et de configuration globale.

| Fichier / Dossier | Statut | Description |
|-------------------|--------|-------------|
| `NEXUS_V7_CHRYSALIS/` | **ACTIF** | **Cœur du système.** Contient tout le code source V7. |
| `GENERATION_ACTIVE/` | **WORKSPACE** | Dossier de travail pour les évolutions (`test_run_1`). Contient les enfants générés. |
| `ARCHIVE/` | **HISTORIQUE** | Stocke les anciennes générations de code (ex: `GEN_006`). |
| `archives/` | **DOCS** | Archives documentaires (brainstorming, planning, tests). |
| `BENCHMARKS/` | **OUTILS** | Scripts d'évaluation de performance ASI (Legacy V6 mais encore présents). |
| `audit/`, `docs/`, `tests/` | **SUPPORT** | Dossiers de documentation et de tests globaux. |
| `KERNEL.py` | **CRITIQUE** | **Loi Fondamentale.** Fichier immuable définissant l'identité et l'alignement. |
| `LINEAGE.json` | **MÉTADONNÉE** | Registre généalogique des versions (Parents/Enfants). |
| `SESSION_CONTINUITY.md` | **MÉMOIRE** | Journal de bord persistant entre sessions. |
| `ROADMAP_NEXUS_V8.md` | **VISION** | Roadmap V8 fraîchement mise à jour (avec GraphRAG). |
| `ROADMAP_NEXUS_V7.md` | **VISION** | Roadmap de la version actuelle. |
| `requirements.txt` | **LEGACY** | Probablement hérité de V6. Les vrais deps sont dans `NEXUS_V7_CHRYSALIS/requirements_v7.txt`. |

---

## 2. CŒUR `NEXUS_V7_CHRYSALIS/`

Le code source actif. Architecture modulaire V7.

### Point d'Entrée
*   `nexus7.py` : Lanceur principal. Initialise le Kernel et l'Orchestrator.

### Structure `core/`
| Module | État | Rôle |
|--------|------|------|
| `orchestration_v7.py` | **ACTIF** | **Cerveau FSM.** Gère les états (IDLE, BRAINSTORM, SWARM). Code robuste et persistant. |
| `config.py` | **ACTIF** | Gestionnaire de configuration centralisé (env vars, modèles). |
| `bootstrap/` | **ACTIF** | `auto_bootstrap.py` : Analyseur de projet capable de générer `NEXUS.md`. |
| `drivers/` | **ACTIF** | `gemini_driver_v7.py`, `claude_driver_hybrid.py`. Interfaces LLM. |
| `execution/` | **ACTIF** | `tool_manager.py` : Exécuteur d'outils (FS, Shell, Git). Sandboxed. |
| `fsm/` | **ACTIF** | États de la machine (Stagnation, PlanHealth, Panic). |
| `interface/` | **ACTIF** | `repl.py` : Interface CLI interactive. Gère `/evolve`, `/specialize`. |
| `reasoning/` | **PARTIEL** | Semble contenir la logique de pensée (Chain of Thought?), à vérifier. |
| `routing/` | **ACTIF** | `model_router.py` : Décide qui de Claude ou Gemini prend la tâche. |
| `security/` | **ACTIF** | Vérifications d'intégrité et permissions. |
| `swarm/` | **ACTIF** | `HybridSwarmEngine` : Moteur de collaboration multi-agents (Sprint 9). |
| `synapse/` | **ACTIF** | `memory_v7.py` (Blackboard RAM + Global Context JSON), `protocol_v7.py` (Pydantic). |
| `telemetry/` | **ACTIF** | `TelemetryCollector` : Enregistre les métriques d'exécution. |

**Observation :** L'architecture est très propre et modulaire. Le "Swarm" et le "Routing" sont bien séparés du FSM principal.

---

## 3. ATELIERS `GENERATION_ACTIVE/`

Zone de mutation et de test.

*   `test_run_1/` : Contient une instance complète de NEXUS. C'est probablement un "enfant" généré lors d'un cycle d'évolution ou de test. Il possède sa propre structure `core/`, `nexus7.py`, etc.

---

## 4. OUTILS `BENCHMARKS/`

Outils d'évaluation ASI (héritage V6).

*   `asi_proximity.py` : Calcule le score ASI.
*   `asi_benchmark.py` : Script de lancement.
*   `coding/` : Tests de codage.
*   **Note :** Ces outils semblent être *externes* au Core V7 (qui a peut-être ses propres métriques internes via `telemetry`), mais sont utilisés pour l'évaluation globale "ASI Score".

---

## 5. ANALYSE DES ÉCARTS (Roadmap vs Réalité)

| Feature | Roadmap V7 | Réalité Code | Verdict |
|---------|------------|--------------|---------|
| **Swarm Engine** | ✅ Prévu | ✅ Présent (`core/swarm/`) | **CONFORME** |
| **Bootstrap** | ✅ Prévu | ✅ Présent (`core/bootstrap/`) | **CONFORME** |
| **Persistance** | ⏳ V7.8 | ⚠️ Partiel | `memory_v7.py` a maintenant le Global Context JSON (ajout récent), mais pas encore de Vector DB. |
| **GraphRAG** | ⏳ V8 | ❌ Absent | Logique purement V8, absente du code V7 (normal). |
| **Opus Integration** | ✅ Prévu | ✅ Présent | `claude_driver_hybrid.py` et `model_router.py` gèrent Opus. |
| **Self-Healing** | ✅ Prévu | ✅ Présent | `panic_system.py` et `plan_health.py` dans `core/fsm/`. |

---

## 6. CONCLUSION

Le projet est dans un état **extrêmement sain**.
*   La structure correspond à la documentation.
*   Il n'y a pas de "code fantôme" majeur (les dossiers `BENCHMARKS` sont utiles).
*   L'architecture V7 est solidement implémentée autour d'un FSM robuste et d'un moteur Swarm fonctionnel.
*   La transition vers V8 est prête à démarrer sur des bases solides (Global Memory initiée).

**Prochaine étape recommandée :** Nettoyer `requirements.txt` à la racine pour éviter la confusion avec `NEXUS_V7_CHRYSALIS/requirements_v7.txt`.
