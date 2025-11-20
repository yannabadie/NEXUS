# ROADMAP NEXUS
## Orchestration Multi-IA Claude + Gemini
### Phase Expérimentale - Novembre 2025

---

## Vision du Projet

Créer un système d'orchestration bidirectionnelle entre Claude Code et Gemini CLI permettant :
- Communication visible et transparente entre les deux IAs
- Échanges réels (pas de simulation de mémoire)
- Capacité de sub-agents imbriqués (récursivité)
- Analyse massive de données SQL ERP (CEGID V11)
- Intégration avec les technologies ACE+COMPASS existantes

---

## Exigences Utilisateur

1. **Communication visible** : L'utilisateur doit voir tous les échanges Claude ↔ Gemini
2. **Pas de simulation** : Vrais échanges, pas de mémoire artificielle via fichier
3. **Bidirectionnalité** : Claude peut appeler Gemini ET Gemini peut appeler Claude
4. **Sub-agents** : Les deux peuvent spawner des sous-processus
5. **Intégration ACE+COMPASS** : Réutiliser KB, agents, playbooks existants
6. **Objectif final** : Analyse SQL ERP pour questions métier complexes

---

## Modes d'Interaction Envisagés

### Mode A : Pipeline Séquentiel
```
User → Claude → Gemini → Claude → User
```
- Claude orchestre, Gemini analyse
- Simple mais pas bidirectionnel

### Mode B : Ping-Pong Bidirectionnel
```
User → Claude ←→ Gemini → Claude → User
           ↑______↓
```
- Gemini peut rappeler Claude via `claude -p`
- Claude peut relancer Gemini via `gemini`
- Vraie collaboration

### Mode C : Multi-Agent Distribué (ADK)
```
           ┌─ Claude Agent 1
User → Orchestrateur ─┼─ Claude Agent 2
     (Claude ou Gemini)├─ Gemini Agent 1
                      └─ Gemini Agent 2
```
- Utilise Google ADK pour orchestration
- Agents spécialisés des deux côtés
- Plus complexe mais plus puissant

### Mode D : COMPASS + NEXUS Hybride
```
User → Claude → [COMPASS KB Search] → Gemini [1M context analysis] → Claude → User
                      ↓
              7 Agents COMPASS
```
- COMPASS fournit le contexte via ChromaDB
- NEXUS ajoute l'analyse massive via Gemini
- Meilleur des deux mondes

---

## Roadmap Détaillée

### Phase 0 : Setup (COMPLÉTÉE)
- [x] Créer structure 20_NEXUS
- [x] CLAUDE.md et GEMINI.md
- [x] Vérifier Gemini CLI (v0.15.4)
- [x] Vérifier Claude CLI (v2.0.44)
- [x] POC communication basique

### Phase 1 : Communication Bidirectionnelle (COMPLÉTÉE)
**Objectif** : Claude et Gemini peuvent s'appeler mutuellement
- [x] Configuration Gemini (Shell access)
- [x] Création GEMINI.md (Manuel Driver)
- [x] Validation POC Symbiose

### Phase 2 : Inversion de Contrôle - Driver Mode (ACTIVE)
**Objectif** : Gemini 3.0 pilote Claude pour l'exécution
- [x] Définition des rôles (Driver/Worker)
- [x] Mise à jour des manuels (CLAUDE.md, GEMINI.md)
- [ ] Tests de délégation complexe (Code Refactor)
- [ ] Intégration Knowledge Base via Driver logic

### Phase 3 : Intégration ACE+COMPASS (3-5 jours)
**Objectif** : Permettre la création de sous-agents des deux côtés

#### 2.1 Claude Sub-Agents
- [ ] Utiliser `Task` tool pour spawner des agents Claude spécialisés
- [ ] Agent "SQL Validator" (Claude)
- [ ] Agent "Report Generator" (Claude)

#### 2.2 Gemini Sub-Agents (via ADK)
- [ ] Installer Google ADK (`pip install google-adk`)
- [ ] Créer agent "Schema Analyzer" (Gemini)
- [ ] Créer agent "Query Generator" (Gemini)
- [ ] Créer agent "Data Synthesizer" (Gemini)

#### 2.3 Orchestration Hiérarchique
- [ ] Claude Principal → [Claude Sub + Gemini Sub]
- [ ] Délégation intelligente selon le type de tâche
- [ ] Consolidation des résultats

### Phase 3 : Intégration ACE+COMPASS (3-5 jours)
**Objectif** : Connecter NEXUS avec le système existant

#### 3.1 Accès à la Knowledge Base
- [ ] NEXUS peut interroger ChromaDB (531K chunks)
- [ ] Injecter contexte KB dans les requêtes Gemini
- [ ] Utiliser embeddings existants

#### 3.2 Réutilisation des Agents COMPASS
- [ ] Agent Planning peut déléguer à Gemini
- [ ] Agent Synthèse utilise Gemini pour consolidation
- [ ] Agent ISA envoie schémas complexes à Gemini

