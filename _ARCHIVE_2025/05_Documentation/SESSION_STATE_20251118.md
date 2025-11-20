# NEXUS - État Session Claude 18/11/2025

## Pour Reprise Prochaine Session

### Découvertes (8)
1. **DIS-001**: Sub-agents n'ont PAS Task tool
2. **DIS-002**: Pipeline séquentiel + contexte projet ✅
3. **DIS-003**: Gemini one-shot rapide
4. **DIS-004**: Extensions interactives (limitation)
5. **DIS-005**: Loop pattern + workaround fichier
6. **DIS-006**: --resume NE GARANTIT PAS mémoire ❌ CRITIQUE
7. **DIS-007**: MCP add OK mais connexion échoue
8. **DIS-008**: Gemini 13+ outils natifs ✅

### Commandes Validées
```bash
gemini --resume latest -p "..."   # -p OBLIGATOIRE avec --resume
gemini --yolo -p "..."            # Shell pour callback
claude -p "..."                   # Non-interactif
```

### Documents Créés
- CAPABILITIES_KB.md, SELF_AWARENESS_KB.md
- ROADMAP_RESEARCH.md, META_ARCHITECTURE.md
- DISCOVERY_LOG.md, 06_Architecture_Library/

### À Faire
1. Tests Phase A (session chain)
2. Installer GitHub MCP manuellement
3. Tester Loader YAML
4. ArchitectureMatcher + embeddings

### Pattern Sauvegarde État
Pour éviter perte contexte:
1. Sauvegarder dans fichier (persistant)
2. Envoyer à Gemini avec --resume (session)
3. Reprendre avec: gemini --resume latest -p "Récupère état NEXUS"
