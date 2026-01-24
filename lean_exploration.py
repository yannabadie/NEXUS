"""Utilisation du Meta GraphRAG pour comprendre l'architecture NEXUS et préparer Lean."""

from tools.meta_graph_rag import load_config, MetaGraphIndexer
import os

# Charger l'index existant (override via env vars)
os.environ.setdefault('META_RAG_EMBEDDINGS', 'gemini')

config = load_config()
indexer = MetaGraphIndexer(config)

print("=" * 80)
print("META GRAPHRAG - Exploration Architecturale de NEXUS")
print("=" * 80)

# Requêtes ciblées pour identifier les composants clés
queries = {
    "orchestration_core": [
        "orchestrator state machine execution flow",
        "fsm states transitions handlers",
        "orchestration_v7 main loop",
        "context building propagation",
    ],
    "agent_system": [
        "agent registry spawn creation",
        "unified agent descriptor capability",
        "agent service pool statistics",
    ],
    "memory_system": [
        "memory coordinator namespace manager",
        "embedding engine singleton",
        "rag namespace storage",
        "success memory task quality",
    ],
    "execution_system": [
        "tool executor handlers registry",
        "bash file git web handlers",
        "tool manager dynamic tools",
        "mcp protocol server client",
    ],
    "api_system": [
        "fastapi app routes middleware",
        "authentication jwt token",
        "rbac permission role",
        "rate limiting concurrency",
    ],
    "communication": [
        "event bus redis pubsub",
        "websocket streaming stream",
        "interaction human in loop",
        "session workspace isolation",
    ],
    "resilience": [
        "circuit breaker health",
        "hibernation panic stagnation",
        "error handling recovery",
    ],
}

results = {}

for domain, domain_queries in queries.items():
    print(f"\n{'='*80}")
    print(f"DOMAIN: {domain.upper()}")
    print(f"{'='*80}")
    
    all_chunks = []
    for query in domain_queries:
        result = indexer.query(query)
        all_chunks.extend(result.seed_chunks)
    
    # Regrouper par fichier
    by_file = {}
    for chunk in all_chunks:
        file_path = chunk.path
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(chunk)
    
    results[domain] = by_file
    
    print(f"\nFichiers clés identifiés ({len(by_file)} fichiers):")
    for file_path, chunks in sorted(by_file.items(), key=lambda x: -len(x[1]))[:8]:
        print(f"\n  📄 {file_path}")
        for chunk in chunks[:3]:
            print(f"     - [{chunk.kind}] {chunk.path}:{chunk.start_line}")
            print(f"       {chunk.text[:100].replace(chr(10), ' ')}...")

# Identifier les fichiers absoluments nécessaires
print(f"\n{'='*80}")
print("FICHIERS PRIORITAIRES POUR FORMALISATION LEAN")
print(f"{'='*80}")

priority_files = set()
for domain, files in results.items():
    for file_path in files.keys():
        # Privilégier les fichiers avec beaucoup de chunks
        if len(files[file_path]) >= 2:
            priority_files.add(file_path)

print(f"\nTotal fichiers prioritaires: {len(priority_files)}")
for fp in sorted(priority_files):
    print(f"  📄 {fp}")

# Sauvegarder la liste pour plus tard
import json
output = {
    "results_by_domain": {k: {fp: len(v) for fp, v in files.items()} for k, files in results.items()},
    "priority_files": list(priority_files)
}

output_path = config.data_path / "lean_exploration.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(output, indent=2, ensure_ascii=True))
print(f"\n💾 Exploration sauvegardée: {output_path}")
