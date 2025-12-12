# Module: core/agents

## Rôle dans l'Architecture NEXUS V9.2
Ce module gère l'identité, la création et la persistance des agents. Il implémente le "Recursive Spawning" permettant à NEXUS de créer des sous-agents spécialisés.

## Composants Clés
*   `unified_registry.py`: Registre central (`UnifiedAgentRegistry`). Gère Gemini, Claude et les agents spawnés.
*   `base.py`: Classe abstraite `BaseAgent`.

## Architecture & Flux
*   **Spawning :** `spawn_agent()` crée un dossier dans `workspace/agents/{name}/` avec sa configuration.
*   **Chargement :** Au démarrage, le registre scanne `workspace/agents/` pour charger les spécialistes.
*   **Routing :** L'Orchestrateur demande un agent par son nom (`@sql_expert`) au registre.

## Dépendances
*   **Utilise :** `core.config`, `core.io`.
*   **Utilisé par :** `core.orchestration`, `core.hive_mind.architect`.
