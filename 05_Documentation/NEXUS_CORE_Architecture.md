# NEXUS CORE - ARCHITECTURE MODULAIRE & ÉLÉGANTE
**Version :** 3.0 (Genesis)
**Philosophie :** "Use What You Have" (Comptes existants, Pas d'API Keys, CLI First)

## 1. Principes Fondamentaux
1.  **Zéro API Cost** : Utilisation exclusive des CLI (`gemini`, `claude`) authentifiées via vos comptes Pro/Ultra.
2.  **Modularité Totale** : Chaque composant (Router, Logger, Memory, Tool) est un module Python indépendant.
3.  **Transparence Absolue** : Chaque échange inter-IA est logué, affiché et archivé.
4.  **Intelligence Distribuée** :
    *   **Gemini 3.0 (Driver)** : Contexte 1M, Stratégie, "Chef de Projet".
    *   **Claude Opus (Sage)** : Décisions critiques, Architecture, Éthique.
    *   **Claude Sonnet (Worker)** : Code, Exécution, "Mains dans le cambouis".

## 2. Structure du Code (Python ADK-Style)

```
20_NEXUS/
├── core/
│   ├── __init__.py
│   ├── router.py        # Décide qui appeler (Opus vs Sonnet)
│   ├── bridge.py        # Wrapper pour les CLI (Gemini/Claude)
│   ├── logger.py        # Historisation & Affichage
│   └── memory.py        # Gestion du contexte (Fichiers/Graph)
│
├── agents/
│   ├── driver.py        # Logique Gemini (Cerveau principal)
│   ├── sage.py          # Logique Claude Opus (Consultant)
│   └── worker.py        # Logique Claude Sonnet (Exécutant)
│
├── workflows/           # Scénarios pré-câblés
│   ├── code_refactor.py
│   └── architecture_review.py
│
└── nexus.py             # Point d'entrée unique (CLI)
```

## 3. Le "BrainRouter" (L'Élégance du Choix)
Au lieu de coder en dur "Appelle Claude", on utilise une fonction de routing :
```python
def route_request(task_type, urgency, complexity):
    if complexity == "high" and task_type == "decision":
        return "claude-opus"  # Le Sage
    elif task_type == "coding" or task_type == "execution":
        return "claude-sonnet" # Le Worker
    else:
        return "gemini-driver" # Le Driver par défaut
```

## 4. Implémentation "CLI Wrapper" (Le Secret)
Pour utiliser vos comptes sans API Key, on wrap les processus système :
*   `Bridge` lance `subprocess.Popen(['claude', '-p', prompt, '--model', model])`.
*   Il capture `stdout` en temps réel pour le `Logger`.
*   Il gère les erreurs d'authentification ou de quota.

## 5. Historisation (La Boîte Noire)
Tout est enregistré dans `20_NEXUS/logs/session_YYYYMMDD.md` sous format lisible :
```markdown
[14:00:05] 🧠 GEMINI (Driver) -> 🧙‍♂️ CLAUDE (Opus)
"Analyse cette architecture critique..."

[14:00:15] 🧙‍♂️ CLAUDE (Opus) -> 🧠 GEMINI (Driver)
"Voici les risques identifiés..."
```
