# CLAUDE CODE - RESEARCH COMPLET (Novembre 2025)

**Date:** 20 Novembre 2025
**Version:** 2.0.47+
**Modèle:** Claude Sonnet 4.5 (default)

---

## SYNTHÈSE CRITIQUE

### État Actuel dans NEXUS V5.0

**Driver Claude actuel :** Semble déjà utiliser une syntaxe correcte, mais manque de documentation.

```python
# ✅ Syntaxe actuelle (à vérifier)
command = f'"{self.cli_path}" -p "{prompt_text}"'
```

**Points à valider :**
- Support du `--output-format json` pour automation
- Lecture de fichiers contextuels via `@syntax`
- Gestion des sessions pour continuité CFL

**Améliorations possibles :**
- Utiliser `@context_in.md` au lieu de prompt inline
- Ajouter `--output-format json` pour parsing structuré
- Configurer CLAUDE.md pour instructions persistantes NEXUS

---

## INSTALLATION

### Méthodes Officielles

**macOS/Linux :**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Homebrew (macOS) :**
```bash
brew install --cask claude-code
```

**Windows :**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**NPM :**
```bash
npm install -g @anthropic-ai/claude-code
```

**Prérequis :** Node.js 18+

### Vérification Installation

```bash
# Vérifier version
claude --version

# Test rapide
claude -p "Hello, respond with JSON: {\"status\": \"ok\"}" --output-format json
```

---

## SYNTAXE OFFICIELLE CLAUDE CODE CLI

### Modes d'Invocation

| Mode | Commande | Usage |
|------|----------|-------|
| **REPL interactif** | `claude` | Session conversationnelle |
| **Prompt initial** | `claude "query"` | Démarre REPL avec contexte |
| **Print mode (non-interactif)** | `claude -p "query"` | Exécute et quitte |
| **Piped input** | `cat file \| claude -p "query"` | Traite contenu depuis stdin |
| **Session continue** | `claude -c` ou `claude --continue` | Reprend session récente |
| **Session spécifique** | `claude -r "<session-id>"` | Reprend session par ID |

### Flags Critiques pour Automation

**Output Formatting (Mode Print `-p` requis) :**
```bash
# Texte standard (défaut)
claude -p "Analyze this code"

# JSON structuré
claude -p "Return error analysis" --output-format json

# Stream JSON (JSONL en temps réel)
claude -p "Run tests" --output-format stream-json

# Inclure messages partiels (streaming)
claude -p "Long task" --output-format stream-json --include-partial-messages
```

**Input/Output Control :**
```bash
# Format d'entrée
claude --input-format json -p "..."

# Validation schema JSON
claude -p "..." --output-format json --json-schema schema.json

# Mode verbose (debug)
claude -p "..." --verbose

# Limite de tours (pour agents)
claude -p "..." --max-turns 10
```

**Sélection de Modèle :**
```bash
# Par alias
claude --model sonnet -p "..."
claude --model opus -p "..."
claude --model haiku -p "..."

# Par ID complet
claude --model claude-sonnet-4-5-20250929 -p "..."
```

**Contrôle Permissions :**
```bash
# Skip permissions (CI/CD seulement, dangereux !)
claude -p "..." --dangerously-skip-permissions

# Déléguer permissions à MCP tool
claude -p "..." --permission-prompt-tool
```

---

## CONTEXT MANAGEMENT

### CLAUDE.md Files - Système Hiérarchique

**3 Niveaux de Contexte :**

1. **Global (~/.claude/CLAUDE.md) :**
   - Appliqué à tous les projets
   - Préférences personnelles
   - Standards généraux

2. **Project (./CLAUDE.md) :**
   - Racine du projet
   - Partagé avec l'équipe
   - Versionné dans git

3. **Directory (./subdir/CLAUDE.md) :**
   - Instructions spécifiques au répertoire
   - Surcharge les niveaux supérieurs

**Load Order :** Global → Project → Directory

### Structure Recommandée CLAUDE.md

