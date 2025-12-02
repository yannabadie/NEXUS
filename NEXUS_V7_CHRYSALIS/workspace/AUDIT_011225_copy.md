# Plan de Remédiation NEXUS V7 - Communication Gemini↔Claude
Action: Diagnostic complet + Plan de remédiation
Statut: ✅ ANALYSE TERMINÉE

## 🔴 PROBLÈMES CRITIQUES IDENTIFIÉS

### BUG #1: ALTERNANCE NON FORCÉE (BRAINSTORMING)
Fichier: orchestration_v7.py:636-639

```python
# CODE ACTUEL (CASSÉ)
next_agent = message.get("next_agent", self.active_agent)  # ⚠️ Default = reste sur le même
if next_agent != self.active_agent:
    self.active_agent = next_agent
```

Problème: L'orchestrateur dépend de next_agent dans la réponse de l'agent. Si l'agent ne renvoie pas next_agent, l'alternance ne se fait PAS!

Preuve: Le mode EVOLUTION_BRAINSTORM (lignes 796-798) FORCE l'alternance:

```python
# FONCTIONNE CORRECTEMENT
self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
```

### BUG #2: CLAUDE DRIVER GARDE "CLAUDE" PAR DÉFAUT
Fichier: claude_driver_hybrid.py:298-301

```python
# CODE ACTUEL (CASSÉ)
next_agent = "Claude"  # ⚠️ Default = reste sur Claude!
if "gemini" in content.lower() and action_type == "TALK":
    next_agent = "Gemini"  # Seulement si "gemini" est mentionné
```

Problème: Claude ne délègue à Gemini que si le mot "gemini" apparaît dans sa réponse!

### BUG #3: MODE SWARM - ERREURS CLAUDE SILENCIEUSES
Fichier: mode_executors.py:129-167

Les executors détectent les erreurs mais ne les montrent pas clairement à l'utilisateur. Si Claude timeout, l'output n'est pas formaté correctement.

---

## ✅ PLAN DE REMÉDIATION DÉTAILLÉ

### CORRECTION #1: Forcer l'alternance dans BRAINSTORMING
Fichier: orchestration_v7.py Lignes: 636-641

```python
# AVANT (CASSÉ):
next_agent = message.get("next_agent", self.active_agent)
if next_agent != self.active_agent:
    self.active_agent = next_agent
    self.stagnation_detector.reset()

# APRÈS (CORRIGÉ):
# V7 FIX: FORCE alternance égale Gemini↔Claude (comme EVOLUTION_BRAINSTORM)
# L'alternance ne doit PAS dépendre de next_agent de l'agent
previous_agent = self.active_agent
self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
self.stagnation_detector.reset()

# Log l'alternance
if self.config.ui_verbose:
    print(f"[FSM] Agent switch: {previous_agent} → {self.active_agent}")
```

### CORRECTION #2: Claude driver - Alterner par défaut
Fichier: claude_driver_hybrid.py Lignes: 298-301

```python
# AVANT (CASSÉ):
next_agent = "Claude"  # Default stay with Claude
if "gemini" in content.lower() and action_type == "TALK":
    next_agent = "Gemini"

# APRÈS (CORRIGÉ):
# V7 FIX: Alterner par défaut pour collaboration égale
# L'orchestrateur force déjà l'alternance, mais on aide ici aussi
next_agent = "Gemini"  # Default: passer à Gemini après chaque réponse
if "je continue" in content.lower() or "i'll continue" in content.lower():
    next_agent = "Claude"  # Claude garde la main seulement si explicite
```

### CORRECTION #3: Améliorer feedback visuel SWARM
Fichier: orchestration_v7.py Lignes: 502-520 (dans process_turn, section SWARM output)

```python
# AJOUTER avant formatted_output:
# V7 FIX: Montrer clairement qui parle et détecter les erreurs
for agent_data in agent_outputs:
    agent_id = agent_data.get("agent_id", "")
    content = agent_data.get("content", "")
    status = agent_data.get("status", "success")
    agent_name = "Gemini" if "gemini" in agent_id.lower() else "Claude"

    if status == "error" or content.startswith("Error:"):
        formatted_output += f"\n🔴 {agent_name} ERROR:\n{content}\n---\n"
    else:
        formatted_output += f"\n🟢 {agent_name}:\n{content}\n---\n"
```

