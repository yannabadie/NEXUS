# NEXUS - Journal des Expériences
## Base de Connaissances des Tests et Découvertes

---

## Objectif

Ce document capture tous les résultats d'expériences pour :
- Ne pas répéter les erreurs
- Capitaliser sur les découvertes
- Guider les futures décisions

---

## Session 18/11/2025

### EXP-001 : Premier contact Claude → Gemini
**Date** : 18/11/2025 15:20
**Commande** : `gemini -p "Bonjour..."`

**Résultat** : ✅ SUCCÈS
- Gemini répond correctement
- Adopte le format demandé ([RÉPONSE GEMINI])
- Confirme version gemini-2.5-pro et contexte 1M tokens

**Apprentissage** :
- `-p` est déprécié mais fonctionne
- Utiliser le prompt positionnel : `gemini "question"`

---

### EXP-002 : Génération de schéma SQL
**Date** : 18/11/2025 15:22
**Commande** : `gemini "Propose-moi un schéma SQL minimal..."`

**Résultat** : ✅ SUCCÈS
- Schéma 5 tables bien structuré
- Noms français (cohérent CEGID)
- Indexes et commentaires inclus
- Contraintes CHECK appropriées

**Apprentissage** :
- Gemini génère du SQL PostgreSQL de qualité
- Comprend le contexte aéronautique (traçabilité)

---

### EXP-003 : Génération requête complexe
**Date** : 18/11/2025 15:25
**Commande** : `gemini "Génère une requête SQL complexe..."`

**Résultat** : ✅ SUCCÈS
- Utilise CTEs (WITH)
- Fenêtres analytiques (ROW_NUMBER)
- Jointures appropriées
- Commentaires explicatifs

**Apprentissage** :
- Gemini maîtrise les requêtes avancées
- Format bien structuré avec étapes numérotées

---

### EXP-004 : Mode interactif avec -i
**Date** : 18/11/2025 15:31
**Commande** : `gemini -i "contexte" --output-format text`

**Résultat** : ❌ ÉCHEC
- Erreur : "cannot be used when input is piped from stdin"

**Apprentissage** :
- Le mode `-i` (prompt-interactive) ne fonctionne pas via subprocess
- Nécessite un TTY réel
- Alternative : utiliser fichier de contexte ou `--resume`

---

### EXP-005 : Script bridge avec mémoire fichier
**Date** : 18/11/2025 15:32
**Script** : `nexus_conversation.py`

**Résultat** : ⚠️ PARTIEL
- Erreur initiale : `[WinError 2]` - gemini non trouvé
- Corrigé avec `shell=True` et `gemini.cmd`
- Fonctionne mais simule la mémoire (pas idéal)

**Apprentissage** :
- Sur Windows, utiliser `gemini.cmd` ou `shell=True`
- Simulation de mémoire via fichier = pas une vraie conversation
- L'utilisateur veut des échanges réels, pas simulés

---

### EXP-006 : Gemini demande outil shell
**Date** : 18/11/2025 15:35
**Commande** : `gemini "... utilise claude -p..."`

**Résultat** : ❌ ÉCHEC
- Erreur : "Tool run_shell_command not found"
- Gemini essaie d'utiliser un outil non disponible

**Apprentissage** :
- Gemini CLI par défaut n'a PAS accès au shell
- Outils disponibles limités : search_file_content, read_file, web_fetch
- Besoin d'activer le mode yolo ou configurer les extensions

---

### EXP-007 : Mode --yolo pour accès shell
**Date** : 18/11/2025 15:38
**Commande** : `gemini --yolo "Exécute claude --version"`

**Résultat** : ✅ SUCCÈS
- Gemini exécute bien `claude --version`
- Retourne "2.0.44 (Claude Code)"
- Lit ensuite des fichiers du projet (proactif)

**Apprentissage** :
- `--yolo` active l'accès shell (auto-approve all)
- Gemini peut réellement appeler Claude !
- Communication bidirectionnelle possible
- ⚠️ Mode yolo = potentiellement dangereux

---

### EXP-008 : Vérification Claude CLI
**Date** : 18/11/2025 15:37
**Commande** : `claude --version`

**Résultat** : ✅ SUCCÈS
- Version 2.0.44 (Claude Code)
- Claude CLI disponible en ligne de commande

**Apprentissage** :
- Claude peut être appelé via `claude -p "question"`
- Permet à Gemini de rappeler Claude
- Architecture bidirectionnelle confirmée possible

---

## Synthèse des Découvertes Clés

### Ce qui FONCTIONNE
1. `gemini "question"` - Mode one-shot basique
2. `gemini --yolo "..."` - Accès shell complet
3. `claude -p "question"` - Mode non-interactif Claude
4. Gemini génère du SQL PostgreSQL de qualité
5. Gemini comprend le contexte métier (CEGID, AS9100)