```markdown
# NEXUS V5.0 - Project Context

## Architecture Overview
- Dual-agent orchestrator (Gemini Strategy + Claude Execution)
- Tool executor with CFL validation
- Workspace-based sandboxing

## Coding Standards
- Python 3.11+
- Type hints obligatoires
- Docstrings Google style
- Black formatting (auto via hook)

## File Organization
- /core/ : Système principal
- /prompts/ : Prompts système (CRITIQUES - NE PAS MODIFIER)
- /workspace/ : Sandbox agents
- /tests/ : Suite de tests automatisés
- /docs/ : Documentation complète

## Workflow
1. Lire context_in.md depuis _IO_BUFFER
2. Répondre en JSON Protocole Synapse V5.0
3. TOUJOURS fournir post_action_review après TOOL_USE
4. Utiliser last_tool_result.json comme vérité absolue

## Critical Rules
- NEVER hallucinate tool results
- ALWAYS validate tool execution via last_tool_result.json
- NEVER skip post_action_review (CFL violation)
- NEVER modify prompts/ directory (system prompts are immutable)
```

**Avantages :**
- Économie tokens (contexte pas répété dans chaque prompt)
- Cohérence multi-sessions
- Instructions persistantes immuables

### @ Syntax - File References

**Inclure fichiers dans le prompt :**

```bash
# Fichier unique
claude @./workspace/_IO_BUFFER/context_in.md -p "Respond in JSON"

# Répertoire récursif
claude @./core/ -p "Analyze architecture"

# Patterns glob
claude @./tests/**/*.py -p "Review test coverage"

# Multiple files
claude @file1.py @file2.py -p "Compare these files"
```

**Espaces dans chemins :**
```bash
# Avec échappement
claude @My\ Documents/file.md -p "..."

# Avec quotes
claude @"My Documents/file.md" -p "..."
```

**Exclusions :**
- Fichiers `.gitignore` exclus automatiquement
- Personnalisable via `.claude/settings.json`

### Piping & Stdin

```bash
# Lire depuis stdout d'une autre commande
cat workspace/_IO_BUFFER/context_in.md | claude -p "Respond in JSON" --output-format json

# Combiner avec @syntax
cat logs.txt | claude @./CLAUDE.md -p "Analyze these errors"
```

---

## CONFIGURATION (.claude/settings.json)

### Hiérarchie de Configuration

**3 Niveaux (ordre de priorité décroissant) :**

1. **Local (`.claude/settings.local.json`)** - Git ignored, config personnelle
2. **Project (`.claude/settings.json`)** - Versionné, config équipe
3. **User (`~/.claude/settings.json`)** - Global user

**Merge behavior :** Local > Project > User

### Configuration NEXUS Recommandée

**Project-level (`.claude/settings.json`) :**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "maxTokens": 8192,
  "maxTurns": 100,
  "permissions": {
    "allowedTools": [
      "Read(*)",
      "Write(workspace/**)",
      "Bash(git *)",
      "Bash(python *)",
      "Bash(pytest *)"
    ],
    "deny": [
      "Write(prompts/**)",
      "Write(.env)",
      "Write(core/config.py)",
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write(*.py)",
        "hooks": [
          {
            "type": "command",
            "command": "python -m black \"$file\""
          }
        ]
      }
    ]
  }
}
```

**Local-level (`.claude/settings.local.json`) :**
```json
{
  "verbose": true,
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(*.key)",
      "Read(*secret*)"
    ]
  }
}
```

---

## HOOKS POUR AUTOMATION

### Types de Hooks

| Event | Timing | Can Block |
|-------|--------|-----------|
| **SessionStart** | Début de session | Non |
| **UserPromptSubmit** | Après prompt user | Oui |
| **PreToolUse** | Avant exécution outil | Oui |
| **PostToolUse** | Après exécution outil | Non |

### Exemples d'Usage

**Auto-formatting :**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write(*.py)",
        "hooks": [
          { "type": "command", "command": "black \"$file\"" },
          { "type": "command", "command": "isort \"$file\"" }
        ]
      }
    ]
  }
}
```

**Pre-commit validation :**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit *)",
        "hooks": [
          { "type": "command", "command": "pytest tests/ -x" }
        ]
      }
    ]
  }
}
```

**Logging CFL violations :**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo \"Turn $(date)\" >> workspace/logs/cfl_turns.log"
          }
        ]
      }
    ]
  }
}
```

---

## SESSION MANAGEMENT

### Persistance Automatique

**Durée de vie :** 5 heures par défaut

**Stockage :**
- macOS/Linux : `~/.claude/sessions/`
- Windows : `C:\Users\<User>\.claude\sessions\`

**Contenu sauvegardé :**
- Historique complet messages
- État conversation
- Contexte accumulé

### Reprendre Sessions

```bash
# Session la plus récente
claude -c
claude --continue

# Picker interactif
claude --resume

# Session spécifique par ID
claude --resume <session-id>

