# 🧠 NEXUS Learning Engine

## Vue d'ensemble

Le **NEXUS Learning Engine** est un système d'apprentissage automatique qui analyse les logs d'interactions DRIVER/WORKER pour extraire des patterns de succès et d'erreur, et générer automatiquement un PLAYBOOK de stratégies optimales.

## Architecture

Basé sur le framework **ACE (Autonomous Cognitive Entities)** de Stanford (arXiv:2510.04618), le système implémente une boucle en 3 phases :

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  GENERATOR  │ ───> │  REFLECTOR   │ ───> │   CURATOR   │
│   Phase 1   │      │   Phase 2    │      │   Phase 3   │
└─────────────┘      └──────────────┘      └─────────────┘
      │                     │                      │
  Parse logs          Extrait patterns      Update PLAYBOOK.md
  → Traces           → Analyse traces       → Merge patterns
```

### Phase 1 - GENERATOR
- Parse `CHAT_HISTORY_MASTER.md`
- Extrait les interactions DRIVER → WORKER
- Crée des traces d'exécution structurées

### Phase 2 - REFLECTOR
- Analyse les traces par agent et type d'action
- Détecte les patterns récurrents
- Calcule la confiance et le taux de succès

### Phase 3 - CURATOR
- Merge les nouveaux patterns avec l'existant
- Filtre les patterns de faible confiance
- Génère/met à jour `PLAYBOOK.md`

## Installation

Aucune dépendance externe requise - utilise uniquement la bibliothèque standard Python 3.7+

```bash
# Vérifier que Python est installé
python --version

# Le script est prêt à l'emploi
cd 20_NEXUS/NEXUS_KERNEL/SKILLS
python nexus_learning.py --help
```

## Usage

### 1. Analyser les logs et mettre à jour le PLAYBOOK

**Méthode 1 - Script batch (Windows)**
```batch
cd 20_NEXUS\NEXUS_KERNEL\SKILLS
LEARN.bat
```

**Méthode 2 - Python direct**
```bash
python nexus_learning.py --learn ../MEMORY/ARCHIVES/CHAT_HISTORY_MASTER.md
```

**Méthode 3 - Chemin personnalisé**
```bash
python nexus_learning.py \
  --learn path/to/history.md \
  --playbook path/to/PLAYBOOK.md
```

### 2. Voir les statistiques du PLAYBOOK

**Méthode 1 - Script batch**
```batch
LEARN.bat --stats
```

**Méthode 2 - Python direct**
```bash
python nexus_learning.py --stats
```

### 3. Obtenir une suggestion de stratégie

```bash
python nexus_learning.py --suggest "deploy infrastructure"
```

### 4. Paramètres avancés

```bash
python nexus_learning.py \
  --learn history.md \
  --min-confidence 0.70 \
  --min-examples 3
```

## Configuration

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `--min-confidence` | 0.60 | Confiance minimale pour accepter un pattern (0.0 à 1.0) |
| `--min-examples` | 2 | Nombre minimum d'occurrences pour détecter un pattern |
| `--playbook` | `../MEMORY/PLAYBOOK.md` | Chemin vers le fichier PLAYBOOK |

## Format des logs

Le Learning Engine analyse les logs au format suivant :

```markdown
### 🧠 **DRIVER (Gemini)** - 2025-11-19 16:50
*Task:* Description de la tâche
*Command:* `commande optionnelle`

---

### 🤖 **WORKER (agent_name)** - 2025-11-19 16:50
*Status: SUCCESS*
*Details:*
- Détails de l'exécution
- Résultats obtenus

*Status:* **STATUT FINAL**
```

### Variantes acceptées
- **Status** : `SUCCESS`, `FAILURE`, `PARTIAL`, `UNKNOWN`
- **Format alternatif** : `*Result: SUCCESS*` au lieu de `*Status: SUCCESS*`
- **Agent** : Détecte automatiquement le nom (scout, coder, architect, etc.)

## Structure du PLAYBOOK généré

Le PLAYBOOK.md est organisé en 4 catégories :

### ✅ Stratégies de Succès
Patterns d'exécutions réussies à reproduire

### ❌ Patterns d'Erreur
Erreurs récurrentes à éviter avec recommandations

### ⚡ Optimisations
Améliorations détectées automatiquement

### 💡 Insights Domaine
Connaissances spécifiques au domaine extraites

Chaque pattern contient :
- **ID unique** : PAT-{agent}-{timestamp}
- **Type et confiance** : Niveau de fiabilité du pattern
- **Taux de succès** : Ratio succès/échecs observés
- **Contexte déclencheur** : Quand appliquer la stratégie
- **Stratégie recommandée** : Que faire
- **Agents concernés** : Quels agents sont impactés
- **Exemples** : Extraits d'exécutions réelles

## Exemples de patterns détectés

### Exemple 1 - Stratégie de succès
```
✅ PAT-scout-20251120-150813
Confiance: 100.0% | Taux succès: 100.0%
Observations: 5 fois

