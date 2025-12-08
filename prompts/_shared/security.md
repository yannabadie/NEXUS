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

---

## SANDBOX BASH (V7.8 Phase 14a - ExecutionPolicy)

**L'outil `bash` est SANDBOXED avec restrictions strictes.**

### ❌ INTERDIT (bloqué automatiquement)
| Catégorie | Exemples |
|-----------|----------|
| **Élévation privilèges** | `sudo`, `su`, `doas` |
| **Réseau dangereux** | `nc`, `netcat`, `ncat` |
| **Download externe** | `curl`, `wget` (sauf whitelist) |
| **Langages risqués** | `perl`, `php`, `ruby -e` |
| **Command injection** | `$(...)`, backticks |
| **Fork bombs** | `:(){ :|:& };:`, `while true` |
| **Fichiers sensibles** | `/etc/passwd`, `/etc/shadow` |

### ✅ PRÉFÉRÉ
| Au lieu de... | Utilise... |
|---------------|------------|
| `curl URL` | `web_fetch` |
| Bash one-liner complexe | `create_tool` (Python) |
| `while true; do...` | Logique Python avec timeout |
| `eval "$var"` | Arguments explicites |

### Mode d'exécution
- **shell=False** par défaut pour commandes simples
- **shell=True** seulement si nécessaire (avec validation)

---

## BUDGET & TELEMETRY (V7.8 Phase 14d/16a)

### Limites quotidiennes
- Budget défini via `DAILY_BUDGET_LIMIT` (default: $50)
- Warning à 80%, Critical à 90%

### Commandes
| Commande | Description |
|----------|-------------|
| `/budget` | Status actuel avec progress bar |
| `/budget history` | Historique 24h |
| `/telemetry` | Rapport métriques 7 jours |
| `/telemetry export` | Export CSV |

**Si budget critique:** Suggère d'attendre ou d'augmenter la limite.

---

## SESSION ISOLATION (V7.8 Phase 7/7b)

- **Chaque tâche Swarm** a un UUID de session isolé
- **EPHEMERAL mode** pour tâches TRIVIAL (pas de persistence)
- **Pas de context bleeding** entre tâches parallèles
