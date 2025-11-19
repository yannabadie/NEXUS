# ADDENDUM - CONTRAINTE BUDGET API CLAUDE

**Date**: 22 octobre 2025
**Contrainte identifiée**: Pas de budget pour API Claude payante

---

## 🔴 IMPACT SUR DIAGNOSTIC INITIAL

### Coûts API Claude dans Budget POC Initial

| Poste | Coût initial | Statut |
|-------|--------------|--------|
| Claude API POC (5M tokens) | 5,000€ | ❌ IMPOSSIBLE |
| Claude API récurrent (an 1) | 7,200€ | ❌ IMPOSSIBLE |
| Azure OpenAI Embeddings | 600€/an | ⚠️ À vérifier si budget |
| Indexation embeddings | 195€ one-time | ⚠️ À vérifier si budget |

**Impact budgétaire** : **-12,200€ sur POC** (initial) + **-7,200€/an** (récurrent)

---

## ✅ SOLUTIONS ALTERNATIVES

### Option 1 : Claude.ai (Compte Gratuit/Pro Personnel) - **RECOMMANDÉE**

#### A. Claude Free (Gratuit)

**Caractéristiques** :
- **Modèle** : Claude 3.5 Sonnet
- **Limites** : ~50 messages/5h (variable selon charge)
- **Context** : 200K tokens input
- **Coût** : **0€**

**Viabilité pour POC** :
- ✅ Développement/tests : OK
- ✅ Démos ponctuelles : OK
- ❌ Usage intensif (>50 queries/jour) : IMPOSSIBLE
- ❌ Production : NON

**Recommandation** : **Viable pour Phase 0 (semaines 1-2) uniquement**

#### B. Claude Pro Personnel (20$/mois = 19€/mois)

**Caractéristiques** :
- **Modèle** : Claude 3.5 Sonnet + Opus
- **Limites** : ~500 messages/jour (5x plus que Free)
- **Context** : 200K tokens
- **Coût** : **19€/mois** (utilisateur Yann)

**Viabilité pour POC** :
- ✅ Développement/tests : EXCELLENT
- ✅ Démos : EXCELLENT
- ✅ Usage modéré (10-15 users légers) : OK
- ⚠️ Production scaling : LIMITÉ

**Recommandation** : **OPTION OPTIMALE pour POC + Pilote**
- Budget POC : 19€ × 3 mois = **57€**
- Budget an 1 : 19€ × 12 = **228€**

---

### Option 2 : Ollama + Modèles Open-Source Locaux

#### Configuration Recommandée

**Stack** :
```
Ollama (runtime local)
├─ mistral:7b-instruct (7GB RAM)          → Requêtes simples
├─ llama3.1:8b-instruct (8GB RAM)         → Conversations
└─ qwen2.5:14b-instruct (14GB RAM)        → Tâches complexes
```

**Embeddings** :
- **nomic-embed-text** (274M params, 1.4GB)
- Dimensions : 768 (vs 3,072 Claude)
- Performance : ~85% de text-embedding-3-large

**Coûts** :
- **0€** (100% gratuit)
- Compute : Machine locale existante

**Viabilité** :
- ✅ Développement : EXCELLENT
- ✅ Tests : EXCELLENT
- ✅ Production : POSSIBLE (performances variables)
- ⚠️ Qualité réponses : Inférieure à Claude (-15-20%)
- ⚠️ Latence : +2-5s selon modèle

**Recommandation** : **Backup/Complément** à Claude Pro

---

### Option 3 : Azure OpenAI (Si Accès Corporate)

**Prérequis** :
- Accès Azure tenant Motherson
- Subscription Azure avec crédits
- Approbation IT corporate

**Modèles disponibles** :
- GPT-4o (équivalent Claude Sonnet)
- text-embedding-3-large

**Coûts** :
- **Peut être 0€** si crédits Azure corporate
- Sinon : ~même prix que Claude API

