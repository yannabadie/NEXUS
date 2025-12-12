# Module: core/hive_mind

## Rôle dans l'Architecture NEXUS V9.2
Ce module implémente l'intelligence de haut niveau ("The Architect"). Il supervise l'orchestrateur, gère les tâches complexes (Sagas) et décide des stratégies d'évolution.

## Composants Clés
*   `architect.py`: L'Architecte. Analyse les logs, détecte la dette technique et propose des refactorings.
*   `saga_manager.py`: Gestionnaire de tâches longue durée (multi-étapes, persistant).
*   `orchestrator.py`: (Legacy V8) Ancienne logique de coordination, progressivement remplacée par `architect.py`.

## Architecture & Flux
*   **Architect Loop :** Observe -> Plan -> Spawn -> Verify.
*   **Saga :** Une tâche complexe est découpée en étapes persistées dans `workspace/.nexus/sagas/`.

## Dépendances
*   **Utilise :** `core.agents`, `core.memory`, `core.swarm`.
*   **Utilisé par :** `nexus7.py` (Mode autonome).
