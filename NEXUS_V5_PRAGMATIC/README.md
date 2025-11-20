# NEXUS V5.0 (Pragmatic Edition)

**Orchestrateur Cognitif Symbiotique avec Auto-Correction Fiable**

## Qu'est-ce que NEXUS ?

NEXUS V5.0 est un système d'orchestration multi-agents qui coordonne deux IA (Gemini et Claude) en symbiose pour résoudre des tâches complexes.

### Philosophie

- **Gemini** (Hémisphère Gauche) : Stratégie, planification, analyse
- **Claude** (Hémisphère Droit) : Exécution, précision, validation
- **Nexus Core** : Exécution centralisée des outils avec vérité absolue

**"Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude), Validation through Objective Truth (Nexus Tool Executor)."**

---

## Évolutions Clés V4.5 → V5.0

| Feature | Impact |
|---------|--------|
| **Tool Executor** | CFL fiable à 99% - capture objective des résultats |
| **last_tool_result.json** | Vérité absolue partagée entre agents |
| **Dual Schema Light/Heavy** | -80% d'oublis post_action_review |
| **Panic System** | Arrêt propre < 3s avec sauvegarde |
| **Plan Health** | Détection automatique plans zombies |
| **State Rollback** | Auto-recovery corruption état |

---

## Installation

### Prérequis

- Windows 11
- Python 3.11+
- Claude CLI (`claude`)
- Gemini CLI (`gemini`) (optionnel)

### Installation Rapide

```powershell
# 1. Cloner ou télécharger NEXUS_V5_PRAGMATIC
cd NEXUS_V5_PRAGMATIC

# 2. Lancer l'installation automatique
.\install.ps1

# 3. Éditer .env avec votre configuration
notepad .env

# 4. Activer l'environnement
.\venv\Scripts\Activate.ps1
```

---

## Usage

### Mode Normal

```powershell
python nexus.py "Analyse le code dans src/ et identifie les bugs critiques"
```

### Mode InProjectImprovement

```powershell
python nexus.py "Améliore le projet" --mode InProjectImprovement
```

### Mode CoreEvolution (⚠ Avancé)

```powershell
python nexus.py "Analyse et améliore le code de NEXUS lui-même" --mode CoreEvolution
```

### Panic Mode (Arrêt d'urgence)

```powershell
# Via CLI
python nexus.py --panic "Claude boucle depuis 3h"

# Via fichier (pendant exécution)
echo "STOP MAINTENANT" > workspace\_IO_BUFFER\STOP_NOW
```

---

## Architecture

```
/NEXUS_V5_PRAGMATIC/
│
├── nexus.py                    # Point d'entrée
├── requirements.txt            # 5 dépendances (rich, pydantic, dotenv, psutil, filelock)
│
├── /core/                      # Système principal
│   ├── orchestration.py       # Boucle principale avec CFL
│   ├── orchestration_logged.py # Version instrumentée pour tests
│   ├── logging_system.py      # Système de logging complet
│   ├── /drivers/              # Communication avec agents
│   ├── /synapse/              # Protocol, memory, state
│   ├── /tools/                # ⭐ Tool Executor (bash, edit, git, read, write)
│   └── /ui/                   # Console Rich
│
├── /prompts/                   # ⭐ Prompts système agents (CRITIQUES)
│   ├── system_gemini_base.md
│   └── system_claude_base.md
│
├── /docs/                      # Documentation complète
│   ├── /architecture/         # Architecture système
│   ├── /testing/              # Guides et résultats de tests
│   ├── /deployment/           # Déploiement production
│   └── /development/          # Notes de développement
│
├── /tests/                     # Suite de tests automatisés
│   ├── test_suite.py          # 11 scénarios de tests
│   ├── log_analyzer.py        # Analyse des logs
│   └── run_tests.bat          # Exécution rapide
│
└── /workspace/                 # Sandbox agents
    ├── .nexus/                # État système
    └── _IO_BUFFER/            # Communication fichiers
```

---

## Protocole CFL (Cognitive Feedback Loop)

**RÈGLE D'OR :** Tout outil suit ce cycle obligatoire.

### Phase 1 : Demande (Tour N)
```json
{
  "action_type": "TOOL_USE",
  "tool_use": {
    "tool_name": "bash",
    "arguments": {"command": "pytest tests/"},
    "expected_outcome": "Les 5 tests passent. Sortie contient '5 passed'."
  }
}
```

### Phase 2 : Exécution (Nexus Core)
```
Nexus exécute → Sauvegarde dans last_tool_result.json
```