### CORRECTION #4: Ajouter logs de debug pour tracer le flux
Fichier: orchestration_v7.py Ajouter après ligne 583 (dans BRAINSTORMING, après response = self._invoke_agent()):

```python
# V7 DEBUG: Tracer les invocations d'agents
self.logger.debug("Agent invoked", {
    "agent": self.active_agent,
    "response_preview": str(response)[:200],
    "action_type": response.get("action_type"),
    "next_agent": response.get("next_agent")
})
```

---

## 📋 RÉSUMÉ DES FICHIERS À MODIFIER

| Fichier | Lignes | Correction |
|---------|--------|------------|
| orchestration_v7.py | 636-641 | Forcer alternance |
| orchestration_v7.py | 502-520 | Améliorer feedback SWARM |
| orchestration_v7.py | ~583 | Ajouter logs debug |
| claude_driver_hybrid.py | 298-301 | Alterner par défaut |

---

## ⚡ PRIORITÉ D'EXÉCUTION

| Priorité | Correction | Description |
|----------|------------|-------------|
| P0 CRITIQUE | #1 (alternance forcée) | C'est LE bug principal |
| P1 HAUTE | #2 (Claude driver) | Support additionnel |
| P2 MOYENNE | #3 (feedback visuel) | UX |
| P3 BASSE | #4 (logs debug) | Diagnostic |

---

## 🔬 ANALYSE APPROFONDIE - 8 POINTS DE RUPTURE

### NIVEAU 1: ARCHITECTURE (cause racine)

| # | Fichier | Ligne | Problème | Impact |
|---|---------|-------|----------|--------|
| 1 | config.py | 178 | swarm_auto_route=True par défaut | TOUTES les requêtes passent par SWARM |
| 2 | orchestration_v7.py | 475-541 | SWARM capture et retourne avant BRAINSTORMING | Pas d'alternance classique |

### NIVEAU 2: BRAINSTORMING (si SWARM fallback)

| # | Fichier | Ligne | Problème | Impact |
|---|---------|-------|----------|--------|
| 3 | orchestration_v7.py | 636 | next_agent = message.get("next_agent", self.active_agent) | Default = reste sur le même agent |
| 4 | protocol_v7.py | 74-76 | Validateur: si next_agent=None → return sender | Renforce le bug #3 |
| 5 | claude_driver_hybrid.py | 298-301 | next_agent = "Claude" par défaut | Claude ne délègue jamais à Gemini |

### NIVEAU 3: SWARM (si utilisé)

| # | Fichier | Ligne | Problème | Impact |
|---|---------|-------|----------|--------|
| 6 | orchestration_v7.py | 509-515 | Erreurs Claude formatées mais pas clairement visibles | User ne voit pas les erreurs |
| 7 | claude_driver_hybrid.py | 164-175 | Timeout = Exception silencieuse | Pas de feedback utilisateur |
| 8 | orchestration_v7.py | 246-254 | _invoke_for_swarm catch exceptions → return f"Error: {e}" | Erreur avalée |

---

## ✅ PREUVE QUE L'ALTERNANCE FORCÉE FONCTIONNE

Mode EVOLUTION_BRAINSTORM (lignes 796-798):

```python
# FORCE ALTERNATION in evolution mode - equal participation
previous_agent = self.active_agent
self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
```

**CE CODE N'EXISTE PAS DANS BRAINSTORMING NORMAL!**

---

## 📊 RÉSUMÉ FINAL

Le problème fondamental est **triple**:

1. **SWARM activé par défaut** → Bypass le BRAINSTORMING
2. **BRAINSTORMING ne force pas l'alternance** (contrairement à EVOLUTION_BRAINSTORM)
3. **Claude driver garde Claude** → Pas de passage à Gemini

Les corrections P0 critiques ont été identifiées et le plan de remédiation est prêt.
