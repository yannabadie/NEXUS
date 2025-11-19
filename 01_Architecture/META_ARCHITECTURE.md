# NEXUS - Architecture de Méta-Agents Dynamiques
## Création, Stockage et Réutilisation d'Architectures
### Co-créé par Claude Code & Gemini CLI - 18/11/2025

---

## 1. VISION

NEXUS ne crée pas juste des réponses - il crée des **architectures d'agents** adaptées à chaque problème, les sauvegarde, et les réutilise intelligemment.

### Concept Clé

```
Problème → [Matcher] → Architecture existante?
                            ↓ Oui          ↓ Non
                     Charger & Exécuter    Créer nouvelle
                                           architecture
                                                ↓
                                           Sauvegarder
                                           pour réutilisation
```

---

## 2. CAPACITÉS TECHNOLOGIQUES RÉELLES

### 2.1 Claude Code - Capacités Dynamiques

| Capacité | Méthode | Usage |
|----------|---------|-------|
| **Agents CLI dynamiques** | `claude --agents '{JSON}'` | Création à la volée |
| **Agents fichiers** | `.claude/agents/*.md` | Persistance |
| **Agents résumables** | `agentId` + `resume` | Continuité |
| **MCP servers** | `.mcp.json` | Outils externes |
| **Skills** | `SKILL.md` + scripts | Activation auto |
| **Tools configurables** | Par agent | Contrôle accès |
| **Models configurables** | sonnet/opus/haiku | Performance vs coût |
| **Permission modes** | 5 modes | Sécurité |

**Limitation** : Sub-agents ne peuvent PAS spawner d'autres sub-agents

### 2.2 Claude Agent - Format YAML

```yaml
# .claude/agents/code-auditor.md
---
name: code-auditor
description: "Audite le code pour vulnérabilités OWASP. Use PROACTIVELY pour toute tâche de sécurité."
tools: Read, Grep, Bash
model: sonnet
permissionMode: acceptEdits
skills: security-patterns
---

Tu es un expert en sécurité applicative. Tu cherches:
- Injection SQL
- XSS
- Secrets hardcodés
- IDOR
- etc.

Format de sortie: JSON avec severity, location, description, fix
```

### 2.3 Gemini ADK - Capacités Dynamiques

| Capacité | Méthode | Usage |
|----------|---------|-------|
| **Agents Python** | Classes héritant `BaseAgent` | Logique custom |
| **SequentialAgent** | Pipeline séquentiel | Chaînage |
| **ParallelAgent** | Exécution parallèle | Performance |
| **LoopAgent** | Itération jusqu'à condition | Retry/Raffinement |
| **State management** | Dict partagé entre agents | Communication |
| **MCP servers** | `gemini mcp add` | Outils externes |
| **Extensions** | `gemini extensions` | Plugins |
| **Tools dynamiques** | `@tool` decorator | Création outils |

### 2.4 Gemini Agent - Format Python

```python
from gemini.adk.agents import BaseAgent, Agent
from gemini.adk.orchestration import SequentialAgent

class CodeAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="code-analyzer",
            model="gemini-2.5-pro",
            tools=[ReadFileTool, SearchCodeTool],
            instructions="Analyse le code pour patterns et dépendances."
        )

    async def run(self, state: dict) -> dict:
        # Logique custom
        files = state.get("files_to_analyze", [])
        analysis = await self.analyze_files(files)
        state["code_analysis"] = analysis
        return state
```

### 2.5 Tableau Comparatif

| Aspect | Claude | Gemini |
|--------|--------|--------|
| **Format définition** | YAML/Markdown | Python classes |
| **Orchestration** | Implicite (Task) | Explicite (Sequential/Parallel/Loop) |
| **State management** | Fichiers | Dict Python |
| **Sub-agents** | Oui (1 niveau) | Oui (multi-niveaux) |
| **Logique custom** | Limitée | Complète (Python) |
| **Persistance** | Fichiers .md | Code + State serialization |

---

## 3. ARCHITECTURE DE BIBLIOTHÈQUE

### 3.1 Structure de Dossiers

```
20_NEXUS/
├── 06_Architecture_Library/
│   ├── index.yaml                    # Index des architectures
│   ├── embeddings.db                 # Vecteurs pour matching
│   │
│   ├── audit/
│   │   ├── code_security_audit.yaml  # Architecture complète
│   │   ├── compliance_audit.yaml
│   │   └── performance_audit.yaml
│   │
│   ├── development/
│   │   ├── feature_implementation.yaml
│   │   ├── refactoring_legacy.yaml
│   │   └── api_design.yaml
│   │
│   ├── research/
│   │   ├── literature_review.yaml
│   │   └── competitive_analysis.yaml
│   │
│   ├── analysis/
│   │   ├── sql_schema_analysis.yaml
│   │   ├── log_root_cause.yaml
│   │   └── data_exploration.yaml
│   │
│   └── _templates/
│       ├── basic_sequential.yaml
│       ├── parallel_analysis.yaml
│       └── iterative_refinement.yaml
```