# Avec nouveau prompt
claude --resume <session-id> "Continue with new task"
```

**Use case NEXUS :**
- Reprendre CFL après interruption
- Maintenir cohérence multi-tours
- Debugging avec historique complet

---

## OUTPUT FORMATS

### Format JSON (Automation)

**Basic JSON :**
```bash
claude -p "Analyze errors" --output-format json
```

**Output structure :**
```json
{
  "content": "...",
  "model": "claude-sonnet-4-5-20250929",
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567
  },
  "stop_reason": "end_turn"
}
```

**Stream JSON (JSONL) :**
```bash
claude -p "Long task" --output-format stream-json
```

**Output (newline-delimited JSON) :**
```jsonl
{"type":"message_start","message":{"id":"msg_123",...}}
{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}
{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}
{"type":"content_block_stop","index":0}
{"type":"message_stop"}
```

**Use case NEXUS :**
- Parser réponses dans driver Python
- Logging événements en temps réel
- Monitoring token usage

---

## SYSTEM PROMPT CUSTOMIZATION

### 3 Modes (Mutuellement Exclusifs)

**1. Replace (--system-prompt) :**
```bash
claude -p "..." --system-prompt "You are a Python expert. Follow PEP 8."
```
⚠️ **Danger :** Supprime TOUS les prompts par défaut de Claude Code (perd capacités outils).

**2. Replace via fichier (--system-prompt-file) :**
```bash
claude -p "..." --system-prompt-file ./prompts/custom_system.md
```
⚠️ **Même danger.**

**3. Append (--append-system-prompt) - RECOMMANDÉ :**
```bash
claude -p "..." --append-system-prompt "Additional instruction: Always provide post_action_review."
```
✅ **Sûr :** Préserve capacités outils + ajoute instructions customs.

### Usage dans NEXUS Driver

```python
def invoke(self, context: str) -> Dict[str, Any]:
    # Écrire contexte
    context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
    context_file.write_text(context, encoding="utf-8")

    # Charger prompt système custom (si utilisé)
    system_prompt_file = self.workspace_path.parent / "prompts" / "system_claude_base.md"

    # Option 1 : Via @syntax + append
    command = (
        f'"{self.cli_path}" '
        f'@"{context_file.absolute()}" '
        f'-p "Respond in JSON (Synapse V5.0 Protocol)" '
        f'--append-system-prompt "CRITICAL: Always provide post_action_review after TOOL_USE." '
        f'--output-format json '
        f'--max-turns 1 '
        f'> "{output_file.absolute()}"'
    )

    # Option 2 : Via system-prompt-file (remplace tout)
    command_alt = (
        f'"{self.cli_path}" '
        f'@"{context_file.absolute()}" '
        f'-p "Respond in JSON" '
        f'--system-prompt-file "{system_prompt_file.absolute()}" '
        f'--output-format json '
        f'> "{output_file.absolute()}"'
    )

    # Exécuter...
```

**Recommandation :** Utiliser `--append-system-prompt` pour injecter règles CFL sans casser outils.

---

## MODÈLES DISPONIBLES (Novembre 2025)

### Sonnet 4.5 (Default - Recommandé NEXUS)

**ID :** `claude-sonnet-4-5-20250929`
**Alias :** `sonnet`

**Caractéristiques :**
- Meilleur modèle de coding au monde (SWE-bench Verified leader)
- Opération autonome : 30 heures (vs 7h pour Opus 4)
- Computer use : 61.4% OSWorld (vs 42.2% Sonnet 4)
- Alignement renforcé (moins de sycophancy, deception, power-seeking)

**Pricing :**
- Input : $3/million tokens
- Output : $15/million tokens

**Use case NEXUS :** Exécution précise, CFL compliance, coding fiable

### Opus 4.1

**Alias :** `opus`

**Caractéristiques :**
- Raisonnement le plus avancé
- Plus lent et coûteux que Sonnet 4.5

**Use case NEXUS :** Escalation (si Sonnet échoue)

### Haiku 3.5

**Alias :** `haiku`

**Caractéristiques :**
- Rapidité maximale
- Moins cher
- Moins capable

**Use case NEXUS :** Résumés, compressions, tâches simples

### Spécification Modèle

```bash
# Par alias
claude --model sonnet -p "..."

# Par ID complet (recommandé pour repro)
claude --model claude-sonnet-4-5-20250929 -p "..."

