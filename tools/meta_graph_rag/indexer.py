"""Indexing pipeline for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import ast
import hashlib
import json
import os
import re

from .config import MetaGraphRagConfig
from .embeddings import (
    EmbeddingBackend,
    GeminiEmbeddingBackend,
    HashEmbeddingBackend,
    NoopEmbeddingBackend,
    SentenceTransformerBackend,
    VectorIndex,
    VectorRecord,
)
from .graph import GraphEdge, GraphNode, GraphStore
from .graph_db import GraphDatabase
from .http_client import HttpConfig


SECURITY_PATTERNS = {
    "exec_eval": ["exec(", "eval("],
    "subprocess_shell": ["shell=True", "os.system(", "subprocess.Popen(", "subprocess.run("],
    "pickle": ["pickle.load", "pickle.loads"],
    "yaml_load": ["yaml.load("],
    "sql_raw": ["execute(", "cursor.execute(", "text("],
}


@dataclass
class Chunk:
    chunk_id: str
    node_id: str
    path: str
    start_line: int
    end_line: int
    kind: str
    text: str
    content_hash: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class IndexManifest:
    files: Dict[str, Dict[str, object]] = field(default_factory=dict)
    sources: Dict[str, Dict[str, object]] = field(default_factory=dict)
    generated_at: str = ""

    @classmethod
    def load(cls, path: Path) -> "IndexManifest":
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            files=payload.get("files", {}),
            sources=payload.get("sources", {}),
            generated_at=payload.get("generated_at", ""),
        )

    def save(self, path: Path) -> None:
        self.generated_at = datetime.now(timezone.utc).isoformat()
        payload = asdict(self)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


class ChunkStore:
    """JSONL-backed chunk store."""

    def __init__(self) -> None:
        self.chunks: Dict[str, Chunk] = {}
        self.node_to_chunks: Dict[str, List[str]] = {}

    def add(self, chunk: Chunk) -> None:
        self.chunks[chunk.chunk_id] = chunk
        self.node_to_chunks.setdefault(chunk.node_id, []).append(chunk.chunk_id)

    def remove(self, chunk_ids: List[str]) -> None:
        for chunk_id in chunk_ids:
            chunk = self.chunks.pop(chunk_id, None)
            if not chunk:
                continue
            if chunk.node_id in self.node_to_chunks:
                self.node_to_chunks[chunk.node_id] = [
                    cid for cid in self.node_to_chunks[chunk.node_id]
                    if cid != chunk_id
                ]

    def get_by_node(self, node_id: str) -> List[Chunk]:
        return [self.chunks[cid] for cid in self.node_to_chunks.get(node_id, [])]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(asdict(chunk), ensure_ascii=True) for chunk in self.chunks.values()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ChunkStore":
        store = cls()
        if not path.exists():
            return store
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            chunk = Chunk(**payload)
            store.add(chunk)
        return store


@dataclass
class GraphRagResult:
    query: str
    seed_chunks: List[Chunk]
    expanded_chunks: List[Chunk]


class MetaGraphIndexer:
    """Builds and queries a meta GraphRAG index."""

    def __init__(self, config: MetaGraphRagConfig) -> None:
        self.config = config
        self.graph_db = GraphDatabase(config.graph_db_path, backend=config.graph_backend)
        self.graph = GraphStore.load(config.graph_path)
        db_status = self.graph_db.status()
        if not self.graph.nodes and db_status["nodes"]:
            self.graph = self.graph_db.load_graph()
            self.graph.save(config.graph_path)
        elif self.graph.nodes and not db_status["nodes"]:
            self.graph_db.upsert_nodes(self.graph.nodes.values())
            self.graph_db.upsert_edges(self.graph.edges)
        self.chunks = ChunkStore.load(config.chunks_path)
        self.manifest = IndexManifest.load(config.manifest_path)
        self.embedding_backend = self._select_backend()
        self.vector_index = VectorIndex.load(
            config.vector_path,
            self.embedding_backend,
            document_task_type=config.gemini_task_type_document,
            query_task_type=config.gemini_task_type_query,
            source_weights=config.source_weights,
        )

    def _select_backend(self) -> EmbeddingBackend:
        backend = self.config.embedding_backend
        if backend == "gemini":
            if not self.config.gemini_api_key:
                raise RuntimeError("META_RAG_EMBEDDINGS=gemini requires GEMINI_API_KEY or GOOGLE_API_KEY")
            http_config = HttpConfig(
                ssl_mode=self.config.ssl_mode,
                ca_bundle_path=self.config.ca_bundle_path,
            )
            return GeminiEmbeddingBackend(
                api_key=self.config.gemini_api_key,
                model_name=self.config.gemini_embedding_model,
                batch_size=self.config.gemini_batch_size,
                output_dimensionality=self.config.gemini_embedding_dim,
                default_task_type=self.config.gemini_task_type_document,
                http_config=http_config,
            )
        if backend == "sentence" or backend == "sentence-transformers":
            return SentenceTransformerBackend(self.config.embedding_model)
        if backend == "hash":
            return HashEmbeddingBackend()
        if backend in {"none", "noop"}:
            return NoopEmbeddingBackend()
        # auto
        try:
            return SentenceTransformerBackend(self.config.embedding_model)
        except Exception:
            if self.config.gemini_api_key:
                http_config = HttpConfig(
                    ssl_mode=self.config.ssl_mode,
                    ca_bundle_path=self.config.ca_bundle_path,
                )
                return GeminiEmbeddingBackend(
                    api_key=self.config.gemini_api_key,
                    model_name=self.config.gemini_embedding_model,
                    batch_size=self.config.gemini_batch_size,
                    output_dimensionality=self.config.gemini_embedding_dim,
                    default_task_type=self.config.gemini_task_type_document,
                    http_config=http_config,
                )
            return HashEmbeddingBackend()

    def index(self, full: bool = False) -> None:
        """Index codebase and external sources into graph + vector store."""
        if full:
            self.graph_db.reset()
        progress_path = self.config.data_path / "index_progress.json"
        files = list(self._scan_files())
        known_files = set(self.manifest.files.keys())
        current_files = set(str(path) for path in files)

        removed_files = known_files - current_files
        for removed in removed_files:
            entry = self.manifest.files.pop(removed, None)
            if not entry:
                continue
            self._remove_entry(entry)

        indexed_files = 0
        for path in files:
            entry_key = str(path)
            _write_progress(progress_path, "indexing", entry_key)
            content_hash = _hash_file(path)
            entry = self.manifest.files.get(entry_key)
            if entry and entry.get("hash") == content_hash and not full:
                continue
            if entry:
                self._remove_entry(entry)
            nodes, edges, chunks = self._index_file(path, content_hash)
            node_ids = sorted({node.node_id for node in nodes})
            chunk_ids = sorted({chunk.chunk_id for chunk in chunks})
            for node in nodes:
                self.graph.add_node(node)
            for edge in edges:
                self.graph.add_edge(edge)
            for chunk in chunks:
                self.chunks.add(chunk)
            self.graph_db.upsert_nodes(nodes)
            self.graph_db.upsert_edges(edges)
            self._add_vectors(chunks)
            self.manifest.files[entry_key] = {
                "hash": content_hash,
                "nodes": node_ids,
                "chunks": chunk_ids,
            }
            indexed_files += 1
            _write_progress(progress_path, "indexed", entry_key)
            if self.config.persist_every_files > 0 and indexed_files % self.config.persist_every_files == 0:
                self._persist()

        self._index_external_sources(full=full)
        self._persist()

    def query(self, query_text: str) -> GraphRagResult:
        seed_records = self.vector_index.query(query_text, limit=self.config.query_seed_limit)
        seed_chunks = [self.chunks.chunks[record.chunk_id] for record in seed_records if record.chunk_id in self.chunks.chunks]
        expanded_chunks = self._expand_chunks(seed_chunks)
        return GraphRagResult(
            query=query_text,
            seed_chunks=seed_chunks,
            expanded_chunks=expanded_chunks,
        )

    def status(self) -> Dict[str, object]:
        db_status = self.graph_db.status()
        return {
            "nodes": len(self.graph.nodes),
            "edges": len(self.graph.edges),
            "chunks": len(self.chunks.chunks),
            "vector_entries": len(self.vector_index.entries),
            "embedding_backend": self.embedding_backend.info(),
            "graph_db": db_status,
        }

    def _persist(self) -> None:
        self.graph.save(self.config.graph_path)
        self.chunks.save(self.config.chunks_path)
        self.vector_index.save(self.config.vector_path)
        self.manifest.save(self.config.manifest_path)

    def _scan_files(self) -> Iterable[Path]:
        max_bytes = self.config.max_file_size_kb * 1024
        extensions = set(ext.lower() for ext in self.config.extensions)
        include_dirs = [self.config.root_path / name for name in self.config.include_dirs]
        exclude = set(self.config.exclude_dirs)

        # Include root files
        for file_path in self.config.root_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                if file_path.stat().st_size <= max_bytes:
                    yield file_path

        for base in include_dirs:
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in exclude]
                for name in files:
                    path = Path(root) / name
                    if path.suffix.lower() not in extensions:
                        continue
                    if path.stat().st_size > max_bytes:
                        continue
                    yield path

    def _index_file(self, path: Path, content_hash: str) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
        relative_path = _relative_path(path, self.config.root_path)
        source_type = _source_type_for_path(relative_path, path.suffix.lower())
        language = _language_for_extension(path.suffix.lower())
        file_node_id = f"file:{relative_path}"
        file_node = GraphNode(
            node_id=file_node_id,
            node_type="file",
            name=path.name,
            path=relative_path,
            start_line=1,
            end_line=_count_lines(path),
            content_hash=content_hash,
            metadata={
                "extension": path.suffix.lower(),
                "source_type": source_type,
                "language": language,
            },
        )
        nodes = [file_node]
        edges: List[GraphEdge] = []
        chunks: List[Chunk] = []

        content = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".py":
            py_nodes, py_edges, py_chunks = _chunk_python(content, relative_path, file_node_id, source_type)
            nodes.extend(py_nodes)
            edges.extend(py_edges)
            chunks.extend(py_chunks)
        elif path.suffix.lower() == ".md":
            md_nodes, md_edges, md_chunks = _chunk_markdown(content, relative_path, file_node_id, source_type)
            nodes.extend(md_nodes)
            edges.extend(md_edges)
            chunks.extend(md_chunks)
        else:
            generic_nodes, generic_edges, generic_chunks = _chunk_generic(
                content,
                relative_path,
                file_node_id,
                source_type,
                self.config.chunk_lines,
                self.config.chunk_overlap,
            )
            nodes.extend(generic_nodes)
            edges.extend(generic_edges)
            chunks.extend(generic_chunks)

        nodes = _dedupe_nodes(nodes)
        edges = _dedupe_edges(edges)
        return nodes, edges, chunks

    def _add_vectors(self, chunks: List[Chunk]) -> None:
        if self.config.skip_embeddings:
            return
        records: List[VectorRecord] = []
        for chunk in chunks:
            source_type = chunk.metadata.get("source_type", "")
            records.append(VectorRecord(
                chunk_id=chunk.chunk_id,
                embedding=[],
                metadata={
                    "text": chunk.text,
                    "path": chunk.path,
                    "node_id": chunk.node_id,
                    "kind": chunk.kind,
                    "source_type": source_type,
                },
            ))
        if records:
            self.vector_index.add_texts(records)

    def embed_missing(self, limit: int | None = None) -> int:
        """Embed missing chunks into the vector index."""
        records: List[VectorRecord] = []
        embedded = 0
        for chunk in self.chunks.chunks.values():
            if chunk.chunk_id in self.vector_index.entries:
                continue
            records.append(VectorRecord(
                chunk_id=chunk.chunk_id,
                embedding=[],
                metadata={
                    "text": chunk.text,
                    "path": chunk.path,
                    "node_id": chunk.node_id,
                    "kind": chunk.kind,
                    "source_type": chunk.metadata.get("source_type", ""),
                },
            ))
            if limit and (embedded + len(records)) >= limit:
                remaining = limit - embedded
                if remaining > 0:
                    self.vector_index.add_texts(records[:remaining])
                    embedded += remaining
                records = []
                break
            if len(records) >= self.config.embed_batch_limit:
                self.vector_index.add_texts(records)
                embedded += len(records)
                records = []

        if records:
            self.vector_index.add_texts(records)
            embedded += len(records)

        if embedded:
            self.vector_index.save(self.config.vector_path)
        return embedded

    def _remove_entry(self, entry: Dict[str, object]) -> None:
        node_ids = entry.get("nodes", [])
        chunk_ids = entry.get("chunks", [])
        if node_ids:
            self.graph.remove_nodes(node_ids)
            self.graph_db.remove_nodes(node_ids)
        if chunk_ids:
            self.chunks.remove(chunk_ids)
            self.vector_index.remove(chunk_ids)

    def _expand_chunks(self, seed_chunks: List[Chunk]) -> List[Chunk]:
        adjacency = self.graph.build_adjacency()
        expanded_nodes: List[str] = []
        for chunk in seed_chunks:
            expanded_nodes.extend(_expand_nodes(adjacency, chunk.node_id, self.config.query_expansion_depth))
        expanded_nodes = list(dict.fromkeys(expanded_nodes))
        expanded_chunks: List[Chunk] = []
        for node_id in expanded_nodes:
            expanded_chunks.extend(self.chunks.get_by_node(node_id))
        return expanded_chunks[: self.config.query_expansion_limit]

    def _index_external_sources(self, full: bool = False) -> None:
        sources_file = self.config.sources_path / "sources.json"
        if not sources_file.exists():
            return
        payload = json.loads(sources_file.read_text(encoding="utf-8"))
        for source in payload.get("sources", []):
            source_id = source.get("id")
            if not source_id:
                continue
            content_hash = source.get("hash")
            manifest_entry = self.manifest.sources.get(source_id)
            if manifest_entry and manifest_entry.get("hash") == content_hash and not full:
                continue
            if manifest_entry:
                self._remove_entry(manifest_entry)
            text_path = self.config.sources_path / source.get("text_path", "")
            if not text_path.exists():
                continue
            content = text_path.read_text(encoding="utf-8", errors="ignore")
            nodes, edges, chunks = _chunk_external_source(
                content,
                source,
            )
            node_ids = sorted({node.node_id for node in nodes})
            chunk_ids = sorted({chunk.chunk_id for chunk in chunks})
            for node in nodes:
                self.graph.add_node(node)
            for edge in edges:
                self.graph.add_edge(edge)
            for chunk in chunks:
                self.chunks.add(chunk)
            self.graph_db.upsert_nodes(nodes)
            self.graph_db.upsert_edges(edges)
            self._add_vectors(chunks)
            self.manifest.sources[source_id] = {
                "hash": content_hash,
                "nodes": node_ids,
                "chunks": chunk_ids,
            }


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except Exception:
        return 0


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _sanitize_text(text: str) -> str:
    return text.encode("ascii", "ignore").decode("ascii")


def _scan_security_tags(text: str) -> List[str]:
    lowered = text.lower()
    tags = []
    for tag, patterns in SECURITY_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            tags.append(tag)
    return tags


def _write_progress(path: Path, stage: str, file_path: str) -> None:
    payload = {
        "stage": stage,
        "file": file_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _source_type_for_path(relative_path: str, suffix: str) -> str:
    lowered = relative_path.lower()
    if lowered.startswith("tests/") or "/tests/" in lowered:
        return "test"
    if lowered.startswith("docs/") or "/docs/" in lowered:
        return "doc"
    if lowered.startswith("prompts/") or "/prompts/" in lowered:
        return "prompt"
    if lowered.startswith("audit/") or "/audit/" in lowered:
        return "audit"
    if lowered.startswith("products/") or "/products/" in lowered:
        return "product"
    if suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
        return "code"
    if suffix in {".md", ".txt"}:
        return "doc"
    if suffix in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini"}:
        return "config"
    return "data"


def _language_for_extension(suffix: str) -> str:
    mapping = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".md": "markdown",
        ".ps1": "powershell",
        ".sh": "shell",
        ".bat": "batch",
        ".json": "json",
        ".jsonl": "jsonl",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
    }
    return mapping.get(suffix, "text")


_JS_IMPORT_RE = re.compile(r"^\s*import\s+(?:.+?\s+from\s+)?[\"']([^\"']+)[\"']", re.MULTILINE)
_JS_REQUIRE_RE = re.compile(r"\brequire\(\s*[\"']([^\"']+)[\"']\s*\)")


def _extract_js_imports(text: str) -> List[str]:
    modules = set(_JS_IMPORT_RE.findall(text))
    modules.update(_JS_REQUIRE_RE.findall(text))
    return sorted(modules)


def _is_relative_import(module: str) -> bool:
    return module.startswith(".") or module.startswith("/")


def _chunk_python(
    content: str,
    relative_path: str,
    file_node_id: str,
    source_type: str,
) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    chunks: List[Chunk] = []

    sanitized = _sanitize_text(content)
    lines = sanitized.splitlines()
    symbol_map: Dict[str, str] = {}

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return nodes, edges, chunks

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            start = getattr(node, "lineno", 1)
            end = getattr(node, "end_lineno", start)
            node_type = "python_class" if isinstance(node, ast.ClassDef) else "python_function"
            node_id = f"{node_type}:{relative_path}:{name}:{start}"
            symbol_map[name] = node_id
            node_text = "\n".join(lines[start - 1:end]).strip()
            if not node_text:
                continue
            tags = _scan_security_tags(node_text)
            graph_node = GraphNode(
                node_id=node_id,
                node_type=node_type,
                name=name,
                path=relative_path,
                start_line=start,
                end_line=end,
                content_hash=_hash_text(node_text),
                metadata={
                    "file": relative_path,
                    "security_tags": ",".join(tags),
                    "source_type": source_type,
                },
            )
            nodes.append(graph_node)
            edges.append(GraphEdge(source=file_node_id, target=node_id, edge_type="contains"))
            chunk_id = f"chunk:{node_id}"
            chunks.append(Chunk(
                chunk_id=chunk_id,
                node_id=node_id,
                path=relative_path,
                start_line=start,
                end_line=end,
                kind=node_type,
                text=node_text,
                content_hash=_hash_text(node_text),
                metadata={
                    "security_tags": ",".join(tags),
                    "source_type": source_type,
                },
            ))

    # Import edges (approximate)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                module_id = f"module:{relative_path}:{module}"
                nodes.append(GraphNode(
                    node_id=module_id,
                    node_type="module",
                    name=module,
                    path=module,
                    start_line=0,
                    end_line=0,
                    content_hash="",
                    metadata={
                        "origin": "import",
                        "source_type": source_type,
                        "module_name": module,
                    },
                ))
                edges.append(GraphEdge(source=file_node_id, target=module_id, edge_type="imports"))
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not module:
                continue
            module_id = f"module:{relative_path}:{module}"
            nodes.append(GraphNode(
                node_id=module_id,
                node_type="module",
                name=module,
                path=module,
                start_line=0,
                end_line=0,
                content_hash="",
                metadata={
                    "origin": "import",
                    "source_type": source_type,
                    "module_name": module,
                },
            ))
            edges.append(GraphEdge(source=file_node_id, target=module_id, edge_type="imports"))

    # Call edges (within file)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        caller_id = symbol_map.get(node.name)
        if not caller_id:
            continue
        for call in ast.walk(node):
            if isinstance(call, ast.Call):
                target_name = _call_name(call)
                if target_name and target_name in symbol_map:
                    edges.append(GraphEdge(
                        source=caller_id,
                        target=symbol_map[target_name],
                        edge_type="calls",
                    ))

    return nodes, edges, chunks


def _call_name(call: ast.Call) -> Optional[str]:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _chunk_markdown(
    content: str,
    relative_path: str,
    file_node_id: str,
    source_type: str,
) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    chunks: List[Chunk] = []

    sanitized = _sanitize_text(content)
    lines = sanitized.splitlines()

    section_start = 1
    section_title = "(intro)"
    for idx, line in enumerate(lines, start=1):
        if line.startswith("#"):
            if idx > section_start:
                nodes, edges, chunks = _emit_md_section(
                    relative_path,
                    file_node_id,
                    section_title,
                    section_start,
                    idx - 1,
                    lines,
                    source_type,
                    nodes,
                    edges,
                    chunks,
                )
            section_start = idx
            section_title = line.lstrip("#").strip() or "(section)"

    nodes, edges, chunks = _emit_md_section(
        relative_path,
        file_node_id,
        section_title,
        section_start,
        len(lines),
        lines,
        source_type,
        nodes,
        edges,
        chunks,
    )

    return nodes, edges, chunks


def _emit_md_section(
    relative_path: str,
    file_node_id: str,
    title: str,
    start: int,
    end: int,
    lines: List[str],
    source_type: str,
    nodes: List[GraphNode],
    edges: List[GraphEdge],
    chunks: List[Chunk],
) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
    section_text = "\n".join(lines[start - 1:end]).strip()
    if not section_text:
        return nodes, edges, chunks
    node_id = f"doc_section:{relative_path}:{title}:{start}"
    tags = _scan_security_tags(section_text)
    nodes.append(GraphNode(
        node_id=node_id,
        node_type="doc_section",
        name=title,
        path=relative_path,
        start_line=start,
        end_line=end,
        content_hash=_hash_text(section_text),
        metadata={
            "file": relative_path,
            "security_tags": ",".join(tags),
            "source_type": source_type,
        },
    ))
    edges.append(GraphEdge(source=file_node_id, target=node_id, edge_type="contains"))
    chunks.append(Chunk(
        chunk_id=f"chunk:{node_id}",
        node_id=node_id,
        path=relative_path,
        start_line=start,
        end_line=end,
        kind="doc_section",
        text=section_text,
        content_hash=_hash_text(section_text),
        metadata={
            "security_tags": ",".join(tags),
            "source_type": source_type,
        },
    ))
    return nodes, edges, chunks


def _chunk_generic(
    content: str,
    relative_path: str,
    file_node_id: str,
    source_type: str,
    chunk_lines: int,
    chunk_overlap: int,
) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    chunks: List[Chunk] = []

    sanitized = _sanitize_text(content)
    lines = sanitized.splitlines()
    ext = Path(relative_path).suffix.lower()
    if ext in {".js", ".jsx", ".ts", ".tsx"}:
        for module in _extract_js_imports(sanitized):
            module_type = "external" if not _is_relative_import(module) else "code"
            module_id = f"module:{relative_path}:{module}"
            nodes.append(GraphNode(
                node_id=module_id,
                node_type="module",
                name=module,
                path=module,
                start_line=0,
                end_line=0,
                content_hash="",
                metadata={
                    "origin": "import",
                    "source_type": module_type,
                    "module_name": module,
                },
            ))
            edges.append(GraphEdge(source=file_node_id, target=module_id, edge_type="imports"))
    total = len(lines)
    start = 1
    chunk_index = 1
    while start <= total:
        end = min(total, start + chunk_lines - 1)
        chunk_text = "\n".join(lines[start - 1:end]).strip()
        if chunk_text:
            node_id = f"file_chunk:{relative_path}:{chunk_index}"
            tags = _scan_security_tags(chunk_text)
            nodes.append(GraphNode(
                node_id=node_id,
                node_type="file_chunk",
                name=f"chunk_{chunk_index}",
                path=relative_path,
                start_line=start,
                end_line=end,
                content_hash=_hash_text(chunk_text),
                metadata={
                    "file": relative_path,
                    "security_tags": ",".join(tags),
                    "source_type": source_type,
                },
            ))
            edges.append(GraphEdge(source=file_node_id, target=node_id, edge_type="contains"))
            chunks.append(Chunk(
                chunk_id=f"chunk:{node_id}",
                node_id=node_id,
                path=relative_path,
                start_line=start,
                end_line=end,
                kind="file_chunk",
                text=chunk_text,
                content_hash=_hash_text(chunk_text),
                metadata={
                    "security_tags": ",".join(tags),
                    "source_type": source_type,
                },
            ))
        chunk_index += 1
        start = end - chunk_overlap + 1
        if start <= 0:
            start = end + 1

    return nodes, edges, chunks


def _chunk_external_source(content: str, source: Dict[str, object]) -> Tuple[List[GraphNode], List[GraphEdge], List[Chunk]]:
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    chunks: List[Chunk] = []

    sanitized = _sanitize_text(content)
    lines = sanitized.splitlines()
    title = str(source.get("title") or source.get("url") or "external")
    node_id = f"external_source:{source.get('id')}"
    tags = _scan_security_tags(sanitized)
    nodes.append(GraphNode(
        node_id=node_id,
        node_type="external_source",
        name=title,
        path=str(source.get("url", "")),
        start_line=1,
        end_line=len(lines),
        content_hash=_hash_text(sanitized),
        metadata={
            "source_id": str(source.get("id")),
            "security_tags": ",".join(tags),
            "source_type": "external",
        },
    ))
    chunks.append(Chunk(
        chunk_id=f"chunk:{node_id}",
        node_id=node_id,
        path=str(source.get("url", "")),
        start_line=1,
        end_line=len(lines),
        kind="external_source",
        text=sanitized,
        content_hash=_hash_text(sanitized),
        metadata={
            "security_tags": ",".join(tags),
            "source_type": "external",
        },
    ))
    return nodes, edges, chunks


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _expand_nodes(adjacency: Dict[str, List[GraphEdge]], start_node: str, depth: int) -> List[str]:
    frontier = [start_node]
    visited = {start_node}
    for _ in range(depth):
        next_frontier: List[str] = []
        for node_id in frontier:
            for edge in adjacency.get(node_id, []):
                if edge.target not in visited:
                    visited.add(edge.target)
                    next_frontier.append(edge.target)
        frontier = next_frontier
    return list(visited)


def _dedupe_nodes(nodes: List[GraphNode]) -> List[GraphNode]:
    deduped: Dict[str, GraphNode] = {}
    for node in nodes:
        deduped[node.node_id] = node
    return list(deduped.values())


def _dedupe_edges(edges: List[GraphEdge]) -> List[GraphEdge]:
    seen = set()
    deduped: List[GraphEdge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.edge_type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped
