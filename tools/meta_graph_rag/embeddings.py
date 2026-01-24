"""Embedding backends and vector index for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol
import json
import math
import re
import time
from pathlib import Path
import urllib.request
import urllib.error

from .http_client import HttpConfig, urlopen


class EmbeddingBackend(Protocol):
    """Protocol for embedding backends."""

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        ...

    def info(self) -> Dict[str, str]:
        ...


class HashEmbeddingBackend:
    """Deterministic hashing-based embeddings (fallback)."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def info(self) -> Dict[str, str]:
        return {"backend": "hash", "dim": str(self.dim)}

    def _embed(self, text: str) -> List[float]:
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]+", text.lower())
        vec = [0.0] * self.dim
        for token in tokens:
            idx = hash(token) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class NoopEmbeddingBackend:
    """No-op backend for graph-only indexing (no embeddings)."""

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        return [[0.0] for _ in texts]

    def info(self) -> Dict[str, str]:
        return {"backend": "none", "dim": "1"}


class SentenceTransformerBackend:
    """Sentence-transformers embedding backend."""

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence-transformers not available") from exc
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=False)
        result: List[List[float]] = []
        for row in embeddings:
            if isinstance(row, list):
                result.append(row)
            else:
                result.append(row.tolist())
        return result

    def info(self) -> Dict[str, str]:
        return {"backend": "sentence-transformers", "model": self._model_name}


class GeminiEmbeddingBackend:
    """Gemini API embeddings backend."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        batch_size: int = 8,
        output_dimensionality: Optional[int] = None,
        default_task_type: Optional[str] = None,
        http_config: Optional[HttpConfig] = None,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._api_key = api_key
        self._model_name = model_name
        self._batch_size = max(1, batch_size)
        self._output_dimensionality = output_dimensionality
        self._default_task_type = default_task_type
        self._http_config = http_config or HttpConfig.from_env()

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        effective_task = task_type or self._default_task_type
        if len(texts) <= 1:
            return [self._embed_single(texts[0], effective_task)] if texts else []
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start:start + self._batch_size]
            embeddings.extend(self._embed_batch(batch, effective_task))
        return embeddings

    def info(self) -> Dict[str, str]:
        return {"backend": "gemini", "model": self._model_name}

    def _embed_single(self, text: str, task_type: Optional[str]) -> List[float]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:embedContent?key={self._api_key}"
        )
        payload = {
            "content": {
                "parts": [
                    {"text": text}
                ]
            }
        }
        if task_type:
            payload["taskType"] = task_type
        if self._output_dimensionality:
            payload["outputDimensionality"] = self._output_dimensionality
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        result = self._request_json(request, timeout=30)
        embedding = result.get("embedding", {}).get("values")
        if not embedding:
            raise RuntimeError("Gemini embedding response missing values")
        return embedding

    def _embed_batch(self, texts: List[str], task_type: Optional[str]) -> List[List[float]]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:batchEmbedContents?key={self._api_key}"
        )
        payload = {
            "requests": [
                {
                    "model": f"models/{self._model_name}",
                    "content": {
                        "parts": [{"text": text}]
                    }
                }
                for text in texts
            ]
        }
        if task_type or self._output_dimensionality:
            for request in payload["requests"]:
                if task_type:
                    request["taskType"] = task_type
                if self._output_dimensionality:
                    request["outputDimensionality"] = self._output_dimensionality
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            result = self._request_json(request, timeout=30)
            embeddings = result.get("embeddings")
            if not embeddings:
                raise RuntimeError("Gemini batch embedding response missing embeddings")
            values = []
            for item in embeddings:
                values.append(item.get("values", []))
            return values
        except Exception:
            return [self._embed_single(text, task_type) for text in texts]

    def _request_json(self, request: urllib.request.Request, timeout: int) -> Dict[str, object]:
        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                with urlopen(request, timeout=timeout, http_config=self._http_config) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
                    _sleep_backoff(attempt, exc.code)
                    continue
                raise
            except urllib.error.URLError as exc:
                last_exc = exc
                if attempt < 3:
                    _sleep_backoff(attempt, None)
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("Gemini request failed")


@dataclass
class VectorRecord:
    chunk_id: str
    embedding: List[float]
    metadata: Dict[str, str]


class VectorIndex:
    """Simple JSON-backed vector index."""

    def __init__(
        self,
        backend: EmbeddingBackend,
        document_task_type: Optional[str] = None,
        query_task_type: Optional[str] = None,
        source_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.backend = backend
        self.entries: Dict[str, VectorRecord] = {}
        self.document_task_type = document_task_type
        self.query_task_type = query_task_type
        self.source_weights = source_weights or {}

    def add_texts(self, records: List[VectorRecord]) -> None:
        texts = [record.metadata.get("text", "") for record in records]
        embeddings = self.backend.embed_texts(texts, task_type=self.document_task_type)
        for record, embedding in zip(records, embeddings):
            self.entries[record.chunk_id] = VectorRecord(
                chunk_id=record.chunk_id,
                embedding=embedding,
                metadata=record.metadata,
            )

    def remove(self, chunk_ids: List[str]) -> None:
        for chunk_id in chunk_ids:
            self.entries.pop(chunk_id, None)

    def query(self, query_text: str, limit: int = 5) -> List[VectorRecord]:
        query_embedding = self.backend.embed_texts([query_text], task_type=self.query_task_type)[0]
        scored: List[tuple[float, VectorRecord]] = []
        for record in self.entries.values():
            score = _cosine_similarity(query_embedding, record.embedding)
            source_type = record.metadata.get("source_type", "")
            weight = self.source_weights.get(source_type, 1.0)
            scored.append((score * weight, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:limit]]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "backend": self.backend.info(),
            "document_task_type": self.document_task_type,
            "query_task_type": self.query_task_type,
            "source_weights": self.source_weights,
            "entries": [
                {
                    "chunk_id": record.chunk_id,
                    "embedding": record.embedding,
                    "metadata": record.metadata,
                }
                for record in self.entries.values()
            ],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    @classmethod
    def load(
        cls,
        path: Path,
        backend: EmbeddingBackend,
        document_task_type: Optional[str] = None,
        query_task_type: Optional[str] = None,
        source_weights: Optional[Dict[str, float]] = None,
    ) -> "VectorIndex":
        index = cls(
            backend,
            document_task_type=document_task_type,
            query_task_type=query_task_type,
            source_weights=source_weights,
        )
        if not path.exists():
            return index
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return index
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return index
        for entry in payload.get("entries", []):
            index.entries[entry["chunk_id"]] = VectorRecord(
                chunk_id=entry["chunk_id"],
                embedding=entry["embedding"],
                metadata=entry["metadata"],
            )
        return index


def _cosine_similarity(left: List[float], right: List[float]) -> float:
    if not left or not right:
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for l_val, r_val in zip(left, right):
        dot += l_val * r_val
        left_norm += l_val * l_val
        right_norm += r_val * r_val
    denom = math.sqrt(left_norm) * math.sqrt(right_norm)
    return dot / denom if denom else 0.0


def _sleep_backoff(attempt: int, status_code: Optional[int]) -> None:
    base = 2 ** (attempt - 1)
    delay = min(base, 16)
    time.sleep(delay)