### Ce qui NE FONCTIONNE PAS
1. `gemini -i` via subprocess (besoin TTY)
2. Gemini shell par défaut (désactivé)
3. Simulation mémoire via fichier (pas souhaité par user)

### Configurations Requises
- **Gemini avec shell** : `gemini --yolo "..."`
- **Claude non-interactif** : `claude -p "..."`
- **Windows** : Utiliser `shell=True` dans subprocess

### Quotas Disponibles
- GoogleAI Ultra : quota élevé
- Claude Max 20x : 20x standard
- Pas besoin d'API keys additionnelles

---

## Session 18/11/2025 (Suite - Symbiose)

### EXP-010 : Session Persistante avec --resume
**Date** : 18/11/2025 16:XX
**Commande** : `gemini --resume latest -p "NEXUS: Test symbiose"`

**Résultat** : ✅ SUCCÈS CRITIQUE
- Gemini récupère le contexte de la session précédente
- Rappelle les 3 dernières interactions (KPIs)
- Confirme 1M tokens disponibles
- Utilise le format de réponse NEXUS

**Apprentissage** :
- **IMPORTANT** : Avec `--resume`, utiliser `-p` (pas positional)
- Le contexte est bien maintenu entre les appels
- Gemini lit automatiquement GEMINI.md

---

### EXP-011 : Callback Bidirectionnel Complet
**Date** : 18/11/2025 16:XX
**Commande** : `gemini --resume latest --yolo -p "NEXUS: Test callback..."`

**Résultat** : ✅ SUCCÈS COMPLET
- ÉTAPE 1 : Gemini génère JSON OF (10 champs)
- ÉTAPE 2 : Gemini appelle Claude (claude -p "NEXUS-CALLBACK:...")
- ÉTAPE 3 : Gemini intègre suggestions de Claude

**Améliorations Claude** :
1. Objet `traceability` (lots, certs matière, NADCAP)
2. Objet `quality` (FAI, plan inspection, NCR)

**Apprentissage** :
- La symbiose Claude ↔ Gemini est pleinement fonctionnelle
- `--resume` + `--yolo` + `-p` = configuration optimale
- Gemini peut orchestrer des callbacks complexes
- Le protocole "NEXUS:" et "NEXUS-CALLBACK:" fonctionne

---

## Synthèse Découvertes Clés (MAJ 18/11)

### Configuration Optimale NEXUS
```bash
# Session persistante avec shell access
gemini --resume latest --yolo -p "NEXUS: [requête]"
```

### Commande Obligatoire
- `-p` est **OBLIGATOIRE** avec `--resume` (pas le positional)
- `--yolo` nécessaire pour callback `claude -p`

### Symbiose Validée
- ✅ Contexte maintenu entre appels
- ✅ Callback bidirectionnel fonctionnel
- ✅ Intégration des suggestions croisées
- ✅ Format de réponse standardisé

---

## Prochaines Expériences à Mener

### EXP-012 : Intégration COMPASS KB
**Objectif** : Injecter contexte ChromaDB dans requête Gemini
**Test** : Charger 50K tokens de KB dans Gemini

### EXP-010 : Gemini --resume pour contexte persistant
**Objectif** : Tester la reprise de session Gemini
**Test** : `gemini --resume latest`

### EXP-011 : Google ADK installation
**Objectif** : Installer et tester ADK pour multi-agent
**Test** : `pip install google-adk`

### EXP-012 : Intégration COMPASS KB
**Objectif** : Injecter contexte ChromaDB dans requête Gemini
**Test** : Charger 50K tokens de KB dans Gemini

---

## Patterns à Réutiliser

### Pattern 1 : Appel Gemini avec contexte
```bash
gemini --yolo "CONTEXTE: ERP CEGID V11, AS9100
QUESTION: [question utilisateur]
FORMAT: Structuré avec sections"
```

### Pattern 2 : Gemini appelle Claude
```bash
gemini --yolo "Analyse ceci puis demande à Claude de valider avec:
claude -p 'Valide ce résultat: [résultat]'"
```

### Pattern 3 : Logging visible
```python
print(f"[CLAUDE → GEMINI] {datetime.now()}")
print(message)
# ... appel ...
print(f"[GEMINI → CLAUDE] {len(response)} chars")
print(response)
```

---

## Anti-Patterns à Éviter

1. ❌ Utiliser `-i` via subprocess
2. ❌ Simuler la mémoire avec fichiers (user refuse)
3. ❌ Oublier `--yolo` pour les commandes shell
4. ❌ Utiliser `-p` (déprécié)
5. ❌ Ignorer les quotas/timeouts

---

*Journal créé le 18/11/2025*
*Mis à jour après chaque expérience*