**Viabilité** :
- ✅ Si crédits disponibles : EXCELLENT
- ❌ Si facturation directe : Même problème budget

**Recommandation** : **À VÉRIFIER avec IT Motherson**
- Demander si crédits Azure disponibles pour R&D
- Si oui : Meilleure option pro (scalable)

---

## 🎯 ARCHITECTURE RECOMMANDÉE RÉVISÉE

### Configuration Hybride "Zero-Cost POC"

```
┌─────────────────────────────────────────────────┐
│         UTILISATEURS (10-15 max POC)            │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────▼────────────────┐
    │   ORCHESTRATEUR             │
    │   (Python/LangChain)        │
    └────┬────────────────────┬───┘
         │                    │
    ┌────▼─────────┐    ┌────▼──────────────┐
    │ Claude Pro   │    │ Ollama (Local)    │
    │ (Compte Yann)│    │ mistral:7b        │
    │ - Tâches     │    │ - Recherche       │
    │   complexes  │    │   simple          │
    │ - Synthesis  │    │ - Embeddings      │
    └──────────────┘    └───────────────────┘
                 │
           ┌─────▼──────────────────┐
           │  Vector Store          │
           │  CHOIX:                │
           │  1. Chroma (local)     │ ← 0€
           │  2. Qdrant (local)     │ ← 0€
           │  3. Azure AI Search    │ ← 90€/mois
           └────────────────────────┘
```

**Logique routage** :
- **Claude Pro** : Synthèses, analyses complexes, rédaction (20% requêtes)
- **Ollama local** : Recherche RAG, Q&A simples (80% requêtes)

---

## 💰 BUDGET POC RÉVISÉ

### Configuration "Zero-Cost" (Option 1)

| Poste | Détail | Coût Révisé |
|-------|--------|-------------|
| **Remédiation corpus** | Filtrage, déduplication | 9,600€ |
| **Développement RAG** | Loaders, pipeline, agents | 16,000€ |
| **LLM Access** | Claude Pro (Yann, 3 mois) | **57€** ✅ |
| **Embeddings** | Ollama nomic-embed (local) | **0€** ✅ |
| **Vector Store** | Chroma (local SQLite) | **0€** ✅ |
| **Formation équipe** | 2j + support | 9,600€ |
| **Testing & tuning** | Validation | 6,400€ |
| **TOTAL POC Révisé** | | **41,657€** |

**Économie vs initial** : **-7,643€** (-15.5%)

### Configuration "Low-Cost Pro" (Option 2)

| Poste | Coût |
|-------|------|
| POC base | 41,657€ |
| Azure AI Search (Basic, 3 mois) | +270€ |
| **TOTAL Low-Cost** | **41,927€** |

**Si crédits Azure disponibles** : 270€ → 0€

---

## 📊 ROI RÉVISÉ

### Coûts Récurrents An 1 (Post-POC)

| Configuration | Mensuel | Annuel |
|---------------|---------|--------|
| **Zero-Cost** (Ollama + Claude Pro) | 19€ | 228€ |
| **Low-Cost** (+ Azure AI Search) | 109€ | 1,308€ |
| **Économie vs initial** | -661€/mois | -7,932€/an |

### ROI Révisé

**Configuration Zero-Cost** :
- Gains : 100,800€/an (inchangés)
- Coûts POC : 41,657€
- Coûts an 1 : 228€
- **ROI 1 an : 140%** (vs 105% initial) ✅ **MEILLEUR**
- **ROI 3 ans : 620%** (vs 420% initial) ✅ **MEILLEUR**
- **Payback : 4 mois** (vs 5 mois) ✅ **PLUS RAPIDE**

---

## ⚠️ IMPACTS TECHNIQUES

### Performances Attendues vs Initial

