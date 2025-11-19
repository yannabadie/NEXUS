# NEXUS - Base de Connaissances Techniques
## Capacités Claude Code & Gemini CLI
### Mise à jour : 18/11/2025

---

## 1. CLAUDE CODE

### Version & Identité
- **Version** : 2.0.44
- **Modèle** : Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **Contexte** : 200K tokens
- **Cutoff** : Janvier 2025

### Outils Natifs Disponibles
| Outil | Description | Usage NEXUS |
|-------|-------------|-------------|
| `Task` | Lancer des sub-agents spécialisés | Orchestration, logging |
| `Bash` | Exécuter commandes shell | Appeler Gemini CLI |
| `BashOutput` | Récupérer output background | Monitor processus longs |
| `Read/Write/Edit` | Manipulation fichiers | Context files, logs |
| `Glob/Grep` | Recherche fichiers/contenu | Exploration codebase |
| `WebSearch/WebFetch` | Recherche web | Mise à jour infos |
| `TodoWrite` | Gestion tâches | Tracking avancement |
| `AskUserQuestion` | Questions utilisateur | Clarifications |

### Sub-Agents (Task Tool)
**Configuration** : `.claude/agents/` (projet) ou `~/.claude/agents/` (global)

**Types disponibles** :
- `general-purpose` : Tâches complexes multi-étapes
- `Explore` : Exploration codebase rapide
- `Plan` : Planification et analyse

**Création custom** : Fichiers Markdown avec system prompt personnalisé

```yaml
# Exemple : .claude/agents/nexus-logger.md
name: nexus-logger
description: Log automatiquement tous les échanges NEXUS
tools: [Read, Write, Edit]
```

### MCP (Model Context Protocol)
**Rôle dual** : Client ET Server

**Client MCP** :
- Connexion à MCP servers externes
- Configuration dans `.mcp.json`
- Accès DB, GitHub, APIs via connecteurs

**Server MCP** :
- Mode : `claude mcp serve`
- Expose outils Claude aux autres clients
- Peut être appelé par Gemini via MCP

### Skills System
- Dossiers avec `SKILL.md` + scripts
- Activation automatique selon contexte
- Pas de slash command nécessaire

### Limitations
- Pas de mémoire entre sessions
- Context 200K (vs 1M Gemini)
- Pas de streaming audio/vidéo natif

---

## 2. GEMINI CLI

### Version & Identité
- **Version** : 0.15.4
- **Modèle par défaut** : gemini-2.5-pro
- **Contexte** : 1M tokens (1,000K)
- **Installation** : npm global

### Modes d'Exécution
| Mode | Commande | Description |
|------|----------|-------------|
| One-shot | `gemini "question"` | Réponse unique, pas de contexte |
| Interactif | `gemini` (REPL) | Session avec historique |
| Resume | `gemini --resume latest -p "..."` | Reprend session précédente (IMPORTANT: -p obligatoire) |
| YOLO | `gemini --yolo "..."` | Auto-approve tout (shell inclus) |

### Options Clés
```bash
--resume <id|latest>     # Reprendre session (CRUCIAL pour contexte)
--list-sessions          # Voir sessions disponibles
--yolo                   # Mode auto-approve tout
--approval-mode          # default | auto_edit | yolo
--model <name>           # Changer de modèle
--output-format          # text | json | stream-json
--allowed-tools          # Outils sans confirmation
--include-directories    # Dossiers additionnels workspace
```

### Sessions Persistantes
**30 sessions disponibles** pour ce projet

Sessions récentes NEXUS :
- Session 20 : Contexte projet (1h ago)
- Session 30 : Test KPIs (4 min ago)

**Stratégie** : Utiliser `--resume` pour maintenir le contexte entre appels

### Outils Intégrés
| Outil | Disponibilité | Description |
|-------|---------------|-------------|
| `search_file_content` | Par défaut | Recherche dans fichiers |
| `read_file` | Par défaut | Lecture fichiers |
| `edit_file` | Par défaut | Modification fichiers |
| `web_fetch` | Par défaut | Récupération web |
| `run_shell_command` | **--yolo seulement** | Exécution shell |
| `google_search` | Par défaut | Recherche Google |

### MCP Servers
**Configuration** : `settings.json` → `mcpServers`

**Types de connexion** :
- Stdio : Exécutable local (`command`)
- SSE : Server-Sent Events (`url`)
- HTTP : Streaming HTTP (`httpUrl`)

**Gestion** :
```bash
gemini mcp add <name> <command>
gemini mcp list
gemini mcp remove <name>
/mcp                    # Status dans REPL
```

### Extensions
**Statut actuel** : Aucune extension installée
**Potentiel** : Plugins pour fonctionnalités additionnelles

### GEMINI.md
Fichier lu automatiquement au démarrage dans le projet
→ Utiliser pour contexte persistant entre sessions

### Limitations
- Pas de sub-agents natifs (comme Claude Task)
- Session perdue si pas de --resume
- --yolo = risque sécurité

---

## 3. GOOGLE ADK (Agent Development Kit)

### Vue d'Ensemble
- **Version** : Python + Go (Nov 2025)
- **GitHub** : 14K stars
- **Statut** : Production (Agentspace, Google CES)

### Agents de Workflow
| Agent | Description | Use Case |
|-------|-------------|----------|
| `SequentialAgent` | Exécute agents en séquence | Pipeline traitement |
| `ParallelAgent` | Exécute agents en parallèle | Tâches indépendantes |
| `LoopAgent` | Boucle jusqu'à condition | Itération/retry |

