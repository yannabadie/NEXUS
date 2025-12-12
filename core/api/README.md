# Module: core/api

## Rôle dans l'Architecture NEXUS V9.2
Ce module fournit des utilitaires pour la gestion des appels API externes, principalement la limitation de débit (Rate Limiting) pour éviter de dépasser les quotas des fournisseurs LLM (Anthropic, Google).

## Composants Clés
*   `rate_limiter.py`: Gestionnaire de quotas (Token bucket ou fenêtre glissante).

## Architecture & Flux
*   **Entrées :** Demandes d'appel API.
*   **Sorties :** Autorisation ou attente (sleep).
*   **Configuration :** Limites définies dans `config.py` ou `.env`.

## Dépendances
*   **Utilise :** `asyncio`, `time`.
*   **Utilisé par :** `core.drivers`, `core.io.universal_io`.
