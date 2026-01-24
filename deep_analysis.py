"""Analyse approfondie du projet NEXUS basée sur Meta GraphRAG."""

from tools.meta_graph_rag import load_config, MetaGraphIndexer
from tools.meta_graph_rag.graph import GraphStore
from pathlib import Path
import json
import os

# Charger l'index existant (override via env vars)
os.environ.setdefault('META_RAG_EMBEDDINGS', 'gemini')
os.environ.setdefault('META_RAG_INCLUDE', 'core,tools,interface,prompts')

config = load_config()
indexer = MetaGraphIndexer(config)

# Analyser la structure du graphe
print("=" * 70)
print("ANALYSE APPROFONDIE DU PROJET NEXUS - META GRAPHRAG")
print("=" * 70)

# Statistiques des types de nodes
node_types = {}
edge_types = {}
for node in indexer.graph.nodes.values():
    node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
for edge in indexer.graph.edges:
    edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1

print("\n📊 STATISTIQUES DU GRAPHE:")
print(f"   Total Nodes: {len(indexer.graph.nodes)}")
print(f"   Total Edges: {len(indexer.graph.edges)}")
print(f"   Total Chunks: {len(indexer.chunks.chunks)}")
print(f"   Vector Entries: {len(indexer.vector_index.entries)}")

print("\n📈 DISTRIBUTION DES TYPES DE NODES:")
for node_type, count in sorted(node_types.items(), key=lambda x: -x[1]):
    print(f"   {node_type}: {count}")

print("\n🔗 DISTRIBUTION DES TYPES D'EDGES:")
for edge_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
    print(f"   {edge_type}: {count}")

# Analyser les relations entre modules
print("\n" + "=" * 70)
print("ANALYSE DES DÉPENDANCES ET RELATIONS")
print("=" * 70)

# Trouver les fichiers les plus connectés
node_connections = {}
for edge in indexer.graph.edges:
    node_connections[edge.source] = node_connections.get(edge.source, 0) + 1
    node_connections[edge.target] = node_connections.get(edge.target, 0) + 1

top_connected = sorted(node_connections.items(), key=lambda x: -x[1])[:15]
print("\n🔗 NODES LES PLUS CONNECTÉS (hubs):")
for node_id, degree in top_connected:
    node = indexer.graph.nodes.get(node_id)
    if node:
        print(f"   {node.name} ({node.node_type}): {degree} connexions")

# Analyser les patterns d'appel de fonctions
print("\n" + "=" * 70)
print("PATRONS D'APPELS DE FONCTIONS (calls)")
print("=" * 70)

call_edges = [e for e in indexer.graph.edges if e.edge_type == 'calls']
print(f"   Total d'appels détectés: {len(call_edges)}")

# Grouper par fichier source
calls_by_file = {}
for edge in call_edges:
    source_node = indexer.graph.nodes.get(edge.source)
    if source_node and source_node.node_type == 'python_function':
        file_path = source_node.path
        calls_by_file[file_path] = calls_by_file.get(file_path, 0) + 1

top_callers = sorted(calls_by_file.items(), key=lambda x: -x[1])[:10]
print("\n📞 FONCTIONS LES PLUS ACTIVES (qui appellent d'autres fonctions):")
for file_path, count in top_callers:
    print(f"   {file_path}: {count} appels sortants")

# Analyser les imports
print("\n" + "=" * 70)
print("ANALYSE DES IMPORTS")
print("=" * 70)

import_edges = [e for e in indexer.graph.edges if e.edge_type == 'imports']
print(f"   Total d'imports détectés: {len(import_edges)}")

# Modules externes les plus importés
external_modules = {}
for edge in import_edges:
    target_node = indexer.graph.nodes.get(edge.target)
    if target_node and target_node.node_type == 'module':
        module_name = target_node.name
        if not module_name.startswith('.'):
            external_modules[module_name] = external_modules.get(module_name, 0) + 1

top_imports = sorted(external_modules.items(), key=lambda x: -x[1])[:15]
print("\n📦 MODULES EXTERNES LES PLUS IMPORTÉS:")
for module, count in top_imports:
    print(f"   {module}: {count}")