#### 3.3 ACE Playbooks pour NEXUS
- [ ] Créer playbooks spécifiques Claude-Gemini
- [ ] Self-improvement loop avec feedback croisé
- [ ] Mémorisation des patterns efficaces

### Phase 4 : Analyse SQL ERP (5-7 jours)
**Objectif** : Cas d'usage cible - analyser CEGID V11

#### 4.1 Chargement du Schéma
- [ ] Récupérer schéma CEGID V11 complet
- [ ] Indexer dans Gemini (1M tokens)
- [ ] Créer mapping sémantique tables/concepts

#### 4.2 Générateur de Requêtes
- [ ] Interface question naturelle → SQL
- [ ] Optimisation PostgreSQL automatique
- [ ] Validation syntaxique et sémantique

#### 4.3 Analyseur de Résultats
- [ ] Exécution des requêtes (si accès DB)
- [ ] Analyse des patterns dans les données
- [ ] Génération de rapports exécutifs

#### 4.4 Questions Métier Complexes
- [ ] "Impact retards paiement sur trésorerie"
- [ ] "Corrélation qualité/fournisseur"
- [ ] "Prévision charge atelier"

### Phase 5 : Production & Optimisation (1-2 semaines)
**Objectif** : Stabiliser et optimiser le système

#### 5.1 Performance
- [ ] Caching des résultats fréquents
- [ ] Parallélisation des requêtes
- [ ] Gestion mémoire contexte Gemini

#### 5.2 Robustesse
- [ ] Retry automatique (erreurs 503)
- [ ] Fallback Claude si Gemini indisponible
- [ ] Logging et monitoring

#### 5.3 UX
- [ ] Interface web pour NEXUS
- [ ] Dashboard des conversations
- [ ] Export des analyses

---

## Architecture Technique Recommandée

### Mode Recommandé : D (Hybride COMPASS + NEXUS)

```python
# Pseudo-code architecture

class NexusOrchestrator:
    def __init__(self):
        self.claude = ClaudeCLI()
        self.gemini = GeminiCLI(yolo=True)
        self.compass = CompassKB(chunks=531385)

    def process_question(self, user_question: str):
        # 1. Chercher contexte dans COMPASS
        kb_context = self.compass.search(user_question)

        # 2. Envoyer à Gemini pour analyse massive
        gemini_analysis = self.gemini.analyze(
            question=user_question,
            context=kb_context,
            schema=self.load_cegid_schema()
        )

        # 3. Gemini peut rappeler Claude pour clarification
        if gemini_analysis.needs_clarification:
            claude_response = self.claude.query(
                gemini_analysis.clarification_question
            )
            gemini_analysis = self.gemini.continue_with(claude_response)

        # 4. Générer rapport final
        return self.claude.synthesize(gemini_analysis)
```

### Commandes Clés

```bash
# Claude appelle Gemini (avec shell access)
gemini --yolo "Analyse ce schéma SQL: $(cat schema.sql)"

# Gemini appelle Claude
claude -p "Génère un test unitaire pour cette fonction"

# Mode conversation (dans Gemini interactif)
gemini  # Lance REPL
> /shell claude -p "Question pour Claude"
```

---

## Métriques de Succès

| Métrique | Cible | Comment Mesurer |
|----------|-------|-----------------|
| Latence échange | < 30s | Timer sur chaque appel |
| Taux de succès | > 95% | Ratio succès/échecs |
| Qualité SQL | > 90% | Validation syntaxique |
| Satisfaction user | > 4/5 | Feedback questionnaire |
| Contexte Gemini utilisé | > 100K tokens | Monitoring API |

---

## Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Timeout Gemini | Moyenne | Bloquant | Retry + timeout config |
| Erreur 503 API | Haute | Retard | Exponential backoff |
| Contexte perdu | Moyenne | Qualité | GEMINI.md persistant |
| Coût API | Faible | Budget | Quotas gratuits suffisants |
| Sécurité shell | Moyenne | Critique | Sandboxing, validation inputs |

---

## Prochaines Actions Immédiates

1. **Aujourd'hui** : Tester échange bidirectionnel complet avec `--yolo`
2. **Demain** : Créer `nexus_bridge.py` v2 avec logging visible
3. **Cette semaine** : Phase 1 complète + début Phase 2

---

## Notes Techniques

### Gemini CLI avec Shell
```bash
gemini --yolo "question"  # Auto-approve toutes les actions
gemini --sandbox=false    # Désactive sandbox (dangereux)
```

### Claude CLI Non-Interactif
```bash
claude -p "question"      # Mode prompt unique
claude --print "question" # Alias
```

### Quotas Disponibles
- **Gemini (GoogleAI Ultra)** : Quota élevé
- **Claude (Max 20x)** : 20x le quota standard

---

*Roadmap créée le 18/11/2025*
*Phase actuelle : Expérimentale*
*Responsable : Yann ABADIE + Claude Code*