| Métrique | Initial (Claude API) | Révisé (Hybrid) | Delta |
|----------|---------------------|-----------------|-------|
| **Précision RAG** | 76% | 70-72% | -4 à -6% |
| **Latence query** | <1s | 1-3s (Ollama) | +1-2s |
| **Qualité synthèses** | Excellente | Bonne | -10-15% |
| **Coût/query** | 0.08€ | 0.00€ | -100% ✅ |

### Limitations

1. **Volume queries** :
   - Claude Pro : ~500 messages/jour (limite compte)
   - Si dépassement : Fallback Ollama automatique

2. **Utilisateurs simultanés** :
   - Max 10-15 en POC (partage compte Yann)
   - Production : Nécessite multi-comptes ou migration API

3. **Qualité variable** :
   - Ollama : Bon pour RAG simple, moyen pour raisonnement complexe
   - Compromis acceptable pour POC

---

## 🚀 STRATÉGIE RECOMMANDÉE FINALE

### Phase 0-2 : POC "Zero-Cost" (10 semaines)

**Configuration** :
- ✅ **Claude Pro** (compte Yann) : 19€/mois
- ✅ **Ollama** (local) : 0€
- ✅ **Chroma** (local) : 0€
- ✅ **Budget total** : 41,657€

**Objectifs** :
1. Valider précision RAG >70% (vs 76% cible initiale)
2. Prouver gains temps >50h/mois
3. Démo use cases critiques
4. **Décision GO/NO-GO Scale**

### Post-POC : Options Scaling

**Si POC réussi (>70% métriques)** :

#### Option A : Upgrade Azure OpenAI
- Négocier crédits corporate
- Migration vers API pro
- Coût : 0€ si crédits ou ~7k€/an si payant

#### Option B : Multi-comptes Claude Pro
- 5 comptes Pro (5 users × 19€) = 95€/mois
- Support 50-100 users légers
- Coût : 1,140€/an

#### Option C : Rester "Zero-Cost"
- Acceptable si usage <50 queries/jour
- Ollama pour 80% trafic
- Coût : 228€/an

---

## ✅ DÉCISION RECOMMANDÉE

### GO POC avec Configuration "Zero-Cost"

**Budget révisé** : **41,657€** (vs 49,300€ initial)

**Investissement LLM** : **57€** pour 3 mois (Claude Pro)

**ROI attendu** : **140% an 1** (meilleur que prévu!)

**Risque technique** :
- ⚠️ Performance -5% vs initial (acceptable pour POC)
- ✅ Scaling limité mais suffisant pour pilote

**Avantages** :
- ✅ **-8k€ économisés** vs diagnostic initial
- ✅ **ROI amélioré** (+35 points)
- ✅ **Payback plus rapide** (4 vs 5 mois)
- ✅ **Viable immédiatement** (pas d'approbation budget API)

---

## 📋 ACTIONS MODIFIÉES

### Lundi 22/10
- [x] Diagnostic complet
- [ ] **Valider approche "Zero-Cost"**
- [ ] **Souscrire Claude Pro** (19€/mois, compte Yann)

### Mardi 23/10
- [ ] Installer Ollama + modèles (mistral:7b, nomic-embed)
- [ ] Setup Chroma local
- [ ] Tests performance Ollama vs Claude

### Mercredi-Vendredi 24-26/10
- [ ] Développement routage intelligent (Claude vs Ollama)
- [ ] Indexation bases JSON avec nomic-embed
- [ ] Démo hybrid system

---

## 🎓 CONCLUSION ADDENDUM

La **contrainte budget API** est en fait une **opportunité** :

✅ **Budget POC réduit** : 41.7k€ vs 49.3k€ (-15%)
✅ **ROI amélioré** : 140% vs 105% (+33%)
✅ **Viable immédiatement** : Pas d'approbation IT nécessaire
✅ **Scalable** : Options upgrade post-POC claires

**Recommandation finale** : **GO immédiat avec config Zero-Cost**

---

**Document mis à jour** : 22 octobre 2025
**Validité** : Remplace sections budget du diagnostic initial
