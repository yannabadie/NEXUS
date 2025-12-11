# Module: MCP (CORTEX) - Client & Server

**Version**: 9.0 (TRUE HIVE MIND)
**Last Updated**: 2025-12-11

## Rôle Architectural

Model Context Protocol (MCP) module bidirectionnel:
- **Client**: NEXUS consomme des outils depuis des serveurs MCP externes
- **Server V9.0**: NEXUS exposé comme serveur MCP pour Claude Desktop, VSCode, etc.

Implémentation zero-dependency (client) + FastMCP SDK (server).

**Phase ROADMAP**: 12.3 - CORTEX (MCP Client), V9.0 - MCP Server

## Alignement ROADMAP V7.6+ / V9.0

Ce module implémente:
- **Phase 12.3**: Infrastructure client MCP
- **V9.0**: NEXUS MCP Server (expose NEXUS comme outil externe)

Capacités:
- Intégration dynamique des outils MCP dans ToolManager (client)
- Support des serveurs MCP via stdio (transport standard)
- Exposition de NEXUS à Claude Desktop, VSCode, etc. (server)

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

### Fichier: `server.py` (V9.0 - NOUVEAU)
* **Fonction**: Expose NEXUS comme serveur MCP pour Claude Desktop/VSCode
* **Framework**: FastMCP SDK (`pip install mcp`)
* **Transport**: stdio (standard JSON-RPC 2.0)
* **Outils exposés**:
  - `nexus_read` - Lecture fichiers workspace
  - `nexus_glob` - Pattern matching fichiers
  - `nexus_grep` - Recherche regex dans code
  - `nexus_analyze` - Analyse tâche multi-agent (Gemini+Claude)
  - `nexus_status` - État système NEXUS
  - `nexus_bash` - Exécution shell sandboxée
* **Resources**:
  - `nexus://config` - Configuration NEXUS
  - `nexus://agents` - Liste des agents enregistrés

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

### Client (consommer des outils MCP externes)

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

### Server V9.0 (exposer NEXUS comme outil)

**Lancement standalone:**
```bash
python -m core.mcp.server
```

**Configuration Claude Desktop** (`claude_desktop_config.json`):
```json
{
    "mcpServers": {
        "nexus": {
            "command": "python",
            "args": ["-m", "core.mcp.server"],
            "cwd": "/path/to/nexus"
        }
    }
}
```

**Usage dans Claude Desktop:**
```
Utilisateur: Analyse le fichier auth.py avec NEXUS
Claude: <uses nexus_read tool to read auth.py>
Claude: <uses nexus_analyze tool for multi-agent analysis>
```

**Prérequis:**
```bash
pip install mcp  # FastMCP SDK
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
