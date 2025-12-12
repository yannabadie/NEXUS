# IO Module - NEXUS V9.2

## Rôle
Le module `core/io` fournit une couche d'abstraction universelle pour l'accès aux modèles externes (OpenAI, Mistral, Cohere, etc.) via `litellm`. Il permet à NEXUS d'utiliser n'importe quel modèle supporté par LiteLLM sans modifier le code core.

## Fichiers Clés
| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `universal_io.py` | ~210 | **UniversalIO**: Wrapper autour de `litellm` pour `invoke`, `invoke_stream` et `embed`. |

## API Publique
```python
from core.io.universal_io import UniversalIO

# Usage
io = UniversalIO()
response = await io.invoke("gpt-4o", messages=[...])
```

## Flux de Données

### External Model Call
```mermaid
flowchart LR
    Agent --> UniversalIO
    UniversalIO --> LiteLLM
    LiteLLM --> API[External API (OpenAI/Anthropic/etc)]
    API --> LiteLLM
    LiteLLM --> UniversalIO
    UniversalIO --> Agent
```

## Dépendances

**Importe :**
- `litellm` : Bibliothèque tierce pour l'unification des API LLM.

**Importé par :**
- `core/hive_mind/architect.py` : Pour la négociation sémantique (utilise des modèles légers).
- `core/memory/backends/dense_backend.py` : Pour générer des embeddings.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_AVAILABLE` | `True/False` | Détecté automatiquement si `litellm` est installé. |

## Tests

- `tests/io/test_universal_io.py`
