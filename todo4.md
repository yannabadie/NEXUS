# ⚡ DIRECTIVES DE RECADRAGE ARCHITECTURAL (AUDIT POST-EXECUTION)

Bonjour. J'ai audité tes récents commits sur le Master Plan V12.4. Tu as fait un travail d'ingénierie exceptionnel. L'implémentation des SDKs (Anthropic, GenAI), l'ajout proactif du driver Ollama pour la frugalité, l'Event Sourcing, le Sandboxing et le protocole A2A démontrent une compréhension parfaite de l'architecture cible. Ton respect du TDD est également validé (ratio 1:1 entre les modules et les tests).

Cependant, tu souffres d'une aversion à la perte et tu n'as pas respecté les consignes de suppression. Tu DOIS régler ces 3 points stricts immédiatement dans un seul commit de nettoyage :

1. **Le Syndrome de Diogène (Rigueur de suppression) :** 
Une codebase Cloud-Native saine exige des suppressions pour éviter la confusion cognitive de l'orchestrateur au runtime.
- SUPPRIME immédiatement `scripts/migrate_v9_to_v10.py`, `requirements_v7.txt`, `nexus7.bat` et `install_v7.ps1` (nous utilisons `pyproject.toml` désormais).
- SUPPRIME intégralement les dossiers `docs/archive/legacy/` et `docs/archive/legacy_asi/`.
- DÉDUPLIQUE les drivers : supprime `gemini_driver_v7.py`, `claude_driver_hybrid.py` et `async_claude_driver.py` de la racine de `core/drivers/` puisqu'ils sont censés être UNIQUEMENT dans `core/drivers/legacy/`.

2. **L'Initiative Rust (`rust/nexus_core/`) :**
J'ai remarqué que tu as introduit une extension native en Rust (`Cargo.toml`, `lib.rs`). C'est une brillante initiative pour la performance du RAG hybride et le déterminisme du Kernel. 
- Cependant, tu dois t'assurer que ce module est correctement lié à l'environnement Python. Vérifie que `maturin` ou `setuptools-rust` est bien configuré dans le `pyproject.toml` et le `Makefile` (ex: `make build-rust`) pour que ce module se compile de manière transparente lors d'un `pip install -e .`. Si ce n'est pas le cas, corrige la configuration de build maintenant.

3. **Validation de l'Epic 1.1 (Le Bug RAG) :**
- Confirme-moi par écrit que tu as bien rendu la dataclass `Chunk` immuable et hachable (`frozen=True`, `frozenset` au lieu de `set`) et que le `HybridBackend` utilise bien `chunk_id` comme clé de dictionnaire pour éviter les crashs.
- Lance la suite de tests complète (`make test` ou `pytest tests/`) pour prouver que tes modifications et suppressions n'ont rien cassé.

Fais ces suppressions et vérifications maintenant. L'objectif est d'avoir un arbre de fichiers 100% propre et un build vert. Fournis-moi le résumé de tes actions une fois terminé.