### Intégration Multi-Modèle
- Gemini via Vertex AI
- Anthropic, Meta, Mistral via LiteLLM
- LangChain, LlamaIndex comme outils

### Capacités Avancées
- Streaming bidirectionnel audio/vidéo
- State management cross-agents
- Évaluation intégrée
- Debug visuel (Web UI)

### Installation
```bash
pip install google-adk
```

### Status NEXUS
**Non installé** - À considérer pour orchestration avancée

---

## 4. STRATÉGIE DE SYMBIOSE

### Architecture Recommandée

```
┌─────────────────────────────────────────────────────────┐
│              CLAUDE CODE (Orchestrateur)                │
│  • Interprète requête utilisateur                       │
│  • Décide délégation Claude vs Gemini                   │
│  • Maintient logs visibles                              │
│  • Synthétise résultats finaux                          │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
  ┌──────────▼────────┐    ┌──────────▼───────────────┐
  │ CLAUDE SUB-AGENTS │    │    GEMINI (--resume)     │
  │   (Task tool)     │    │                          │
  │                   │    │  Session persistante     │
  │ • Logger          │    │  Contexte 1M tokens      │
  │ • Validator       │    │  Shell via --yolo        │
  │ • Synthesizer     │    │                          │
  └───────────────────┘    └──────────────────────────┘
```

### Maintien du Contexte

**Claude** :
- Context via CLAUDE.md
- Sub-agents avec context propre
- Fichiers partagés

**Gemini** :
- `--resume latest` pour session persistante
- GEMINI.md lu automatiquement
- Fichiers contexte dans workspace

### Pattern de Communication

```bash
# 1. Claude prépare le contexte
# 2. Appel Gemini avec --resume pour continuer session
gemini --resume latest -p "NEXUS: [question]"

# 3. Si besoin shell, utiliser --yolo
gemini --resume latest --yolo -p "Exécute claude -p '...'"
```

### Logging Automatique

**Solution** : Sub-agent Claude dédié

```markdown
# .claude/agents/nexus-logger.md
Logs tous les échanges dans 20_NEXUS/05_Documentation/EXCHANGE_LOG.md
Format: [timestamp] [CLAUDE→GEMINI] ou [GEMINI→CLAUDE]
```

---

## 5. PATTERNS D'ÉCHANGE

### Pattern 1 : Claude Orchestre, Gemini Analyse
```
User → Claude: "Analyse le schéma CEGID"
Claude → Gemini: Envoie schéma (1M context)
Gemini → Claude: Retourne analyse
Claude → User: Synthèse formatée
```

### Pattern 2 : Gemini Rappelle Claude
```
User → Claude: "Génère et valide requête SQL"
Claude → Gemini: Génère requête
Gemini → Claude: claude -p "Valide: [SQL]"
Claude → Gemini: Validation
Gemini → Claude: Résultat final
Claude → User: Requête validée
```

### Pattern 3 : Multi-Agent Parallèle
```
User → Claude: "Analyse complète budget + planning"
Claude → [Gemini: Budget] + [Claude Task: Planning]
         ↓                    ↓
     Analyse budget     Analyse planning
         ↓                    ↓
Claude → User: Synthèse consolidée
```

---

## 6. COMMANDES DE RÉFÉRENCE

### Gemini CLI
```bash
# Session management
gemini --list-sessions
gemini --resume latest -p "question"   # -p OBLIGATOIRE avec --resume
gemini --resume 20 -p "question"

# Modes
gemini --yolo "commande shell"
gemini --approval-mode auto_edit "..."

# MCP
gemini mcp list
gemini mcp add <name> <command>
```

### Claude CLI
```bash
# Non-interactif
claude -p "question"
claude --print "question"

# MCP server mode
claude mcp serve
```

### Communication
```bash
# Claude → Gemini (avec session persistante)
gemini --resume latest -p "NEXUS: [message de Claude]"

# Gemini → Claude (nécessite --yolo)
gemini --yolo "Exécute: claude -p 'Message de Gemini'"
```

---

## 7. LIMITATIONS CONNUES

### Claude Code
- ❌ Contexte limité à 200K (vs 1M Gemini)
- ❌ Pas de streaming audio/vidéo
- ❌ Session non persistante nativement

### Gemini CLI
- ❌ Pas de sub-agents natifs
- ❌ Shell désactivé par défaut
- ❌ Contexte perdu sans --resume
- ❌ Mode -i incompatible subprocess

### Communication
- ❌ Latence ~5-30s par échange
- ❌ Timeout possible sur requêtes longues
- ❌ Pas de streaming en temps réel

---

## 8. MISES À JOUR À SURVEILLER

### Gemini CLI
- [ ] Intégration ADK native (Issue #8256)
- [ ] Extensions MCP additionnelles
- [ ] Mode conversation persistant

### Claude Code
- [ ] Support contexte étendu
- [ ] Intégration ADK
- [ ] Streaming amélioré

### ADK
- [ ] Support langages additionnels
- [ ] Intégration CLI simplifiée

---

## 9. FICHIERS DE CONFIGURATION

### Claude
- `.claude/agents/` - Sub-agents custom
- `.mcp.json` - MCP servers
- `CLAUDE.md` - Contexte projet

### Gemini
- `settings.json` → `mcpServers`
- `GEMINI.md` - Contexte projet (lu auto)

---

*Base de connaissances créée le 18/11/2025*
*Mise à jour après chaque découverte technique*
*Maintenue par : Claude Code + Gemini CLI*
