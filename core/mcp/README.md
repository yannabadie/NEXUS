# Module: MCP (CORTEX)

## Rôle Architectural

Client Model Context Protocol (MCP) permettant à NEXUS d'interagir avec des outils externes via le standard MCP.
Implémentation zero-dependency utilisant JSON-RPC 2.0 sur stdio.

**Phase ROADMAP**: 12.3 - CORTEX (MCP Client)

## Alignement ROADMAP V7.6+

Ce module implémente la Phase 12.3 de la roadmap:
- Infrastructure client MCP
- Intégration dynamique des outils MCP dans ToolManager
- Support des serveurs MCP via stdio (transport standard)

## Composants Clés

### Fichier: `protocol.py`
* **Fonction**: Types JSON-RPC 2.0 pour le protocole MCP
* **Classes**:
  - `MCPRequest` / `MCPResponse` - Messages JSON-RPC 2.0
  - `MCPTool` / `MCPToolResult` - Définitions et résultats d'outils
  - `MCPCapabilities` - Capacités serveur
  - `MCPError` - Erreurs protocole
* **Zero-Dep**: Aucune dépendance externe, sérialisation JSON native

### Fichier: `client.py`
* **Fonction**: Client MCP gérant la communication subprocess
* **Classe principale**: `MCPClient`
* **Responsabilités**:
  - Gestion du cycle de vie (start, initialize, close)
  - Communication stdio avec le serveur
  - Thread de lecture asynchrone
  - Handshake protocolaire MCP
* **Timeout**: 30s par défaut, 10s pour l'initialisation

### Fichier: `registry.py`
* **Fonction**: Chargement de la configuration des serveurs MCP
* **Classe principale**: `MCPRegistry`
* **Configuration**: `workspace/.nexus/mcp_servers.json`
* **Fonctionnalités**:
  - Chargement paresseux des configs
  - Cache des clients connectés
  - Gestion automatique des reconnexions

## Format de Configuration

```json
{
  "servers": {
    "filesystem": {
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
      "args": ["/tmp"],
      "env": {"DEBUG": "true"},
      "enabled": true,
      "description": "File system access via MCP"
    }
  }
}
```

## Intégration ToolManager

Les outils MCP sont automatiquement enregistrés dans `ToolManager` avec le préfixe:
```
mcp_{server}_{tool}
```

Exemple: `mcp_filesystem_read_file`

## Dépendances et Interactions

```
┌─────────────────┐      ┌──────────────────┐
│  ToolManager    │─────▶│   MCPRegistry    │
└────────┬────────┘      └────────┬─────────┘
         │                        │
         │ execute()              │ get_client()
         ▼                        ▼
┌─────────────────┐      ┌──────────────────┐
│   MCPClient     │◀─────│  ServerConfig    │
└────────┬────────┘      └──────────────────┘
         │
         │ JSON-RPC 2.0 (stdio)
         ▼
┌─────────────────┐
│   MCP Server    │ (subprocess)
│   (external)    │
└─────────────────┘
```

## Usage

```python
from core.mcp import MCPClient, MCPRegistry

# Via Registry (recommandé)
registry = MCPRegistry(workspace_path)
client = registry.get_client("filesystem")
tools = client.list_tools()
result = client.call_tool("read_file", {"path": "/tmp/test.txt"})

# Directement
with MCPClient(command=["npx", "-y", "server-name"]) as client:
    tools = client.list_tools()
    result = client.call_tool("tool_name", {"arg": "value"})
```

## Tests

```bash
pytest tests/test_mcp_client.py -v
```

Tests incluent:
- Types protocole (serialization/deserialization)
- Cycle de vie client (start, initialize, close)
- Opérations sur les outils (list, call)
- Gestion des erreurs
- Intégration ToolManager

## Notes d'Audit

- **Thread Safety**: Reader thread pour les réponses asynchrones
- **Timeouts**: Configurables, défaut raisonnable (30s)
- **Error Handling**: Exceptions spécifiques (MCPClientError, MCPServerError)
- **Zero-Dep**: Pas de dépendance au SDK MCP officiel