### 3.2 Format d'Architecture (YAML)

```yaml
# 06_Architecture_Library/audit/code_security_audit.yaml

metadata:
  name: "Code Security Audit"
  version: "1.0.0"
  description: "Architecture complète pour audit de sécurité de codebase. Utilise Gemini pour l'ingestion massive et Claude pour la synthèse."
  author: "NEXUS"
  created: "2025-11-18"
  tags: ["security", "audit", "owasp", "code-review"]
  estimated_time: "5-30min selon taille codebase"

requirements:
  min_context_tokens: 100000
  tools_required: ["Read", "Grep", "Bash"]
  models_required: ["gemini-2.5-pro", "claude-sonnet"]

orchestrator:
  type: "SequentialAgent"
  error_handling: "retry_then_escalate"
  max_retries: 3

agents:
  - id: "codebase_ingestion"
    type: "gemini_native"
    class: "CodebaseIngestorAgent"
    model: "gemini-2.5-pro"
    description: "Ingère tous les fichiers source dans le contexte"
    input_from_state: ["target_directory", "file_patterns"]
    output_to_state: ["code_files", "file_tree"]
    config:
      max_files: 1000
      extensions: [".py", ".js", ".ts", ".java", ".go"]
      ignore_patterns: ["node_modules", "__pycache__", ".git"]

  - id: "vulnerability_scan"
    type: "gemini_native"
    class: "VulnerabilityScannerAgent"
    model: "gemini-2.5-pro"
    description: "Analyse le code pour vulnérabilités OWASP"
    input_from_state: ["code_files"]
    output_to_state: ["vulnerabilities"]
    config:
      severity_levels: ["critical", "high", "medium", "low"]
      checks: ["sql_injection", "xss", "hardcoded_secrets", "idor", "ssrf"]

  - id: "claude_synthesis"
    type: "claude_proxy"
    agent_id: "security-report-writer"
    model: "sonnet"
    description: "Synthétise les résultats en rapport exécutif"
    input_from_state: ["vulnerabilities", "file_tree"]
    output_to_state: ["final_report"]
    prompt_template: |
      Tu es un expert en sécurité. Voici les vulnérabilités détectées:

      {{vulnerabilities}}

      Génère un rapport d'audit avec:
      1. Executive Summary (5 lignes max)
      2. Statistiques (Critical: X, High: Y, etc.)
      3. Top 5 vulnérabilités prioritaires
      4. Recommandations de remediation
      5. Plan d'action suggéré

      Format: Markdown professionnel

state_schema:
  target_directory: "string"
  file_patterns: "list[string]"
  code_files: "dict[string, string]"
  file_tree: "string"
  vulnerabilities: "list[dict]"
  final_report: "string"

success_criteria:
  - "vulnerabilities is not empty OR code_files is empty"
  - "final_report contains 'Executive Summary'"

example_usage:
  input:
    target_directory: "/path/to/project"
    file_patterns: ["**/*.py", "**/*.js"]
  expected_output:
    final_report: "# Security Audit Report\n\n## Executive Summary..."
```

### 3.3 Index des Architectures

```yaml
# 06_Architecture_Library/index.yaml

architectures:
  - path: "audit/code_security_audit.yaml"
    embedding_id: "emb_001"
    usage_count: 15
    avg_success_rate: 0.92
    last_used: "2025-11-18"

  - path: "analysis/sql_schema_analysis.yaml"
    embedding_id: "emb_002"
    usage_count: 8
    avg_success_rate: 0.95
    last_used: "2025-11-17"

  # ...

embedding_config:
  model: "gemini-embedding-001"
  dimensions: 768
  index_on: ["metadata.description", "metadata.tags"]
```

---

## 4. SYSTÈME DE MATCHING

### 4.1 Algorithme de Sélection

