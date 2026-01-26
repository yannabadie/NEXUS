"""Embedding backends and vector index for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol
import json
import hashlib
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
        timeout: int = 30,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._api_key = api_key
        self._model_name = model_name
        self._batch_size = max(1, batch_size)
        self._output_dimensionality = output_dimensionality
        self._default_task_type = default_task_type
        self._http_config = http_config or HttpConfig.from_env()
        self._timeout = timeout

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
        result = self._request_json(request, timeout=self._timeout)
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
            result = self._request_json(request, timeout=self._timeout)
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


class DeepSeekEmbeddingBackend:
    """DeepSeek OpenAI-compatible embeddings backend."""

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model_name: str,
        batch_size: int = 8,
        expected_dim: Optional[int] = None,
        http_config: Optional[HttpConfig] = None,
        timeout: int = 60,
    ) -> None:
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        if not model_name:
            raise ValueError("DeepSeek embedding model is required")
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._model_name = model_name
        self._batch_size = max(1, batch_size)
        self._expected_dim = expected_dim
        self._http_config = http_config or HttpConfig.from_env()
        self._timeout = timeout
        self._resolved_model: Optional[str] = None

    def _is_auto_model(self) -> bool:
        return self._model_name.lower() in {"auto", "latest", "embedding-latest"}

    def _model_sort_key(self, model_id: str) -> tuple:
        digits = [int(value) for value in re.findall(r"\d+", model_id)] or [0]
        return (digits, len(model_id), model_id)

    def _fetch_models(self) -> List[str]:
        url = f"{self._api_base}/models"
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            method="GET",
        )
        result = self._request_json(request, timeout=self._timeout)
        data = result.get("data", []) if isinstance(result, dict) else []
        model_ids = [
            item.get("id")
            for item in data
            if isinstance(item, dict) and item.get("id")
        ]
        return [model_id for model_id in model_ids if model_id]

    def _resolve_model(self) -> str:
        if self._resolved_model:
            return self._resolved_model
        if not self._is_auto_model():
            self._resolved_model = self._model_name
            return self._resolved_model
        try:
            model_ids = self._fetch_models()
        except Exception:
            self._resolved_model = self._model_name
            return self._resolved_model
        embedding_models = [
            model_id for model_id in model_ids
            if "embed" in model_id.lower()
        ]
        if not embedding_models:
            self._resolved_model = self._model_name
            return self._resolved_model
        self._resolved_model = max(embedding_models, key=self._model_sort_key)
        return self._resolved_model

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        if not texts:
            return []
        if len(texts) <= self._batch_size:
            return self._embed_batch(texts)
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start:start + self._batch_size]
            embeddings.extend(self._embed_batch(batch))
        return embeddings

    def info(self) -> Dict[str, str]:
        return {"backend": "deepseek", "model": self._model_name}

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._resolve_model()
        url = f"{self._api_base}/embeddings"
        payload = {
            "model": model,
            "input": texts,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        result = self._request_json(request, timeout=self._timeout)
        data_items = result.get("data", []) if isinstance(result, dict) else []
        if not data_items:
            raise RuntimeError("DeepSeek embedding response missing data")
        ordered = sorted(
            [item for item in data_items if isinstance(item, dict)],
            key=lambda item: item.get("index", 0),
        )
        embeddings: List[List[float]] = []
        for item in ordered:
            embedding = item.get("embedding")
            if not embedding:
                raise RuntimeError("DeepSeek embedding response missing embedding values")
            if self._expected_dim and len(embedding) != self._expected_dim:
                raise RuntimeError(
                    "DeepSeek embedding dimension mismatch: "
                    f"{len(embedding)} != {self._expected_dim}"
                )
            embeddings.append(embedding)
        return embeddings

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
        raise RuntimeError("DeepSeek request failed")


class FallbackEmbeddingBackend:
    """Fallback embeddings wrapper (Gemini -> DeepSeek on quota/429)."""

    def __init__(
        self,
        primary: EmbeddingBackend,
        fallback: EmbeddingBackend,
        fallback_statuses: Optional[set[int]] = None,
        fallback_markers: Optional[set[str]] = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._fallback_statuses = fallback_statuses or {429}
        self._fallback_markers = fallback_markers or {"quota", "resource_exhausted"}

    def embed_texts(self, texts: List[str], task_type: Optional[str] = None) -> List[List[float]]:
        try:
            return self._primary.embed_texts(texts, task_type=task_type)
        except urllib.error.HTTPError as exc:
            if self._should_fallback_http(exc):
                return self._fallback.embed_texts(texts, task_type=task_type)
            raise
        except RuntimeError as exc:
            if self._should_fallback_message(str(exc)):
                return self._fallback.embed_texts(texts, task_type=task_type)
            raise

    def info(self) -> Dict[str, str]:
        primary_info = self._primary.info()
        fallback_info = self._fallback.info()
        payload = {
            "backend": "fallback",
            "primary_backend": primary_info.get("backend", ""),
            "primary_model": primary_info.get("model", ""),
            "fallback_backend": fallback_info.get("backend", ""),
            "fallback_model": fallback_info.get("model", ""),
            "policy": "quota/429",
        }
        return {key: value for key, value in payload.items() if value}

    def _should_fallback_message(self, message: str) -> bool:
        lowered = message.lower()
        return any(marker in lowered for marker in self._fallback_markers)

    def _should_fallback_http(self, exc: urllib.error.HTTPError) -> bool:
        if exc.code in self._fallback_statuses:
            return True
        try:
            body = exc.read().decode("utf-8").lower()
        except Exception:
            body = ""
        if exc.code == 403 and self._should_fallback_message(body):
            return True
        return self._should_fallback_message(str(exc))


@dataclass
class VectorRecord:
    chunk_id: str
    embedding: List[float]
    metadata: Dict[str, str]


class QueryEmbeddingCache:
    """Simple JSON-backed cache for query embeddings."""

    def __init__(self, path: Path, ttl_seconds: int = 3600, max_entries: int = 1000) -> None:
        self._path = path
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._loaded = False
        self._entries: Dict[str, Dict[str, object]] = {}

    def get(
        self,
        query_text: str,
        backend_info: Dict[str, str],
        task_type: Optional[str],
    ) -> Optional[List[float]]:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return None
        self._load()
        key = self._make_key(query_text, backend_info, task_type)
        entry = self._entries.get(key)
        if not entry:
            return None
        updated_at = float(entry.get("updated_at", 0.0))
        if self._ttl_seconds and (time.time() - updated_at) > self._ttl_seconds:
            self._entries.pop(key, None)
            self._save()
            return None
        embedding = entry.get("embedding")
        if isinstance(embedding, list):
            return embedding
        return None

    def set(
        self,
        query_text: str,
        backend_info: Dict[str, str],
        task_type: Optional[str],
        embedding: List[float],
    ) -> None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return
        self._load()
        key = self._make_key(query_text, backend_info, task_type)
        self._entries[key] = {
            "embedding": embedding,
            "updated_at": time.time(),
        }
        self._evict()
        self._save()

    def _make_key(
        self,
        query_text: str,
        backend_info: Dict[str, str],
        task_type: Optional[str],
    ) -> str:
        payload = {
            "backend": backend_info,
            "task_type": task_type or "",
            "query": query_text,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _evict(self) -> None:
        if len(self._entries) <= self._max_entries:
            return
        oldest = sorted(self._entries.items(), key=lambda item: float(item[1].get("updated_at", 0.0)))
        excess = len(self._entries) - self._max_entries
        for key, _ in oldest[:excess]:
            self._entries.pop(key, None)

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        entries = payload.get("entries") if isinstance(payload, dict) else None
        if isinstance(entries, dict):
            self._entries = entries

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "entries": self._entries,
        }
        self._path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


class VectorIndex:
    """Simple JSON-backed vector index."""

    def __init__(
        self,
        backend: EmbeddingBackend,
        document_task_type: Optional[str] = None,
        query_task_type: Optional[str] = None,
        source_weights: Optional[Dict[str, float]] = None,
        query_cache: Optional[QueryEmbeddingCache] = None,
        chunk_cache_enabled: bool = True,
    ) -> None:
        self.backend = backend
        self.entries: Dict[str, VectorRecord] = {}
        self.document_task_type = document_task_type
        self.query_task_type = query_task_type
        self.source_weights = source_weights or {}
        self.query_cache = query_cache
        self._chunk_cache_enabled = chunk_cache_enabled
        self._chunk_embedding_cache: Dict[str, List[float]] = {}

    def add_texts(self, records: List[VectorRecord]) -> None:
        to_embed: List[VectorRecord] = []
        for record in records:
            cached = self._get_cached_embedding(record.metadata)
            if cached is None:
                to_embed.append(record)
                continue
            self.entries[record.chunk_id] = VectorRecord(
                chunk_id=record.chunk_id,
                embedding=cached,
                metadata=record.metadata,
            )
            self._cache_embedding(record.metadata, cached)
        if to_embed:
            texts = [record.metadata.get("text", "") for record in to_embed]
            embeddings = self.backend.embed_texts(texts, task_type=self.document_task_type)
            for record, embedding in zip(to_embed, embeddings):
                self.entries[record.chunk_id] = VectorRecord(
                    chunk_id=record.chunk_id,
                    embedding=embedding,
                    metadata=record.metadata,
                )
                self._cache_embedding(record.metadata, embedding)

    def remove(self, chunk_ids: List[str]) -> None:
        for chunk_id in chunk_ids:
            self.entries.pop(chunk_id, None)

    def query(self, query_text: str, limit: int = 5) -> List[VectorRecord]:
        query_embedding = None
        if self.query_cache is not None:
            query_embedding = self.query_cache.get(
                query_text,
                backend_info=self.backend.info(),
                task_type=self.query_task_type,
            )
        if query_embedding is None:
            query_embedding = self.backend.embed_texts([query_text], task_type=self.query_task_type)[0]
            if self.query_cache is not None:
                self.query_cache.set(
                    query_text,
                    backend_info=self.backend.info(),
                    task_type=self.query_task_type,
                    embedding=query_embedding,
                )
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
        query_cache: Optional[QueryEmbeddingCache] = None,
        chunk_cache_enabled: bool = True,
    ) -> "VectorIndex":
        index = cls(
            backend,
            document_task_type=document_task_type,
            query_task_type=query_task_type,
            source_weights=source_weights,
            query_cache=query_cache,
            chunk_cache_enabled=chunk_cache_enabled,
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
        index._build_chunk_cache()
        return index

    def _build_chunk_cache(self) -> None:
        if not self._chunk_cache_enabled:
            return
        for record in self.entries.values():
            content_hash = self._content_hash_from_metadata(record.metadata)
            if not content_hash:
                continue
            key = self._make_chunk_cache_key(content_hash)
            self._chunk_embedding_cache.setdefault(key, record.embedding)

    def _get_cached_embedding(self, metadata: Dict[str, str]) -> Optional[List[float]]:
        if not self._chunk_cache_enabled:
            return None
        content_hash = self._content_hash_from_metadata(metadata)
        if not content_hash:
            return None
        key = self._make_chunk_cache_key(content_hash)
        return self._chunk_embedding_cache.get(key)

    def _cache_embedding(self, metadata: Dict[str, str], embedding: List[float]) -> None:
        if not self._chunk_cache_enabled:
            return
        content_hash = self._content_hash_from_metadata(metadata)
        if not content_hash:
            return
        key = self._make_chunk_cache_key(content_hash)
        self._chunk_embedding_cache[key] = embedding

    def _content_hash_from_metadata(self, metadata: Dict[str, str]) -> Optional[str]:
        content_hash = metadata.get("content_hash")
        if content_hash:
            return content_hash
        text = metadata.get("text")
        if not text:
            return None
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        metadata["content_hash"] = content_hash
        return content_hash

    def _make_chunk_cache_key(self, content_hash: str) -> str:
        payload = {
            "backend": self.backend.info(),
            "task_type": self.document_task_type or "",
            "content_hash": content_hash,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
