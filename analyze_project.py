"""Script d'indexation optimisé et analyse du projet avec Meta GraphRAG."""

from tools.meta_graph_rag import load_config, MetaGraphIndexer
from tools.meta_graph_rag.reports import generate_reports
import os
import json

# Configuration optimisee pour une indexation rapide (override via env vars)
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
os.environ.setdefault('META_RAG_INCLUDE', 'core/api,core/agents,core/memory,core/execution')
os.environ.setdefault('META_RAG_EXCLUDE', '__pycache__,.git,.nexus,.venv,venv,logs,archive,workspace,test_workspace')
os.environ.setdefault('META_RAG_CHUNK_LINES', '30')
os.environ.setdefault('META_RAG_QUERY_SEEDS', '5')
os.environ.setdefault('META_RAG_QUERY_DEPTH', '1')
os.environ.setdefault('META_RAG_QUERY_EXPANSION', '10')
os.environ.setdefault('META_RAG_PERSIST_EVERY', '10')

print('=' * 60)
print('META GRAPHRAG - Analyse du Projet NEXUS')
print('=' * 60)

config = load_config()
print(f'\n[CONFIG] Root: {config.root_path}')
print(f'[CONFIG] Data: {config.data_path}')
print(f'[CONFIG] Include: {config.include_dirs}')
print(f'[CONFIG] Exclude: {config.exclude_dirs}')

indexer = MetaGraphIndexer(config)
print('\n[INDEX] Indexation en cours...')
indexer.index(full=True)
status = indexer.status()

print(f'\n[STATUS] Index cree:')
print(f'  - Nodes: {status["nodes"]}')
print(f'  - Edges: {status["edges"]}')
print(f'  - Chunks: {status["chunks"]}')
print(f'  - Vector entries: {status["vector_entries"]}')
print(f'  - Backend: {status["embedding_backend"]["backend"]}')

# Requêtes analytiques pour comprendre l'architecture
print('\n' + '=' * 60)
print('ANALYSE DE L ARCHITECTURE')
print('=' * 60)

queries = [
    "agent orchestration system architecture",
    "memory embedding vector store",
    "tool execution function call",
    "api routes fastapi endpoints",
    "session workspace isolation",
    "security authentication permissions",
]

for query in queries:
    print(f'\n[QUERY] "{query}"')
    result = indexer.query(query)
    print(f'  Seed chunks: {len(result.seed_chunks)}')
    print(f'  Expanded chunks: {len(result.expanded_chunks)}')
    
    # Afficher les premiers résultats
    for i, chunk in enumerate(result.seed_chunks[:3]):
        print(f'    {i+1}. [{chunk.kind}] {chunk.path}:{chunk.start_line}-{chunk.end_line}')
        excerpt = chunk.text[:150].replace('\n', ' ')
        print(f'       "{excerpt}..."')

# Générer un rapport d'overview
print('\n' + '=' * 60)
print('GENERATION DES RAPPORTS')
print('=' * 60)

paths = generate_reports(
    graph=indexer.graph,
    chunks_count=status["chunks"],
    vector_count=status["vector_entries"],
    output_dir=config.reports_path,
)

print(f'\n[RAPPORTS] Generes:')
print(f'  - Overview: {paths.overview}')
print(f'  - Top-down: {paths.top_down}')
print(f'  - Bottom-up: {paths.bottom_up}')
print(f'  - Security: {paths.security}')
print(f'  - Module catalog: {paths.module_catalog}')

# Lire et afficher l'overview
if paths.overview.exists():
    print('\n' + '=' * 60)
    print('OVERVIEW DU PROJET')
    print('=' * 60)
    overview = paths.overview.read_text(encoding='utf-8', errors='ignore')
    print(overview[:3000])

print('\n' + '=' * 60)
print('ANALYSE TERMINEE')
print('=' * 60)
