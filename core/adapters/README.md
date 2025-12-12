# Module: core/adapters

## Rôle dans l'Architecture NEXUS V9.2
Ce module contient des adaptateurs pour transformer les données entre différents formats ou composants, assurant le découplage entre les couches (ex: Analyse -> FSM).

## Composants Clés
*   `analysis_adapter.py`: Adapte les résultats de l'analyseur de tâches (`TaskAnalyzer`) pour l'Orchestrateur ou le Swarm Engine.

## Architecture & Flux
*   **Entrées :** Objets d'analyse bruts.
*   **Sorties :** Structures de données normalisées pour la FSM.

## Dépendances
*   **Utilise :** `core.hive_mind.types`, `core.fsm.states`.
*   **Utilisé par :** `core.orchestration.fsm_handlers`, `core.swarm.engine`.
