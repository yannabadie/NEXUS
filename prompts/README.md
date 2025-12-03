# Prompts - NEXUS V7.5 HIVE MIND

## Structure

```
prompts/
├── _shared/                    # Sections réutilisables
│   ├── vision.md              # Vision HIVE MIND
│   ├── collaboration.md       # Philosophie égalitaire
│   ├── security.md            # Règles KERNEL
│   ├── auto_memory.md         # Système Auto-Memory
│   └── tools.md               # Liste des 11 outils
├── system_gemini_v7.md        # Prompt Gemini (JSON strict)
├── system_claude_v7.md        # Prompt Claude (hybride XML)
├── evolution_brainstorm.md    # Mode /evolve
├── specialization_mission.md  # Mode /specialize
└── README.md                  # Ce fichier
```

## Optimisation V7.5

| Prompt | Avant | Après | Réduction |
|--------|-------|-------|-----------|
| system_gemini_v7.md | 620 lignes | 169 lignes | -73% |
| system_claude_v7.md | 609 lignes | 163 lignes | -73% |
| evolution_brainstorm.md | 141 lignes | 89 lignes | -37% |
| specialization_mission.md | 37 lignes | 59 lignes | +59% (enrichi) |

**Économie tokens estimée:** ~50% par session

## Includes

Les prompts utilisent des directives `<!-- #include _shared/file.md -->`.
Le loader `prompt_loader.py` résout ces includes au chargement.

## Utilisation

```python
from core.prompts import load_prompt

gemini_prompt = load_prompt("system_gemini_v7")
claude_prompt = load_prompt("system_claude_v7")
evolution_prompt = load_prompt("evolution_brainstorm", {
    "child_count": 3,
    "parent_id": "NEXUS_V7",
    "lineage_context": "..."
})
```

## Philosophie

1. **Collaboration égalitaire** - Gemini et Claude sont égaux
2. **Auto-Memory** - NEXUS apprend de ses succès/échecs
3. **Coexistence** - Les enfants coexistent avec le parent
4. **Sécurité** - KERNEL.py immuable