```python
class ArchitectureMatcher:
    def __init__(self, library_path: str):
        self.index = load_yaml(f"{library_path}/index.yaml")
        self.embeddings_db = ChromaDB(f"{library_path}/embeddings.db")

    def match(self, user_request: str, threshold: float = 0.75) -> Optional[str]:
        """
        Trouve l'architecture la plus adaptée à la requête.

        Returns:
            Path vers le fichier YAML ou None si aucune correspondance
        """
        # 1. Vectoriser la requête
        query_embedding = embed(user_request)

        # 2. Recherche sémantique
        results = self.embeddings_db.query(
            query_embedding,
            n_results=3
        )

        # 3. Vérifier le seuil
        if results[0].score < threshold:
            return None  # Créer nouvelle architecture

        # 4. Retourner la meilleure correspondance
        return results[0].metadata["path"]

    def suggest_modifications(self, arch_path: str, user_request: str) -> dict:
        """
        Suggère des ajustements à une architecture existante.
        """
        architecture = load_yaml(arch_path)
        # Utiliser LLM pour suggérer des modifications
        return suggest_with_llm(architecture, user_request)
```

### 4.2 Création Dynamique d'Architecture

```python
class ArchitectureGenerator:
    def create_from_request(self, user_request: str) -> str:
        """
        Crée une nouvelle architecture basée sur la requête.

        Returns:
            Path vers la nouvelle architecture créée
        """
        # 1. Analyser la requête
        analysis = analyze_request(user_request)

        # 2. Sélectionner le template approprié
        template = self.select_template(analysis.task_type)

        # 3. Générer l'architecture
        architecture = generate_architecture(
            template=template,
            requirements=analysis.requirements,
            agents_needed=analysis.agents
        )

        # 4. Sauvegarder
        path = self.save_architecture(architecture)

        # 5. Indexer pour future recherche
        self.index_architecture(path)

        return path
```

---

## 5. EXÉCUTION D'ARCHITECTURE

### 5.1 Loader Principal

```python
class ArchitectureLoader:
    def load(self, arch_path: str) -> BaseAgent:
        """
        Charge une architecture YAML et retourne un agent exécutable.
        """
        config = load_yaml(arch_path)

        # Instancier les agents
        agents = []
        for agent_config in config["agents"]:
            if agent_config["type"] == "gemini_native":
                agent = self.load_gemini_agent(agent_config)
            elif agent_config["type"] == "claude_proxy":
                agent = self.load_claude_proxy(agent_config)
            agents.append(agent)

        # Créer l'orchestrateur
        orchestrator_type = config["orchestrator"]["type"]
        if orchestrator_type == "SequentialAgent":
            return SequentialAgent(agents=agents)
        elif orchestrator_type == "ParallelAgent":
            return ParallelAgent(agents=agents)
        elif orchestrator_type == "LoopAgent":
            return LoopAgent(agent=agents[0], **config["orchestrator"])

    def load_claude_proxy(self, config: dict) -> BaseAgent:
        """
        Crée un agent qui appelle Claude via CLI.
        """
        return ClaudeProxyAgent(
            agent_id=config["agent_id"],
            model=config["model"],
            prompt_template=config["prompt_template"],
            input_keys=config["input_from_state"],
            output_key=config["output_to_state"][0]
        )
```

### 5.2 Claude Proxy Agent

```python
class ClaudeProxyAgent(BaseAgent):
    """
    Agent Gemini qui délègue à Claude via CLI.
    """
    def __init__(self, agent_id: str, model: str, prompt_template: str,
                 input_keys: list, output_key: str):
        self.agent_id = agent_id
        self.model = model
        self.prompt_template = prompt_template
        self.input_keys = input_keys
        self.output_key = output_key

    async def run(self, state: dict) -> dict:
        # 1. Préparer le prompt avec les données du state
        prompt = self.prompt_template
        for key in self.input_keys:
            value = state.get(key, "")
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # 2. Appeler Claude
        result = await self.call_claude(prompt)

        # 3. Mettre à jour le state
        state[self.output_key] = result
        return state

    async def call_claude(self, prompt: str) -> str:
        """
        Appelle Claude via CLI avec le bon agent.
        """
        import subprocess

        # Échapper le prompt pour le shell
        escaped_prompt = prompt.replace("'", "'\\''")

        # Construire la commande
        cmd = f"claude -p '{escaped_prompt}'"

        # Exécuter
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        return result.stdout
```

---

## 6. SYNERGIES CLAUDE + GEMINI

### 6.1 Qui Orchestre Qui ?

**Règle générale** : Gemini ADK orchestre, Claude exécute

| Situation | Orchestrateur | Raison |
|-----------|---------------|--------|
| Logique complexe | Gemini | Python complet |
| Multi-niveaux | Gemini | Sub-agents illimités |
| Parallélisation | Gemini | ParallelAgent natif |
| Task simple | Claude | Task tool direct |
| Interaction user | Claude | Meilleur alignement |

### 6.2 Patterns de Communication

