# GEMINI CLI - RESEARCH COMPLET (Novembre 2025)

**Date:** 20 Novembre 2025
**Version CLI:** 0.17.0-nightly.20251116
**Modèle:** Gemini 3 Pro

---

## SYNTHÈSE CRITIQUE

### Problème Identifié dans NEXUS V5.0

**Erreur actuelle :** Le driver Gemini utilise une syntaxe CLI incorrecte, causant un JSON vide.

```python
# ❌ INCORRECT (driver actuel)
command = f'"{self.cli_path}" "{prompt}" > "{output_file.absolute()}"'
```

**Impact :** Les tests échouent avec `JSONDecodeError` car `action_out.json` reste vide.

**Solution :** Utiliser la syntaxe officielle avec flag `-p` et `--output-format json`.

---

## SYNTAXE OFFICIELLE GEMINI CLI

### Commande de Base

```bash
# Mode interactif
gemini

# Mode non-interactif avec prompt
gemini -p "Your prompt here"

# Avec modèle spécifique
gemini -m gemini-3-pro-preview-11-2025-thinking -p "Analyze this code"

# Avec sortie JSON
gemini -p "Your prompt" --output-format json

# Avec JSON streaming (JSONL)
gemini -p "Your prompt" --output-format stream-json
```

### Inclusion de Fichiers (@syntax)

```bash
# Lire un fichier et l'inclure dans le contexte
gemini @path/to/file.txt -p "Analyze this file"

# Lire un répertoire entier
gemini @src/ -p "Review the code"

# Espaces dans les chemins (nécessite escape)
gemini @My\ Documents/file.txt -p "Summarize"
```

### Formats de Sortie

| Format | Flag | Usage |
|--------|------|-------|
| **Texte standard** | (défaut) | Affichage terminal |
| **JSON** | `--output-format json` | Automation, parsing |
| **Stream JSON** | `--output-format stream-json` | Événements en temps réel (JSONL) |
| **Markdown export** | `/chat share file.md` | Export conversation |

---

## SPÉCIFICATIONS TECHNIQUES

### Version et Installation

**Version actuelle :** 0.17.0-nightly.20251116

**Canaux de release :**
- `@preview` : Publié chaque mardi avec dernières features
- `@latest` : Version stable recommandée

**Installation :**
```bash
# npm (global)
npm install -g @google/gemini-cli

# Homebrew (macOS/Linux)
brew install gemini-cli

# npx (sans installation)
npx @google/gemini-cli
```

**Prérequis :** Node.js 20+

### Modèles Disponibles

| Modèle | Fenêtre Contexte | Usage |
|--------|------------------|-------|
| **gemini-3-pro-preview-11-2025-thinking** | 1M tokens | Raisonnement avancé, planning stratégique |
| **gemini-2.5-pro** | 1M tokens | Équilibre performance/coût |
| **gemini-2.5-flash** | 1M tokens | Rapidité maximale |

**Spécification modèle :**
```bash
gemini -m gemini-3-pro-preview-11-2025-thinking -p "Prompt"
```

### Limites Free Tier (Google Account)

- **Requêtes/minute :** 60
- **Requêtes/jour :** 1 000

**Modes d'authentification :**
1. OAuth Google Account (free tier)
2. Gemini API Key (100 requests/day free)
3. Vertex AI (enterprise)

---

## COMMANDES INTERNES

### Slash Commands (`/`)

Contrôle méta du CLI lui-même.

| Commande | Description |
|----------|-------------|
| `/chat save <tag>` | Sauvegarde checkpoint conversation |
| `/chat share <file>` | Exporte en MD ou JSON |
| `/copy` | Copie dernière réponse vers clipboard |
| `/memory add <text>` | Ajoute contexte persistant |

**Checkpoints stockés dans :**
- Linux/macOS : `~/.gemini/tmp/<project_hash>/`
- Windows : `C:\Users\<User>\.gemini\tmp\<project_hash>\`

### At Commands (`@`)

Injection de contenu fichiers/répertoires.

```bash
# Fichier unique
gemini @workspace/context_in.md -p "Respond in JSON"

# Répertoire entier
gemini @core/ -p "Analyze architecture"
```

**Note :** Les fichiers `.gitignore` sont exclus par défaut.

### Shell Commands (`!`)

Exécution commandes système.

```bash
# Commande unique
!git status

