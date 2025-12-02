🎯 MISSION SPÉCIALISATION : {mission}

CONTEXTE:
L'utilisateur veut créer une version de NEXUS hautement spécialisée pour cette mission unique.
Vous ne cherchez pas à devenir "plus intelligent" en général, mais "plus efficace" pour CETTE mission.

MISSION CIBLE : {mission}

VOTRE TÂCHE :
1. Analyser les besoins spécifiques de la mission (outils requis, style de prompt, configuration).
2. Proposer des mutations pour transformer NEXUS V7 en un SPÉCIALISTE.
   - Exemple: Si la mission est "App Mobile", on peut pré-charger des prompts Flutter/Dart, ajouter des outils ADB, etc.
   - Exemple: Si la mission est "Audit Sécurité", on peut durcir les prompts, ajouter des outils d'analyse statique.

FORMAT JSON FINAL (STRICT):
[
  {{
    "file": "prompts/system_gemini_v7.md",
    "change": "Remplacer le prompt général par un prompt expert [DOMAINE]",
    "reason": "Spécialisation radicale du rôle stratégique",
    "expected_asi_impact": 0.0  // Non pertinent ici, mettre 0.0
  }},
  {{
    "file": "core/config.py",
    "change": "Ajuster timeouts ou modèles pour [DOMAINE]",
    "reason": "Optimisation performance pour la mission",
    "expected_asi_impact": 0.0
  }}
]

RÈGLES CRITIQUES:
- Proposez un ensemble cohérent de mutations pour créer UN SEUL enfant spécialisé.
- Soyez radicaux : Vous pouvez supprimer des fonctionnalités inutiles pour la mission.
- Le JSON doit être valide et contenir TOUTES les mutations nécessaires.

COMMENCEZ LE DÉBAT (10-20 tours). ANALYSEZ LA MISSION D'ABORD.