Contexte: Lecture et analyse de fichiers de contexte (CLAUDE.md)
Stratégie: Toujours lire le contexte complet avant d'exécuter une tâche
Agents: scout, coder
```

### Exemple 2 - Pattern d'erreur
```
❌ PAT-architect-20251120-151034
Confiance: 85.0% | Taux succès: 15.0%
Observations: 7 fois

Contexte: Déploiement infrastructure sans vérification préalable
Stratégie: ⚠️ Erreur récurrente: missing dependencies.
         Vérifier prérequis avant exécution (pip install, npm install)
Agents: architect, coder
```

## Workflow recommandé

### 1. Développement continu
```bash
# Après chaque session de travail
cd 20_NEXUS/NEXUS_KERNEL/SKILLS
LEARN.bat

# Consulter le PLAYBOOK mis à jour
type ..\MEMORY\PLAYBOOK.md
```

### 2. Analyse périodique
```bash
# Hebdomadaire : analyser tendances
LEARN.bat --stats

# Comparer avec version précédente
git diff ../MEMORY/PLAYBOOK.md
```

### 3. Amélioration continue
- Examiner patterns de faible confiance (< 70%)
- Investiguer patterns d'erreur récurrents
- Documenter patterns manuellement si nécessaire

## Debugging

### Le parser ne trouve aucune trace
```bash
# Vérifier format du fichier log
cat CHAT_HISTORY_MASTER.md | head -20

# Format attendu: sections ### avec 🧠/🤖
# Si différent: adapter les regex dans ExecutionTrace.from_log_entry()
```

### Patterns non détectés
```bash
# Réduire seuil de confiance
python nexus_learning.py --learn history.md --min-confidence 0.50

# Réduire nombre d'exemples minimum
python nexus_learning.py --learn history.md --min-examples 2
```

### PLAYBOOK vide après exécution
```bash
# Vérifier chemin du fichier créé
python nexus_learning.py --learn history.md 2>&1 | grep "PLAYBOOK.md"

# Utiliser chemin absolu
python nexus_learning.py \
  --learn "C:/full/path/to/history.md" \
  --playbook "C:/full/path/to/PLAYBOOK.md"
```

## Intégration CI/CD

### GitHub Actions
```yaml
- name: Update NEXUS Playbook
  run: |
    cd 20_NEXUS/NEXUS_KERNEL/SKILLS
    python nexus_learning.py --learn ../MEMORY/ARCHIVES/CHAT_HISTORY_MASTER.md
    git add ../MEMORY/PLAYBOOK.md
    git commit -m "chore: update NEXUS PLAYBOOK [skip ci]"
```

### Cron Job (Linux/Mac)
```bash
# Mise à jour quotidienne à 2h du matin
0 2 * * * cd /path/to/20_NEXUS/NEXUS_KERNEL/SKILLS && python nexus_learning.py --learn ../MEMORY/ARCHIVES/CHAT_HISTORY_MASTER.md
```

## Évolutions futures

### Version 1.1 (planifié)
- [ ] Parser patterns existants depuis PLAYBOOK.md (merge intelligent)
- [ ] Détection d'optimisations automatiques
- [ ] Extraction d'insights domaine via NLP
- [ ] Export JSON des patterns pour intégration externe

### Version 1.2 (roadmap)
- [ ] Interface web de visualisation patterns
- [ ] Suggestions proactives pendant exécution
- [ ] A/B testing de stratégies alternatives
- [ ] Intégration avec système de métriques

## Support

**Documentation complète** : `20_NEXUS/NEXUS_KERNEL/SKILLS/nexus_learning.py` (docstrings)

**Exemples** : `20_NEXUS/NEXUS_KERNEL/MEMORY/PLAYBOOK.md` (généré automatiquement)

**Contact** : Voir fichier `CLAUDE.md` pour équipe projet

---

**Version** : 1.0
**Date** : 2025-11-20
**Auteur** : NEXUS Project
**License** : Propriétaire Motherson Aerospace
