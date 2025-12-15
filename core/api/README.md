# API Module - NEXUS V9.0

## Rôle

Gère les interactions avec les APIs externes (Gemini, Claude). Fournit un rate limiter token-bucket pour éviter les erreurs 429 en mode PARALLEL.

## Fichiers Clés

| Fichier | Lignes | Responsabilité |
|---------|--------|----------------|
| `rate_limiter.py` | ~345 | Token bucket rate limiting (async + sync) |
| `__init__.py` | ~14 | Exports publics |

## API Publique

```python
from core.api import APIRateLimiter, RateLimitExceeded

# Usage direct
limiter = APIRateLimiter(requests_per_minute=60, burst_size=10)
await limiter.acquire_async()  # Async (asyncio)
limiter.acquire_sync()          # Sync (ThreadPoolExecutor)

# Via registry (recommandé - singleton par provider)
from core.api.rate_limiter import get_rate_limiter
limiter = get_rate_limiter("gemini")
await limiter.acquire_async(timeout=30.0)
```

## Flux de Données

```
┌──────────────────┐     acquire()      ┌─────────────────┐
│  Swarm Executor  │ ─────────────────► │  APIRateLimiter │
│  (mode_executors)│                    │                 │
│                  │ ◄───────────────── │  Token Bucket   │
└──────────────────┘     token granted  └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  External API   │
                    │  (Gemini/Claude)│
                    └─────────────────┘
```

## Classes Principales

### `APIRateLimiter`
- **Token bucket algorithm** avec refill automatique
- **Dual-safe**: `asyncio.Lock` + `threading.Lock`
- **Statistics**: `get_stats()` retourne requests, waits, avg_wait_time

### `RateLimiterRegistry`
- **Singleton** - une instance par provider
- **Auto-configuration** via `DEFAULT_LIMITS`

### `RateLimitExceeded`
- Exception levée si timeout atteint sans token disponible

## Dépendances

**Importe**:
- Standard library uniquement (`asyncio`, `threading`, `time`, `collections`)

**Importé par**:
- `core/swarm/mode_executors.py:31` - Rate limiting en PARALLEL mode

## Configuration

| Provider | RPM | Burst | Source |
|----------|-----|-------|--------|
| `gemini` | 60 | 10 | DEFAULT_LIMITS |
| `claude` | 50 | 8 | DEFAULT_LIMITS |
| `default` | 30 | 5 | Fallback |

## Tests

- Pas de fichier de test dédié (TODO: `tests/test_rate_limiter.py`)

## Notes

- Ajouté en V8.4.5 pour résoudre les erreurs 429 en PARALLEL
- Token bucket sliding window de 60 secondes
- Compatible avec `ThreadPoolExecutor` (sync) et `asyncio` (async)
