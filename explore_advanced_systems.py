"""Exploration des systèmes avancés NEXUS via Meta GraphRAG."""

from tools.meta_graph_rag import load_config, MetaGraphIndexer
import os

# Charger l'index existant (override via env vars)
allow_hash = os.getenv("META_RAG_ALLOW_HASH", "false").lower() == "true"
embedding_env = os.getenv("META_RAG_EMBEDDINGS")
if allow_hash:
    os.environ.setdefault("META_RAG_EMBEDDINGS", embedding_env or "hash")
else:
    if embedding_env and embedding_env.lower() == "hash":
        print("[WARN] META_RAG_EMBEDDINGS=hash ignored (set META_RAG_ALLOW_HASH=1 to allow).")
        os.environ["META_RAG_EMBEDDINGS"] = "gemini"
    else:
        os.environ.setdefault("META_RAG_EMBEDDINGS", "gemini")

config = load_config()
indexer = MetaGraphIndexer(config)

print("=" * 80)
print("META GRAPHRAG - Exploration des Systèmes Avancés NEXUS")
print("=" * 80)

# Requêtes spécifiques pour chaque système
queries = {
    "HIVE_MIND": [
        "hive mind orchestrator adaptive debate",
        "context scope manager hive mind",
        "session integration cost estimator",
        "swarm bridge negotiation protocol",
        "json parser agent registry",
    ],
    "SWARM": [
        "swarm hybrid engine collaboration mode",
        "agent pool task analyzer",
        "task completion validator merge strategy",
        "adaptive fallback mode executor",
        "session manager agent metrics",
    ],
    "EVOLUTION": [
        "evolution manager lineage evaluator",
        "mutation parser tiered validator",
        "evolution service phase brainstorm",
        "promote create validation",
        "rate limiter evolution",
    ],
    "SPAWN": [
        "spawn agent creation service",
        "pilot multi ai executor story generator",
        "crew manager ncm orchestrator",
        "prompt refresh token monitor",
        "snapshot story shard",
    ],
    "SYNAPSE_PROTOCOL": [
        "synapse protocol memory manager",
        "blackboard async coordination",
        "event bus types telemetry bridge",
        "cancellation token safe task",
    ],
    "RESILIENCE": [
        "circuit breaker system health",
        "hibernation manager panic system",
        "stagnation detector predictor",
        "plan health health state machine",
    ],
}

all_results = {}

for system, system_queries in queries.items():
    print(f"\n{'='*80}")
    print(f"🎯 SYSTÈME: {system}")
    print(f"{'='*80}")
    
    # Requêtes parallèles
    all_chunks = []
    for query in system_queries:
        result = indexer.query(query)
        all_chunks.extend(result.seed_chunks)
        all_chunks.extend(result.expanded_chunks)
    
    # Regrouper par fichier avec scores
    file_scores = {}
    for chunk in all_chunks:
        file_path = chunk.path
        if file_path not in file_scores:
            file_scores[file_path] = {"chunks": [], "score": 0}
        file_scores[file_path]["chunks"].append(chunk)
        file_scores[file_path]["score"] += 1
    
    # Trier par score
    sorted_files = sorted(file_scores.items(), key=lambda x: -x[1]["score"])
    
    print(f"\n📁 Fichiers clés ({len(sorted_files)} fichiers):")
    for file_path, data in sorted_files[:8]:
        print(f"\n  📄 {file_path} (score: {data['score']})")
        for chunk in data["chunks"][:2]:
            kind_label = chunk.kind if hasattr(chunk, 'kind') else "unknown"
            print(f"     • [{kind_label}] {chunk.path}:{chunk.start_line}")
            excerpt = chunk.text[:120].replace('\n', ' ').replace('  ', ' ')
            print(f"       \"{excerpt}...\"")
    
    all_results[system] = sorted_files[:8]

# Identifier les patterns architecturaux
print(f"\n{'='*80}")
print("🔍 PATRONS ARCHITECTURAUX DÉTECTÉS")
print(f"{'='*80}")

# Patterns dans les chunks
patterns_detected = {
    "Singleton": [],
    "Factory": [],
    "Observer": [],
    "Strategy": [],
    "State Machine": [],
    "Pool": [],
    "Registry": [],
}

for system, files in all_results.items():
    for file_path, data in files:
        chunks = data["chunks"]
        for chunk in chunks:
            text_lower = chunk.text.lower()
            if "singleton" in text_lower or "single instance" in text_lower:
                patterns_detected["Singleton"].append(file_path)
            if "factory" in text_lower:
                patterns_detected["Factory"].append(file_path)
            if "observer" in text_lower or "subscribe" in text_lower or "pub/sub" in text_lower:
                patterns_detected["Observer"].append(file_path)
            if "strategy" in text_lower or "mode" in text_lower or "merge" in text_lower:
                patterns_detected["Strategy"].append(file_path)
            if "state" in text_lower or "fsm" in text_lower or "transition" in text_lower:
                patterns_detected["State Machine"].append(file_path)
            if "pool" in text_lower or "registry" in text_lower:
                patterns_detected["Pool"].append(file_path)
            if "registry" in text_lower:
                patterns_detected["Registry"].append(file_path)

print("\nPatterns par système:")
for pattern, files in patterns_detected.items():
    unique_files = list(set(files))
    if unique_files:
        print(f"\n  {pattern}:")
        for f in unique_files[:3]:
            print(f"    • {f}")

# Sauvegarder les résultats
import json
output_path = config.data_path / "advanced_systems_exploration.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps({
    "systems": {k: [(fp, d["score"]) for fp, d in v] for k, v in all_results.items()},
    "patterns": {p: list(set(f)) for p, f in patterns_detected.items()}
}, indent=2, ensure_ascii=True))

print(f"\n💾 Exploration sauvegardée: {output_path}")
