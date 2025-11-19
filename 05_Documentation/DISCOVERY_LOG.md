# NEXUS - Journal des Découvertes
## Traçabilité Complète des Expérimentations
### Succès, Échecs, Limitations, Patterns

---

## Métadonnées

- **Créé** : 2025-11-18
- **Dernière mise à jour** : 2025-11-18 17:00
- **Total découvertes** : 5
- **Succès** : 2
- **Échecs** : 0
- **Partiels** : 3

---

## Légende

| Statut | Signification |
|--------|---------------|
| ✅ | Succès complet |
| ❌ | Échec |
| ⚠️ | Partiel / Workaround |
| 🔄 | À retester |

---

## Index par Type

### Capacités Validées
<!-- Liste auto-générée -->

### Limitations Découvertes
<!-- Liste auto-générée -->

### Patterns Efficaces
<!-- Liste auto-générée -->

### Bugs / Problèmes
<!-- Liste auto-générée -->

---

## Découvertes

<!-- Les entrées seront ajoutées ci-dessous par nexus-discovery-logger -->

---

## DIS-001 - Sub-agents ne peuvent pas spawner d'autres sub-agents

**Timestamp** : 2025-11-18 16:50
**Type** : Limitation
**Statut** : ✅ Confirmé

### Contexte
Vérifier si les sub-agents Claude peuvent créer d'autres sub-agents (nesting)

### Action
```
Task tool avec prompt demandant de lancer un autre Task
```

### Résultat
Le sub-agent n'a PAS accès au Task tool. Ses outils disponibles sont : Bash, Glob, Grep, Read, Edit, Write, NotebookEdit, WebFetch, TodoWrite, WebSearch, BashOutput, KillShell, AskUserQuestion, Skill, SlashCommand

### Découverte
**Limitation architecturale confirmée** : Les sub-agents ne peuvent pas spawner d'autres sub-agents. Seul l'agent principal a accès au Task tool.

### Impact
- **KB à mettre à jour** : CAPABILITIES_KB.md (déjà mentionné)
- **Architecture impactée** : Oui - orchestration multi-niveaux doit passer par Gemini ADK
- **Réutilisable** : Oui - contrainte de design

### Métriques
- Durée : 3s
- Tokens estimés : ~500
- Coût : 0

### Tags
`claude-task` `sub-agent` `limitation` `validated`

---

## DIS-002 - Pipeline Gemini→Claude→Gemini Fonctionnel

**Timestamp** : 2025-11-18 16:55
**Type** : Pattern
**Statut** : ✅ Succès

### Contexte
Tester un workflow complet où Gemini génère, Claude critique, Gemini présente

### Action
```bash
gemini --yolo "NEXUS PIPELINE TEST: Génère 3 noms variables → Claude critique → Montre résultat"
```

### Résultat
Pipeline complet en ~15s :
1. Gemini génère : `component_serial_number`, `last_scan_timestamp`, `assembly_line_id`
2. Claude critique avec notes : 9/10, 9/10, 8/10
3. Claude utilise contexte projet (ISA-95, MES Tanger) !

### Découverte
**Symbiose contextuelle** : Claude dans le callback a accès au contexte projet et l'utilise automatiquement. Il a suggéré `work_center_id` pour conformité ISA-95.

### Impact
- **KB à mettre à jour** : Non (pattern déjà documenté)
- **Architecture impactée** : Validée - pipeline séquentiel efficace
- **Réutilisable** : Oui - pattern de base pour toutes les architectures

### Métriques
- Durée : 15s
- Tokens estimés : ~1500
- Coût : 0

### Tags
`pipeline` `sequential` `callback` `validated` `context-aware`

---

## DIS-003 - Gemini sans --resume Rapide

**Timestamp** : 2025-11-18 16:54
**Type** : Capacité
**Statut** : ✅ Succès

### Contexte
Test après blocage de --resume

### Action
```bash
gemini "NEXUS TEST: Réponds uniquement '[OK]'"
```

### Résultat
Réponse instantanée (<2s)

### Découverte
Gemini one-shot très rapide. Le blocage précédent était lié à --resume ou à la session.

### Impact
- **Réutilisable** : Oui - pour tests rapides

### Métriques
- Durée : <2s
- Coût : 0

### Tags
`gemini` `performance` `validated`

---

## DIS-004 - Installation Extension Gemini Interactive

**Timestamp** : 2025-11-18 16:53
**Type** : Limitation
**Statut** : ⚠️ Partiel

### Contexte
Tentative d'installer l'extension GitHub pour Gemini

### Action
```bash
gemini extensions install https://github.com/github/github-mcp-server
```

### Résultat
Erreur 415 sur download, propose git clone mais nécessite confirmation interactive (Y/n)

### Découverte
L'installation d'extensions Gemini nécessite une interaction manuelle. Pas automatisable via subprocess.

### Impact
- **Architecture impactée** : Extensions doivent être pré-installées
- **Workaround** : Installation manuelle par l'utilisateur

### Métriques
- Durée : N/A
- Coût : 0

### Tags
`gemini` `extension` `limitation` `interactive`

---

## DIS-005 - Loop Pattern avec Workaround Fichier

**Timestamp** : 2025-11-18 17:00
**Type** : Pattern
**Statut** : ⚠️ Partiel

### Contexte
Test de pattern Génération→Critique→Amélioration (x2) avec itérations de raffinement

### Action
```bash
gemini --yolo avec 2 itérations de raffinement OEE
```

### Résultat
- **Itération 1** : Erreur bash (parenthèses dans code généré)
- **Itération 2** : Gemini utilise fichier comme workaround
- **Note finale** : 6/10 avec suggestions TypedDict

### Découverte
**Passage de code via CLI problématique** : Les parenthèses et caractères spéciaux dans le code généré causent des erreurs d'échappement bash. Le workaround efficace consiste à passer le code via un **fichier intermédiaire** plutôt que directement en CLI.

### Impact
- **Pattern validé** : Boucles itératives Gemini→Claude→Gemini fonctionnelles
- **Limitation découverte** : Code complexe ne doit pas passer directement en CLI
- **Workaround efficace** : Fichier temporaire pour éviter l'échappement
- **Réutilisable** : Oui - pattern applicable à tous les workflows de raffinement code

### Métriques
- Durée : 45s
- Tokens estimés : ~2000
- Coût : 0

### Tags
`loop` `iterative` `workaround` `limitation` `code-generation` `cli-escape`

---