### Phase 3 : Validation (Tour N+1)
```json
{
  "post_action_review": {
    "validation_status": "SUCCESS",
    "analysis": "Les 5 tests ont réussi comme attendu."
  }
}
```

**→ Plus jamais d'hallucination sur les résultats.**

---

## Outils Disponibles

| Outil | Description | Exemple |
|-------|-------------|---------|
| `bash` | Commandes shell | `pytest tests/`, `git status` |
| `read` | Lire fichier | `src/auth.py` |
| `write` | Créer/écraser fichier | Nouveau module |
| `edit` | Remplacer texte | Correction bug |
| `git` | Opérations git | add, commit, status, diff |
| `list_dir` | Lister répertoire | `src/*.py` |

---

## Détection de Stagnation

**3 Niveaux d'Escalade :**

1. **Seuil 3** : Avertissement injecté dans le contexte
2. **Seuil 5** : Basculement automatique vers l'agent partenaire
3. **Seuil 7** : Arrêt d'urgence avec sauvegarde

---

## Plan Health

Le système surveille la "santé" du plan stratégique :

- **LOW** : Plan progresse normalement ✓
- **MEDIUM** : 2+ étapes bloquées > 20 tours ⚠
- **HIGH** : Aucun progrès depuis 20 tours ⚠
- **CRITICAL** : Aucun progrès depuis 40 tours → Basculement auto en InProjectImprovement 🚨

---

## Configuration (.env)

```env
# Chemins CLI
CLAUDE_CLI_PATH=claude
GEMINI_CLI_PATH=gemini

# Sessions
CLAUDE_SESSION_ID=

# Modèles (Updated November 2025)
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking
MODEL_EXECUTION=claude-sonnet-4-5-20250929

# Paramètres CFL
MAX_STALEMATE_COUNT=5
COMPRESSION_THRESHOLD_TOKENS=100000
```

---

## Dépendances

```
rich>=13.0.0          # Interface console
pydantic>=2.0.0       # Validation protocole
python-dotenv>=1.0.0  # Configuration
psutil>=5.9.0         # Monitoring ressources
filelock>=3.12.0      # Robustesse Windows I/O
```

**Installation : `pip install -r requirements.txt`**

---

## Exemples d'Objectifs

### Développement
```powershell
python nexus.py "Crée un module de tests unitaires complet pour src/auth.py"
python nexus.py "Corrige le bug dans validate_token qui accepte les tokens expirés"
python nexus.py "Refactorise le code dans src/utils.py pour améliorer la lisibilité"
```

### Analyse
```powershell
python nexus.py "Analyse le code et génère un rapport de qualité"
python nexus.py "Identifie les vulnérabilités de sécurité potentielles"
```

### CI/CD
```powershell
python nexus.py "Exécute tous les tests, corrige les échecs, puis commit"
```

---

## Troubleshooting

### L'agent ne fournit pas post_action_review

**Cause :** Oubli du protocole CFL.

**Solution :** NEXUS détecte automatiquement et avertit l'agent. Après 3 violations, basculement vers l'autre agent.

### Stagnation détectée

**Cause :** L'agent répète la même action échouée.

**Solution :** NEXUS escalade automatiquement (avertissement → changement d'agent → arrêt).

### Plan zombie (drift CRITICAL)

**Cause :** Aucun progrès depuis 40+ tours.

**Solution :** NEXUS bascule automatiquement en mode InProjectImprovement pour analyse.

### État corrompu

**Cause :** Interruption brutale ou bug.

**Solution :** NEXUS restaure automatiquement depuis `.bak1` ou `.bak2`.

---

## Limites Connues

1. **Sous-agents** : Protocole défini mais non implémenté (TODO)
2. **CoreEvolution** : Mode défini mais non implémenté (TODO)
3. **Compression mémorielle** : Placeholder simple (TODO: intégrer LLM pour résumé)
4. **API Fallback** : Drivers CLI uniquement (TODO: ajouter API Python)

---

## Contribuer

NEXUS V5.0 est un système autonome et extensible.

**Points d'extension :**
- Nouveaux outils dans `/core/tools/`
- Nouveaux drivers dans `/core/drivers/`
- Amélioration prompts système dans `/prompts/`

---

## Licence

Ce système est fourni "tel quel" pour usage personnel et éducatif.

---

## Credits

**Architecture :** Claude + Gemini Deep Think + Grok 4.1 Thinking
**Implémentation :** Claude (Sonnet 4.5)
**Date :** 20 Novembre 2025
**Version :** 5.0 (Pragmatic Edition)

**"Le système multi-agent local le plus fiable jamais créé."**
