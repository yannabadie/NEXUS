# NEXUS - Plan de Restauration MVN (Minimum Viable NEXUS)
## Diagnostic Système - 2025-11-20

### 📊 ÉTAT ACTUEL

#### Architecture Observable
```
20_NEXUS/
├── NEXUS_KERNEL/        ✅ Intact - Contient protocoles et documentation
├── _ARCHIVE_2025/       ✅ Code legacy préservé (bridge, core, agents)
├── 02_CORE/            ❌ VIDE - Doit contenir le moteur principal
├── 02_Bridge/          ❌ VIDE - Doit contenir la communication
├── 03_Agents/          ⚠️  MCP skeleton uniquement (pas d'agents métier)
└── .venv/              ✅ Environnement Python configuré
```

#### Analyse des Lacunes
1. **Pas de Core opérationnel** : Le cerveau du système est absent
2. **Pas de Bridge actif** : Aucune communication Driver↔Worker
3. **Mémoire non persistante** : Pas de système de stockage actif
4. **Agents non intégrés** : MCP existe mais déconnecté du core

### 🎯 OBJECTIF MVN

Restaurer une capacité opérationnelle minimale en 3 phases :

## PHASE 1 : BRIDGE MINIMAL (Priorité CRITIQUE)
**Objectif** : Rétablir communication Driver↔Worker
**Durée estimée** : 2 heures

### Actions :
1. **Créer `02_Bridge/nexus_bridge.py`**
   - Port du code de `_ARCHIVE_2025/legacy_core/persistent_bridge.py`
   - Simplification : Focus sur IPC via fichiers (plus simple que MCP pour démarrer)
   - Structure minimale :
     ```python
     class NexusBridge:
         def __init__(self):
             self.session_id = generate_session_id()
             self.ipc_dir = Path("02_Bridge/ipc")

         def send_to_worker(self, message):
             # Écriture dans fichier IPC

         def receive_from_worker(self):
             # Lecture depuis fichier IPC
     ```

2. **Créer structure IPC**
   ```
   02_Bridge/
   ├── nexus_bridge.py
   └── ipc/
       ├── driver_to_worker.json
       ├── worker_to_driver.json
       └── session_state.json
   ```

## PHASE 2 : CORE MINIMAL
**Objectif** : Moteur de traitement basique
**Durée estimée** : 3 heures

### Actions :
1. **Créer `02_CORE/nexus_core.py`**
   - Port sélectif de `_ARCHIVE_2025/nexus.py`
   - Fonctions essentielles :
     ```python
     class NexusCore:
         def __init__(self):
             self.bridge = NexusBridge()
             self.memory = MemoryManager()
             self.protocol = load_protocol("NEXUS_KERNEL/CORE_PROTOCOL.md")

         def process_instruction(self, instruction):
             # Logique de traitement selon protocole

         def execute_task(self, task):
             # Exécution avec logging
     ```

2. **Créer `02_CORE/memory.py`**
   - Système de mémoire simplifié
   - SQLite pour persistance (comme dans legacy)
   - Index des conversations et décisions

## PHASE 3 : INTERFACE CLI MINIMALE
**Objectif** : Point d'entrée utilisable
**Durée estimée** : 1 heure

### Actions :
1. **Créer `nexus.py` à la racine**
   ```python
   #!/usr/bin/env python
   """NEXUS CLI - Minimum Viable Interface"""

   from 02_CORE.nexus_core import NexusCore

   def main():
       print("NEXUS MVN - Initializing...")
       nexus = NexusCore()

       while True:
           command = input("NEXUS> ")
           if command == "exit":
               break
           result = nexus.process_instruction(command)
           print(f"[NEXUS]: {result}")
   ```

2. **Créer `start_nexus.bat`**
   ```batch
   @echo off
   .venv\Scripts\activate && python nexus.py
   ```

### 🚀 RÉSULTAT ATTENDU POST-MVN

Un système NEXUS minimal mais fonctionnel avec :
- ✅ Communication Driver↔Worker via IPC
- ✅ Core capable de traiter des instructions basiques
- ✅ Mémoire persistante des interactions
- ✅ Interface CLI pour interaction directe
- ✅ Base solide pour reconstruction progressive

### 📋 PROCHAINES ÉTAPES (POST-MVN)

1. **Intégration MCP** : Migrer de IPC vers MCP pour scalabilité
2. **Agents Spécialisés** : Réactiver agents métier (historian, analyst)
3. **Self-Learning** : Implémenter moteur ACE
4. **God Mode** : Activer capacités étendues selon protocole

### ⚠️ RISQUES IDENTIFIÉS

1. **Dépendances manquantes** : Vérifier packages Python nécessaires
2. **Conflit de versions** : Legacy code vs nouvelles APIs
3. **Perte de contexte** : Documentation incomplète sur certains modules

### 💡 RECOMMANDATION ARCHITECTE

**Commencer par le Bridge** est critique car sans communication, aucune autre fonction n'est utile. L'approche IPC (fichiers) est plus robuste que MCP pour un MVN car :
- Pas de dépendance réseau
- Debugging plus simple
- Persistance naturelle
- Migration vers MCP possible ultérieurement

---

*Diagnostic effectué le 2025-11-20*
*Architecte : Claude (Worker NEXUS)*
*Statut : En attente validation Driver pour exécution*