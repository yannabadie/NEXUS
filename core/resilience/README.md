# Module: Resilience - System Health & Stability

**Version**: V9.6
**Module**: `core.resilience`

---

## Vue d'Ensemble

Le module `resilience` est le garant de la stabilité opérationnelle de NEXUS. Il fournit des mécanismes unifiés pour surveiller, isoler et protéger l'exécution du système.

### Composants Clés

1.  **SystemHealth** (`system_health.py`) : Moniteur centralisé de l'état des composants.
2.  **ContextScope** (`context_scope.py`) : Isolation des contextes d'exécution.
3.  **CircuitBreaker** : Protection contre les pannes en cascade (intégré via `SystemHealth`).

---

## 1. SystemHealth (Unified Monitor)

Le `SystemHealth` agrège les statuts de tous les sous-systèmes critiques (EventBus, SafeTaskManager, ToolRegistry, etc.).

### Usage

```python
from core.resilience import get_system_health

health = get_system_health()
report = await health.check_all()

if report.status == HealthStatus.UNHEALTHY:
    print(f"CRITICAL FAILURE: {report.message}")
    # Déclencher procédure de recovery
```

### Métriques Surveillées
- **Memory Usage** : Alerte si > 80%
- **Event Loop Lag** : Détection de blocages async
- **Component Liveness** : Vérification heartbeat des sous-systèmes

---

## 2. ContextScope (Isolation)

Le `ContextScope` empêche la "fuite" de données entre différentes exécutions (ex: entre deux tâches parallèles du Swarm).

### Principe
Chaque exécution majeure (Tâche, Phase HiveMind, Tool Call) se voit attribuer un Scope unique. Les modifications du blackboard ou des variables globales sont confinées à ce scope ou explicitement propagées.

---

## Intégration V9.6

En V9.6, `SystemHealth` est utilisé par :
- **OrchestratorV7** : Check avant chaque tour de boucle.
- **Tool Handlers** : Rapport de succès/échec pour mise à jour des métriques.
- **API** : Endpoint `/health` pour monitoring externe.