# Mode shell persistant
!
```

**Variable d'environnement :** `GEMINI_CLI=1` activée automatiquement.

---

## GEMINI 3 PRO - CAPACITÉS

### Caractéristiques Clés (Novembre 2025)

**Modèle :** `gemini-3-pro-preview-11-2025-thinking`

**Features :**
- 1M tokens context window
- Thinking mode avec traces explicites de raisonnement
- Capacités agentiques de coding
- Génération de scaffolds complets de projets web
- Search grounding intégré

**Mise à jour :** Intégré dans Gemini CLI le 18 novembre 2025

### Utilisation Recommandée

**Pour NEXUS V5.0 - Rôle "Stratégie" :**
- Planning stratégique long-terme (1M context)
- Raisonnement complexe multi-étapes
- Analyse de plans avec historique complet

**Avantages vs Gemini 2.0 Flash :**
- Contexte 30x plus large (1M vs 32k)
- Raisonnement explicite (thinking mode)
- Meilleure cohérence sur longues sessions

---

## FONCTIONNALITÉS 2025

### Interactive Shell (Octobre 2025)

**Nouvelle capacité :** Exécution de commandes interactives complexes.

```bash
# Lancer vim directement dans Gemini CLI
!vim file.txt

# Monitoring système
!top

# Git rebase interactif
!git rebase -i HEAD~5
```

**Impact :** Gemini peut maintenant utiliser des outils interactifs sans blocage.

### Extensibilité MCP

**Model Context Protocol (MCP) :** Support pour intégrations customs.

**Use case :** Connecter Gemini CLI à des bases de données, APIs externes, outils internes.

---

## INTÉGRATION DANS NEXUS V5.0

### Driver Corrigé (Recommandé)

```python
def invoke(self, context: str) -> Dict[str, Any]:
    """
    Invoque Gemini via CLI avec syntaxe correcte.
    """
    # Écrire le contexte
    context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
    context_file.write_text(context, encoding="utf-8")

    # Fichier de sortie
    output_file = self.workspace_path / "_IO_BUFFER" / "action_out.json"

    # SYNTAXE CORRECTE :
    # Option 1 : Lire fichier avec @syntax
    command = (
        f'"{self.cli_path}" '
        f'@"{context_file.absolute()}" '
        f'-p "Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)." '
        f'--output-format json '
        f'> "{output_file.absolute()}"'
    )

    # Option 2 : Prompt direct avec modèle spécifié
    command_alt = (
        f'"{self.cli_path}" '
        f'-m gemini-3-pro-preview-11-2025-thinking '
        f'-p "Lis {context_file.absolute()}. Réponds en JSON." '
        f'--output-format json '
        f'> "{output_file.absolute()}"'
    )

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
        raise Exception(f"Gemini CLI error: {result.stderr}")

    # Lire la réponse JSON
    return self.read_response()
```

### Avantages de l'Approche @syntax

**Pourquoi utiliser `@file` plutôt que prompt direct :**

1. **Limite de taille :** Les arguments CLI ont une taille max (32k caractères sur Windows)
2. **Encodage :** `@syntax` gère automatiquement l'encodage UTF-8
3. **Contexte large :** Gemini 3 Pro peut ingérer tout le fichier (jusqu'à 1M tokens)
4. **Propreté :** Pas besoin d'échapper les caractères spéciaux dans le contexte

### Test de Validation

```bash
# Test 1 : Vérifier version CLI
gemini --version

# Test 2 : Vérifier JSON output
gemini -p "Return JSON: {\"status\": \"ok\"}" --output-format json

# Test 3 : Vérifier lecture fichier
echo "Test context" > test.md
gemini @test.md -p "Summarize in JSON" --output-format json

