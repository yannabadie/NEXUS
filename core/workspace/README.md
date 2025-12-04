# Module: Workspace Management

## Rôle Architectural

Gestion multi-workspace pour NEXUS permettant de créer, archiver et basculer entre différents environnements de travail isolés.

**Phase ROADMAP**: 13b - Workspace Commands Activation

## Alignement ROADMAP V7.6+

Ce module active les commandes `/workspace` dans le REPL:
- `/workspace` - Affiche le workspace actuel
- `/workspace new [name]` - Crée un nouveau workspace
- `/workspace list` - Liste tous les workspaces
- `/workspace switch <name>` - Bascule vers un autre workspace

## Composants Clés

### Fichier: `manager.py`
* **Classe**: `WorkspaceManager`
* **Responsabilités**:
  - Gestion du cycle de vie des workspaces
  - Archivage et restauration
  - Recherche et suggestions
* **Méthodes principales**:
  - `get_current()` - Workspace actif
  - `list_workspaces()` - Tous les workspaces
  - `create_workspace(name)` - Création
  - `switch_workspace(name)` - Basculement
  - `archive_current()` - Archivage

### Fichier: `models.py`
* **Classes**: `WorkspaceInfo`, `WorkspaceMetrics`
* **Responsabilités**:
  - Métadonnées des workspaces
  - Statistiques d'utilisation
  - Sérialisation JSON

### Fichier: `exceptions.py`
* **Exceptions**:
  - `WorkspaceError` - Base
  - `WorkspaceNotFoundError` - Workspace introuvable
  - `WorkspaceExistsError` - Workspace déjà existant

## Structure des Répertoires

```
nexus_root/
├── workspace/                 # Workspace actif
│   ├── .nexus/
│   │   └── workspace.json     # Métadonnées
│   ├── logs/
│   └── memory/
└── workspace_archive/         # Archives
    ├── project-alpha/
    ├── project-beta/
    └── ...
```

## Usage

```python
from core.workspace import WorkspaceManager

manager = WorkspaceManager(nexus_root)

# Workspace actuel
current = manager.get_current()
print(f"Current: {current.name}")

# Lister tous
for ws in manager.list_workspaces():
    status = "ACTIF" if ws.is_current else ""
    print(f"{status} {ws.name} - {ws.get_relative_time()}")

# Créer nouveau (archive l'actuel)
new_ws = manager.create_workspace("my-project")

# Basculer
manager.switch_workspace("old-project")
```

## Tests

```bash
pytest tests/test_workspace_manager.py -v
```

33 tests couvrant:
- Création/archivage de workspaces
- Listing et recherche
- Gestion des erreurs
- Sérialisation des métadonnées

## Notes d'Audit

- **Isolation**: Chaque workspace a son propre blackboard et logs
- **Archivage**: Utilise `shutil.move` pour efficacité
- **Nettoyage**: Noms sanitisés pour le filesystem
- **Suggestions**: Utilise `difflib.get_close_matches` pour les typos
