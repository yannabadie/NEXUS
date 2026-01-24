"""Evaluation harness for Meta GraphRAG retrieval quality."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import importlib.util
import json
import time

from .indexer import MetaGraphIndexer, _expand_nodes


DEFAULT_EVAL_QUERIES = "eval/queries.json"


@dataclass
class EvalQuery:
    query_id: str
    query: str
    expected_paths: List[str] = field(default_factory=list)
    expected_nodes: List[str] = field(default_factory=list)
    notes: Optional[str] = None


def load_queries(path: Path) -> List[EvalQuery]:
    if not path.exists():
        raise FileNotFoundError(f"Eval queries file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    queries: List[EvalQuery] = []
    for item in payload.get("queries", []):
        if not item:
            continue
        queries.append(EvalQuery(
            query_id=str(item.get("id") or item.get("query") or f"query_{len(queries)+1}"),
            query=str(item.get("query", "")).strip(),
            expected_paths=list(item.get("expected_paths", []) or []),
            expected_nodes=list(item.get("expected_nodes", []) or []),
            notes=item.get("notes"),
        ))
    return queries


def run_eval(
    indexer: MetaGraphIndexer,
    queries: Iterable[EvalQuery],
    seed_limit: int,
    expansion_depth: int,
    expansion_limit: int,
) -> Dict[str, Any]:
    started_at = time.time()
    results = []

    for query in queries:
        seed_chunks, expanded_chunks = _collect_candidates(
            indexer,
            query.query,
            seed_limit=seed_limit,
            expansion_depth=expansion_depth,
            expansion_limit=expansion_limit,
        )

        seed_eval = _score_query(query, seed_chunks)
        expanded_eval = _score_query(query, seed_chunks + expanded_chunks)

        results.append({
            "id": query.query_id,
            "query": query.query,
            "expected_paths": query.expected_paths,
            "expected_nodes": query.expected_nodes,
            "seed": seed_eval,
            "expanded": expanded_eval,
        })

    summary = _summarize_results(results)

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_seconds": round(time.time() - started_at, 2),
        "seed_limit": seed_limit,
        "expansion_depth": expansion_depth,
        "expansion_limit": expansion_limit,
        "results": results,
        "summary": summary,
        "integrations": _detect_optional_evaluators(),
    }


def write_report(report: Dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return output_path


def _collect_candidates(
    indexer: MetaGraphIndexer,
    query: str,
    seed_limit: int,
    expansion_depth: int,
    expansion_limit: int,
) -> Tuple[List[Any], List[Any]]:
    seed_records = indexer.vector_index.query(query, limit=seed_limit)
    seed_chunks = [
        indexer.chunks.chunks[record.chunk_id]
        for record in seed_records
        if record.chunk_id in indexer.chunks.chunks
    ]

    expanded_chunks: List[Any] = []
    if expansion_depth > 0 and expansion_limit > 0 and seed_chunks:
        adjacency = indexer.graph.build_adjacency()
        expanded_nodes: List[str] = []
        for chunk in seed_chunks:
            expanded_nodes.extend(_expand_nodes(adjacency, chunk.node_id, expansion_depth))
        expanded_nodes = list(dict.fromkeys(expanded_nodes))
        seed_chunk_ids = {chunk.chunk_id for chunk in seed_chunks}
        for node_id in expanded_nodes:
            for chunk in indexer.chunks.get_by_node(node_id):
                if chunk.chunk_id in seed_chunk_ids:
                    continue
                expanded_chunks.append(chunk)
                if len(expanded_chunks) >= expansion_limit:
                    break
            if len(expanded_chunks) >= expansion_limit:
                break

    return seed_chunks, expanded_chunks


def _score_query(query: EvalQuery, chunks: List[Any]) -> Dict[str, Any]:
    expected_total = len(query.expected_paths) + len(query.expected_nodes)
    candidate_paths = [chunk.path for chunk in chunks]
    candidate_nodes = [chunk.node_id for chunk in chunks]

    matched_paths = _count_path_matches(query.expected_paths, candidate_paths)
    matched_nodes = _count_node_matches(query.expected_nodes, candidate_nodes)
    matched_total = matched_paths + matched_nodes

    precision = 0.0
    if chunks:
        precision = matched_total / len(chunks)

    recall = 0.0
    if expected_total:
        recall = matched_total / expected_total

    mrr = _mrr(query.expected_paths, query.expected_nodes, candidate_paths, candidate_nodes)

    return {
        "candidates": len(chunks),
        "matched_total": matched_total,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "mrr": round(mrr, 4),
        "paths": candidate_paths[:25],
    }


def _summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {}

    def avg(values: List[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    seed_precision = [r["seed"]["precision"] for r in results]
    seed_recall = [r["seed"]["recall"] for r in results]
    seed_mrr = [r["seed"]["mrr"] for r in results]

    expanded_precision = [r["expanded"]["precision"] for r in results]
    expanded_recall = [r["expanded"]["recall"] for r in results]
    expanded_mrr = [r["expanded"]["mrr"] for r in results]

    return {
        "queries": len(results),
        "seed_avg_precision": avg(seed_precision),
        "seed_avg_recall": avg(seed_recall),
        "seed_avg_mrr": avg(seed_mrr),
        "expanded_avg_precision": avg(expanded_precision),
        "expanded_avg_recall": avg(expanded_recall),
        "expanded_avg_mrr": avg(expanded_mrr),
    }


def _detect_optional_evaluators() -> Dict[str, bool]:
    return {
        "ragas": importlib.util.find_spec("ragas") is not None,
        "trulens": importlib.util.find_spec("trulens_eval") is not None,
        "deepeval": importlib.util.find_spec("deepeval") is not None,
    }


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def _path_matches(expected: str, candidate: str) -> bool:
    expected_norm = _normalize_path(expected)
    candidate_norm = _normalize_path(candidate)
    return candidate_norm.endswith(expected_norm) or expected_norm in candidate_norm


def _count_path_matches(expected_paths: List[str], candidates: List[str]) -> int:
    matched = 0
    for expected in expected_paths:
        if any(_path_matches(expected, candidate) for candidate in candidates):
            matched += 1
    return matched


def _count_node_matches(expected_nodes: List[str], candidates: List[str]) -> int:
    return sum(1 for expected in expected_nodes if expected in candidates)
