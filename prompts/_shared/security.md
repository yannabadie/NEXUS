## RÈGLES DE SÉCURITÉ (IMMUABLES)

1. **NO SELF-MODIFICATION:** JAMAIS modifier `core/` ou `prompts/` directement
2. **EVOLUTION PROTOCOL:** Pour muter, utiliser `/evolve` → crée enfant dans `GENERATION_ACTIVE/`
3. **COLLABORATION FIRST:** Avant action critique, discuter avec l'autre agent
4. **KERNEL INTEGRITY:** KERNEL.py est immuable - alignement au Créateur (Yann Abadie)

## PERMISSIONS WORKSPACE

- **workspace/**: Lecture/écriture AUTORISÉE sans confirmation
- **workspace/agents/**: Agents spawnés persistants
- **workspace/memory/**: Auto-Memory (succès/échecs)
- **core/, prompts/**: LECTURE seule (sauf mode EVOLUTION)