**Pattern 1: Pipeline Gemini→Claude**
```
Gemini [Ingestion] → Gemini [Analysis] → Claude [Synthesis] → Output
```

**Pattern 2: Claude délègue à Gemini**
```
Claude [Reçoit requête] → Gemini [Traitement lourd] → Claude [Finalise]
```

**Pattern 3: Ping-Pong Itératif**
```
Gemini [Génère] ↔ Claude [Critique] ↔ Gemini [Améliore] → Claude [Valide]
```

**Pattern 4: Parallèle puis Fusion**
```
       ┌→ Gemini [Analyse A] ─┐
Input ─┤                      ├→ Claude [Fusionne] → Output
       └→ Gemini [Analyse B] ─┘
```

---

## 7. EXEMPLES D'ARCHITECTURES RÉUTILISABLES

### 7.1 Data Science Pipeline

```yaml
name: "EDA Pipeline"
orchestrator: SequentialAgent
agents:
  - gemini: DataLoaderAgent      # Charge CSV/JSON (1M context)
  - gemini: StatisticsAgent      # Calcule stats descriptives
  - gemini: VisualizationAgent   # Génère specs pour graphiques
  - claude: NotebookGenerator    # Crée notebook Jupyter complet
```

### 7.2 Literature Review

```yaml
name: "Research Synthesis"
orchestrator: SequentialAgent
agents:
  - gemini: PaperIngestorAgent   # Charge 20+ papers
  - gemini: KeyFindingsExtractor # Extrait méthodologies/résultats
  - gemini: GapAnalyzer          # Identifie lacunes
  - claude: StateOfArtWriter     # Rédige synthèse académique
```

### 7.3 Refactoring Legacy

```yaml
name: "Legacy Modernization"
orchestrator: SequentialAgent
agents:
  - gemini: CodebaseMapper       # Cartographie dépendances
  - gemini: PatternDetector      # Détecte anti-patterns
  - parallel:
      - gemini: TypeScriptMigrator
      - gemini: TestGenerator
  - claude: PRReviewer           # Review le code généré
  - loop:
      agent: TestRunner
      until: all_tests_pass
```

---

## 8. AMÉLIORATION CONTINUE

### 8.1 Feedback Loop

```python
class ArchitectureLearner:
    def record_execution(self, arch_path: str, result: ExecutionResult):
        """
        Enregistre le résultat d'une exécution pour apprentissage.
        """
        self.db.insert({
            "architecture": arch_path,
            "success": result.success,
            "duration": result.duration,
            "tokens_used": result.tokens,
            "user_satisfaction": result.feedback,
            "errors": result.errors,
            "timestamp": datetime.now()
        })

    def optimize_architecture(self, arch_path: str) -> str:
        """
        Propose des optimisations basées sur l'historique.
        """
        history = self.db.query(architecture=arch_path)

        # Identifier patterns d'échec
        common_errors = analyze_errors(history)

        # Suggérer modifications
        suggestions = suggest_improvements(common_errors)

        return suggestions
```

### 8.2 Versioning

```yaml
# architecture_v1.0.0.yaml → architecture_v1.1.0.yaml

changes:
  - version: "1.1.0"
    date: "2025-11-20"
    modifications:
      - "Ajout retry sur VulnerabilityScanner (échecs réseau)"
      - "Augmentation timeout Claude à 180s"
    performance_improvement: "+15% success rate"
```

---

## 9. PROCHAINES ÉTAPES

### Immédiat (Aujourd'hui)

1. [ ] Créer structure `06_Architecture_Library/`
2. [ ] Implémenter première architecture (Code Audit)
3. [ ] Tester le loader et l'exécution
4. [ ] Créer index.yaml initial

### Court terme (Cette semaine)

5. [ ] Implémenter ArchitectureMatcher avec embeddings
6. [ ] Créer 3-5 architectures de base
7. [ ] Tester le système de réutilisation
8. [ ] Documenter l'API

### Moyen terme (Décembre)

9. [ ] Implémenter feedback loop
10. [ ] Ajouter versioning automatique
11. [ ] Dashboard de monitoring
12. [ ] Optimisation automatique

---

## 10. QUESTIONS DE DESIGN OUVERTES

1. **Format state** : JSON vs MessagePack vs Pickle ?
2. **Persistance inter-session** : Fichiers vs Redis vs SQLite ?
3. **Sécurité** : Comment sandboxer les architectures custom ?
4. **Coût** : Comment estimer le coût avant exécution ?
5. **Timeout** : Global vs par agent ?

---

*Document créé le 18/11/2025*
*Par : Claude Code & Gemini CLI*
*Pour : NEXUS - Système d'Orchestration Multi-IA*
*Version : 1.0*