# Analyse de la sécurité
print("\n" + "=" * 70)
print("ANALYSE DE SÉCURITÉ - HOTSPOTS DÉTECTÉS")
print("=" * 70)

security_chunks = {}
for chunk in indexer.chunks.chunks.values():
    tags = chunk.metadata.get('security_tags', '')
    if tags:
        for tag in tags.split(','):
            tag = tag.strip()
            if tag:
                security_chunks[tag] = security_chunks.get(tag, 0) + 1

print("\n🔒 PATTERNS DE SÉCURITÉ DÉTECTÉS:")
for tag, count in sorted(security_chunks.items(), key=lambda x: -x[1]):
    print(f"   {tag}: {count} occurrences")

# Analyser les classes principales
print("\n" + "=" * 70)
print("CATALOGUE DES CLASSES PRINCIPALES")
print("=" * 70)

classes_by_file = {}
for node in indexer.graph.nodes.values():
    if node.node_type == 'python_class':
        file_path = node.path
        classes_by_file.setdefault(file_path, []).append(node.name)

print("\n🏗️ CLASSES PAR FICHIER:")
for file_path, classes in sorted(classes_by_file.items(), key=lambda x: -len(x[1]), reverse=True)[:10]:
    print(f"\n   {file_path}:")
    for cls in classes[:5]:
        print(f"      - {cls}")
    if len(classes) > 5:
        print(f"      ... et {len(classes) - 5} autres")

# Analyser les fonctions clés par domaine
print("\n" + "=" * 70)
print("FONCTIONS CLÉS PAR DOMAINE")
print("=" * 70)

# API Routes
api_functions = []
# Memory functions
memory_functions = []
# Execution functions
execution_functions = []

for node in indexer.graph.nodes.values():
    if node.node_type == 'python_function':
        if 'route' in node.path or node.path.startswith('core/api/'):
            api_functions.append(f"{node.name} ({node.path})")
        elif 'memory' in node.path:
            memory_functions.append(f"{node.name} ({node.path})")
        elif 'execution' in node.path or 'handler' in node.path:
            execution_functions.append(f"{node.name} ({node.path})")

print("\n🌐 FONCTIONS API:")
for func in api_functions[:10]:
    print(f"   {func}")

print("\n💾 FONCTIONS MEMORY:")
for func in memory_functions[:10]:
    print(f"   {func}")

print("\n⚙️ FONCTIONS EXECUTION/HANDLERS:")
for func in execution_functions[:10]:
    print(f"   {func}")

# Générer une vue d'ensemble textuelle
print("\n" + "=" * 70)
print("VUE D'ENSEMBLE ARCHITECTURALE")
print("=" * 70)

# Compter les modules par domaine
domains = {
    'api': 0,
    'memory': 0,
    'execution': 0,
    'agents': 0,
    'hive_mind': 0,
    'swarm': 0,
    'orchestration': 0,
    'security': 0,
    'session': 0,
    'telemetry': 0,
}

for path in indexer.graph.nodes.keys():
    for domain in domains.keys():
        if domain in path.lower():
            domains[domain] += 1

print("\n🏛️ DISTRIBUTION PAR DOMAINE:")
for domain, count in sorted(domains.items(), key=lambda x: -x[1]):
    if count > 0:
        bar = '█' * (count // 20)
        print(f"   {domain:15} {bar} {count}")

# Sauvegarder l'analyse
analysis_output = {
    'stats': {
        'nodes': len(indexer.graph.nodes),
        'edges': len(indexer.graph.edges),
        'chunks': len(indexer.chunks.chunks),
        'vector_entries': len(indexer.vector_index.entries),
    },
    'node_types': node_types,
    'edge_types': edge_types,
    'security_hotspots': security_chunks,
    'top_modules': top_imports,
    'domains': {k: v for k, v in domains.items() if v > 0}
}

output_path = config.data_path / 'analysis_output.json'
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(analysis_output, indent=2, ensure_ascii=True))
print(f"\n💾 Analyse sauvegardée dans: {output_path}")

print("\n" + "=" * 70)
print("ANALYSE TERMINÉE")
print("=" * 70)