# Dans .claude/settings.json
{
  "model": "claude-sonnet-4-5-20250929"
}
```

---

## SUBAGENTS (Agents Délégués)

### Concept

**Définition :** Subagents = agents spécialisés délégués pour sous-tâches.

**Avantages :**
- Parallélisation tâches
- Spécialisation contexte
- Isolation erreurs

### Définition via CLI

```bash
claude -p "..." --agents '{
  "test-runner": {
    "systemPrompt": "You are a test specialist. Run tests and analyze failures.",
    "maxTurns": 5
  },
  "code-reviewer": {
    "systemPrompt": "You are a code reviewer. Check for bugs and style issues.",
    "maxTurns": 3
  }
}'
```

**Invocation depuis prompt :**
```
User: "Review the code and run tests"
Claude: [Délègue à code-reviewer et test-runner]
```

### Cas d'Usage NEXUS

**Potentiel (non implémenté dans V5.0) :**
- Subagent "CFL Validator" : Vérifie post_action_review compliance
- Subagent "Plan Analyzer" : Analyse drift du plan stratégique
- Subagent "Error Recovery" : Gère erreurs sans interrompre flux principal

---

## INTÉGRATION DANS NEXUS V5.0

### Driver Optimisé (Recommandé)

```python
class ClaudeDriver(BaseDriver):
    """Driver pour Claude Code CLI."""

    def __init__(self, config: Config, workspace_path: Path):
        super().__init__(workspace_path, config.cli_timeout_seconds)
        self.cli_path = config.claude_cli_path
        self.model = config.model_execution
        self.session_id = config.claude_session_id or None

    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoque Claude via CLI avec syntaxe optimale.
        """
        # Écrire le contexte
        context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
        context_file.write_text(context, encoding="utf-8")

        # Fichier de sortie
        output_file = self.workspace_path / "_IO_BUFFER" / "action_out.json"

        # Construire la commande
        command_parts = [
            f'"{self.cli_path}"',
            f'@"{context_file.absolute()}"',  # Lire contexte via @syntax
            '-p "Respond STRICTLY in JSON (Synapse V5.0 Protocol)."',
            f'--model {self.model}',
            '--output-format json',
            '--max-turns 1',  # Non-interactif, 1 tour seulement
            '--append-system-prompt "CRITICAL: After TOOL_USE, always provide post_action_review. Use last_tool_result.json as truth."',
        ]

        # Si session existe, la reprendre
        if self.session_id:
            command_parts.insert(1, f'--resume {self.session_id}')

        # Redirection output
        command_parts.append(f'> "{output_file.absolute()}"')

        command = ' '.join(command_parts)

        # Exécuter
        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode != 0:
                raise Exception(f"Claude CLI error: {result.stderr}")

            # Attendre (Windows I/O lag)
            time.sleep(0.5)

            # Lire la réponse JSON
            return self.read_response()

        except subprocess.TimeoutExpired:
            raise Exception(f"Claude CLI timeout après {self.timeout}s")
```

### Configuration .env

```env
# CLI Path
CLAUDE_CLI_PATH=claude

# Session (optionnel, pour continuité)
CLAUDE_SESSION_ID=

# Modèle
MODEL_EXECUTION=claude-sonnet-4-5-20250929

# Timeout (Claude peut être lent sur tâches complexes)
CLI_TIMEOUT_SECONDS=120
```

### CLAUDE.md pour NEXUS

**Location :** `NEXUS_V5_PRAGMATIC/CLAUDE.md`

**Contenu (voir template complet dans "Context Management") :**
- Architecture overview
- CFL protocol (CRITICAL)
- File organization
- Tool execution rules
- Forbidden actions

---

## BEST PRACTICES

### 1. Review Before Accept

**Toujours :** Vérifier changements avant acceptation.

**Dans NEXUS :** Orchestrateur vérifie via CFL `post_action_review`.

### 2. Granular Permissions

**Faire :**
```json
{
  "permissions": {
    "allowedTools": ["Bash(git status)", "Bash(pytest *)"],
    "deny": ["Bash(rm *)", "Bash(sudo *)"]
  }
}
```

**Ne pas faire :**
```json
{
  "permissions": {
    "allowedTools": ["Bash(*)"]  // Trop large !
  }
}
```

### 3. Hooks for Consistency

**Auto-format post-write :**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write(*.py)",
        "hooks": [{ "type": "command", "command": "black \"$file\"" }]
      }
    ]
  }
}
```

### 4. Task Separation

**Principe :** 1 session = 1 tâche logique.

**Pourquoi :** Évite pollution contexte, optimise tokens.

**Dans NEXUS :** Chaque objectif user = nouvelle session orchestrateur.

### 5. Avoid Skip-Permissions

**Danger :** `--dangerously-skip-permissions` peut causer dommages irréversibles.

**Acceptable :** CI/CD avec environnement sandboxé + rollback automatique.

**Dans NEXUS :** Jamais utiliser (orchestrateur gère permissions via tool executor).

---

## TROUBLESHOOTING

### Erreurs Communes

| Erreur | Cause | Solution |
|--------|-------|----------|
| **Command not found: claude** | CLI pas installé ou pas dans PATH | Vérifier installation, ajouter au PATH |
| **Authentication failed** | Pas de login Anthropic | `claude auth login` |
| **JSONDecodeError** | Pas de `--output-format json` | Ajouter le flag |
| **Empty output** | Redirection stdout ratée | Vérifier syntaxe redirection Windows |
| **Timeout** | Tâche trop complexe | Augmenter `CLI_TIMEOUT_SECONDS` |
| **Permission denied** | Tool bloqué par settings | Vérifier `.claude/settings.json` permissions |
| **Session not found** | Session expirée (>5h) | Démarrer nouvelle session |

### Debugging

**Mode verbose :**
```bash
claude -p "..." --verbose
```

**Logs détaillés :**
- Session logs : `~/.claude/sessions/<session-id>/`
- Error logs : stderr de la commande

**Test validation :**
```bash
# Test 1 : Version CLI
claude --version

# Test 2 : JSON output
claude -p "Return {\"status\": \"ok\"}" --output-format json

# Test 3 : File reading
echo "Test" > test.md
claude @test.md -p "Summarize" --output-format json

# Test 4 : Model specification
claude --model claude-sonnet-4-5-20250929 -p "Hello" --output-format json
```

---

## RESSOURCES OFFICIELLES

**Documentation :**
- CLI Reference : https://code.claude.com/docs/en/cli-reference
- Anthropic Docs : https://docs.anthropic.com/en/docs/claude-code/cli-usage
- Best Practices : https://www.anthropic.com/engineering/claude-code-best-practices

**GitHub :**
- Repo : https://github.com/anthropics/claude-code
- Issues : https://github.com/anthropics/claude-code/issues
- Awesome Claude Code : https://github.com/hesreallyhim/awesome-claude-code

**Community :**
- Discord : https://anthropic.com/discord
- Blog posts : https://www.anthropic.com/engineering

**Cheatsheets :**
- Shipyard : https://shipyard.build/blog/claude-code-cheat-sheet/
- DevToolHub : https://devtoolhub.com/claude-code-setup-guide/

---

## COMPARAISON AVEC GEMINI CLI

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| **Installation** | curl/brew/npm | npm/homebrew |
| **Modèle par défaut** | Sonnet 4.5 | Gemini 2.5 Pro |
| **Context window** | 200k tokens | 1M tokens (Gemini 3 Pro) |
| **File reading** | `@syntax` | `@syntax` |
| **JSON output** | `--output-format json` | `--output-format json` |
| **Session management** | 5h auto-save | Checkpoints manuels |
| **Hooks** | Oui (4 types) | Non |
| **CLAUDE.md / GEMINI.md** | Oui (hiérarchique) | Oui (GEMINI.md) |
| **Permissions granulaires** | Oui (JSON config) | Non |
| **Subagents** | Oui (via --agents) | Non |
| **Streaming** | stream-json (JSONL) | stream-json (JSONL) |

**Recommandation NEXUS :**
- **Gemini :** Stratégie (1M context, thinking mode)
- **Claude :** Exécution (meilleur coding, CFL compliance)

---

## CHANGELOG NEXUS

**Date de mise à jour :** 20 Novembre 2025

**Changements appliqués :**
- [x] Recherche complète sur Claude Code CLI
- [x] Documentation syntaxe optimale
- [ ] Vérification driver actuel Claude
- [ ] Application améliorations (--output-format json, @syntax)
- [ ] Création CLAUDE.md pour instructions persistantes
- [ ] Configuration .claude/settings.json avec permissions

**Prochaines étapes :**
1. Vérifier syntaxe actuelle driver Claude
2. Appliquer optimisations si nécessaire
3. Créer CLAUDE.md à la racine NEXUS
4. Configurer .claude/settings.json avec hooks
5. Tester intégration complète

---

**Auteur :** Claude Sonnet 4.5
**Date :** 20 Novembre 2025
**Version NEXUS :** 5.0 Pragmatic Edition
**Status :** ✅ RECHERCHE COMPLÈTE - PRÊT POUR OPTIMISATION