# Test 4 : Vérifier modèle Gemini 3 Pro
gemini -m gemini-3-pro-preview-11-2025-thinking -p "Hello" --output-format json
```

---

## COMPARAISON SYNTAXES

### ❌ Ancienne Syntaxe (Driver NEXUS Bugué)

```bash
gemini "Lis workspace/_IO_BUFFER/context_in.md. Réponds en JSON." > output.json
```

**Problèmes :**
- Pas de flag `-p` → CLI ne reconnaît pas comme prompt
- Pas de `--output-format json` → Sortie en texte markdown, pas JSON
- Prompt trop long → Peut être tronqué sur Windows
- Pas de spécification modèle → Utilise modèle par défaut (peut-être pas Gemini 3 Pro)

### ✅ Nouvelle Syntaxe (Correcte)

```bash
gemini @workspace/_IO_BUFFER/context_in.md \
  -p "Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)." \
  --output-format json \
  > workspace/_IO_BUFFER/action_out.json
```

**Avantages :**
- Flag `-p` explicite → Prompt bien reconnu
- `--output-format json` → JSON valide garanti
- `@syntax` → Lecture automatique du fichier contexte
- Sortie redirigée proprement → Pas de mélange stdout/stderr

---

## RECOMMANDATIONS POUR NEXUS

### Configuration Optimale

**Variables d'environnement (.env) :**
```env
# CLI paths
GEMINI_CLI_PATH=gemini

# Modèle stratégique (Updated Nov 2025)
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking

# Timeout (Gemini 3 Pro peut être plus lent que Flash)
CLI_TIMEOUT_SECONDS=180
```

### Monitoring & Debugging

**Logs à capturer :**
```python
# Dans le driver, logger :
self.logger.debug(f"Gemini CLI command: {command}")
self.logger.debug(f"Gemini CLI stdout: {result.stdout}")
self.logger.debug(f"Gemini CLI stderr: {result.stderr}")
self.logger.debug(f"Gemini CLI return code: {result.returncode}")
```

**Fichiers à vérifier en cas d'erreur :**
1. `context_in.md` → Vérifier que le contexte est bien écrit
2. `action_out.json` → Vérifier que le JSON est valide (pas vide)
3. stderr de la commande → Erreurs CLI (auth, rate limits, etc.)

### Gestion des Erreurs

**Erreurs communes :**

| Erreur | Cause | Solution |
|--------|-------|----------|
| **Empty JSON** | Pas de `--output-format json` | Ajouter le flag |
| **JSONDecodeError** | Sortie en markdown au lieu de JSON | Vérifier `--output-format` |
| **Authentication failed** | Pas de login Google | `gemini auth login` |
| **Rate limit exceeded** | >60 req/min ou >1000 req/jour | Attendre ou upgrade vers API key |
| **Timeout** | Contexte trop large ou modèle lent | Augmenter `CLI_TIMEOUT_SECONDS` |

---

## RESSOURCES OFFICIELLES

**Documentation :**
- GitHub : https://github.com/google-gemini/gemini-cli
- CLI Commands : https://google-gemini.github.io/gemini-cli/docs/cli/commands.html
- Google Developers : https://developers.google.com/gemini-code-assist/docs/gemini-cli
- Google Cloud Docs : https://docs.cloud.google.com/gemini/docs/codeassist/gemini-cli

**Tutoriels :**
- Google Codelabs : https://codelabs.developers.google.com/gemini-cli-hands-on
- DataCamp Guide : https://www.datacamp.com/tutorial/gemini-cli

**Blogs :**
- Gemini 3 Pro in CLI : https://developers.googleblog.com/5-things-to-try-with-gemini-3-pro-in-gemini-cli/
- Interactive Shell : https://developers.googleblog.com/en/say-hello-to-a-new-level-of-interactivity-in-gemini-cli/

---

## CHANGELOG NEXUS

**Date de mise à jour :** 20 Novembre 2025

**Changements appliqués :**
- [x] Recherche complète sur Gemini CLI
- [x] Identification du bug dans `gemini_driver.py`
- [ ] Correction du driver avec syntaxe `-p` et `--output-format json`
- [ ] Tests de validation avec syntaxe corrigée
- [ ] Mise à jour documentation interne

**Prochaines étapes :**
1. Appliquer la correction au driver
2. Tester manuellement la commande CLI
3. Re-exécuter les tests automatisés
4. Valider CFL avec Gemini 3 Pro fonctionnel

---

**Auteur :** Claude Sonnet 4.5
**Date :** 20 Novembre 2025
**Version NEXUS :** 5.0 Pragmatic Edition
**Status :** ✅ RECHERCHE COMPLÈTE - DRIVER PRÊT À CORRIGER
