"""Web research ingestion for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional
import hashlib
import json
import re
import urllib.request


DEFAULT_SOURCES = [
    {
        "url": "https://github.com/microsoft/graphrag",
        "title": "Microsoft GraphRAG (GitHub)",
        "tags": ["graphrag", "knowledge-graph"],
    },
    {
        "url": "https://www.microsoft.com/en-us/research/project/graphrag/",
        "title": "GraphRAG Project Page",
        "tags": ["graphrag", "research"],
    },
    {
        "url": "https://arxiv.org/abs/2404.16130",
        "title": "GraphRAG Paper (ArXiv)",
        "tags": ["graphrag", "paper"],
    },
    {
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "title": "OWASP LLM Top 10",
        "tags": ["security", "llm"],
    },
    {
        "url": "https://arxiv.org/abs/2312.10997",
        "title": "RAG Survey (ArXiv)",
        "tags": ["rag", "survey"],
    },
]


@dataclass
class SourceRecord:
    source_id: str
    url: str
    title: str
    text_path: str
    content_hash: str
    fetched_at: str
    tags: List[str]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._parts)


def fetch_sources(
    sources_path: Path,
    urls: Optional[List[str]] = None,
) -> List[SourceRecord]:
    sources_path.mkdir(parents=True, exist_ok=True)
    records: List[SourceRecord] = []
    targets = urls or [source["url"] for source in DEFAULT_SOURCES]

    for url in targets:
        payload = _fetch_url(url)
        text = _sanitize_text(payload)
        content_hash = _hash_text(text)
        slug = _slugify(url)
        text_path = f"{slug}.txt"
        (sources_path / text_path).write_text(text, encoding="utf-8")

        title = _title_for(url)
        record = SourceRecord(
            source_id=slug,
            url=url,
            title=title,
            text_path=text_path,
            content_hash=content_hash,
            fetched_at=_utc_now(),
            tags=_tags_for(url),
        )
        records.append(record)

    _save_manifest(records, sources_path)
    return records


def _fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NEXUS-MetaGraphRAG/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read().decode("utf-8", errors="ignore")
    if "text/html" in content_type:
        parser = _TextExtractor()
        parser.feed(raw)
        return parser.get_text()
    return raw


def _sanitize_text(text: str) -> str:
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"\n{3,}", "\n\n", ascii_text)
    return ascii_text.strip()


def _save_manifest(records: List[SourceRecord], sources_path: Path) -> None:
    payload = {
        "generated_at": _utc_now(),
        "sources": [
            {
                "id": record.source_id,
                "url": record.url,
                "title": record.title,
                "text_path": record.text_path,
                "hash": record.content_hash,
                "fetched_at": record.fetched_at,
                "tags": record.tags,
            }
            for record in records
        ],
    }
    (sources_path / "sources.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _title_for(url: str) -> str:
    for source in DEFAULT_SOURCES:
        if source["url"] == url:
            return source.get("title", url)
    return url


def _tags_for(url: str) -> List[str]:
    for source in DEFAULT_SOURCES:
        if source["url"] == url:
            return source.get("tags", [])
    return []


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
