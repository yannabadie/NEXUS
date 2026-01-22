"""Deep research ingestion for Meta GraphRAG using Gemini."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from .config import MetaGraphRagConfig
from .http_client import HttpConfig, urlopen
from .research import DEFAULT_SOURCES, _slugify


@dataclass
class ResearchSource:
    source_id: str
    title: str
    url: str
    content: str
    provider: str
    published_at: str
    tags: List[str]


class GeminiResearchClient:
    def __init__(self, api_key: str, model_name: str, http_config: HttpConfig) -> None:
        if not api_key:
            raise ValueError("Gemini API key is required")
        self._api_key = api_key
        self._model_name = model_name
        self._http_config = http_config

    def summarize(self, source: ResearchSource) -> str:
        prompt = _build_prompt(source)
        response = self._generate(prompt)
        return _sanitize_text(response)

    def _generate(self, prompt: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={self._api_key}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt}
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60, http_config=self._http_config) as response:
            result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini generateContent returned no candidates")
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise RuntimeError("Gemini generateContent returned empty content")
        return parts[0].get("text", "")


def run_deep_research(config: MetaGraphRagConfig) -> List[Path]:
    if not config.gemini_api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is required for deep research")

    http_config = HttpConfig(ssl_mode=config.ssl_mode, ca_bundle_path=config.ca_bundle_path)

    client = GeminiResearchClient(
        api_key=config.gemini_api_key,
        model_name=config.gemini_generation_model,
        http_config=http_config,
    )

    sources: List[ResearchSource] = []
    sources.extend(_static_sources(http_config))

    for query in config.research_queries:
        sources.extend(_search_arxiv(query, config.research_limit, http_config))
        sources.extend(_search_semantic_scholar(query, config.research_limit, http_config))

    deduped = _dedupe_sources(sources)

    output_paths: List[Path] = []
    records: List[Dict[str, object]] = []
    config.sources_path.mkdir(parents=True, exist_ok=True)

    for source in deduped:
        try:
            summary = client.summarize(source)
        except Exception as exc:
            summary = _fallback_summary(source, exc)
        content = _format_summary(source, summary)
        text_path = f"{source.source_id}.md"
        full_path = config.sources_path / text_path
        full_path.write_text(content, encoding="utf-8")
        output_paths.append(full_path)

        record_hash = _hash_text(content)
        records.append({
            "id": source.source_id,
            "url": source.url,
            "title": source.title,
            "text_path": text_path,
            "hash": record_hash,
            "fetched_at": _utc_now(),
            "tags": source.tags,
            "provider": source.provider,
            "published_at": source.published_at,
        })

    manifest = {
        "generated_at": _utc_now(),
        "sources": records,
    }
    (config.sources_path / "sources.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    return output_paths


def _static_sources(http_config: HttpConfig) -> List[ResearchSource]:
    items = []
    for source in DEFAULT_SOURCES:
        url = source["url"]
        title = source.get("title", url)
        tags = source.get("tags", [])
        content = _fetch_text(url, http_config)
        source_id = _slugify(title)
        items.append(ResearchSource(
            source_id=source_id,
            title=title,
            url=url,
            content=content,
            provider="static",
            published_at="",
            tags=tags,
        ))
    return items


def _search_arxiv(query: str, limit: int, http_config: HttpConfig) -> List[ResearchSource]:
    safe_query = urllib.parse.quote(query)
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query=all:{safe_query}&start=0&max_results={limit}"
    )
    raw = _fetch_text(url, http_config)
    entries = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return entries

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=ns).strip()
        entry_id = entry.findtext("atom:id", default="", namespaces=ns).strip()
        published = entry.findtext("atom:published", default="", namespaces=ns).strip()
        if not title or not entry_id:
            continue
        content = f"Title: {title}\nURL: {entry_id}\nPublished: {published}\n\nAbstract:\n{summary}"
        source_id = _slugify(f"arxiv-{title}")
        entries.append(ResearchSource(
            source_id=source_id,
            title=title,
            url=entry_id,
            content=content,
            provider="arxiv",
            published_at=published,
            tags=["arxiv", "paper"],
        ))
    return entries


def _search_semantic_scholar(query: str, limit: int, http_config: HttpConfig) -> List[ResearchSource]:
    params = urllib.parse.urlencode({
        "query": query,
        "limit": str(limit),
        "fields": "title,abstract,year,url,authors",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    try:
        raw = _fetch_json(url, http_config)
    except Exception:
        return []
    entries = []
    for item in raw.get("data", []):
        title = item.get("title", "")
        abstract = item.get("abstract", "") or ""
        year = item.get("year")
        url_value = item.get("url") or ""
        if not title:
            continue
        content = f"Title: {title}\nURL: {url_value}\nYear: {year}\n\nAbstract:\n{abstract}"
        source_id = _slugify(f"semantic-{title}")
        entries.append(ResearchSource(
            source_id=source_id,
            title=title,
            url=url_value,
            content=content,
            provider="semantic_scholar",
            published_at=str(year or ""),
            tags=["semantic_scholar", "paper"],
        ))
    return entries


def _dedupe_sources(sources: Iterable[ResearchSource]) -> List[ResearchSource]:
    seen = set()
    unique: List[ResearchSource] = []
    for source in sources:
        key = source.url or source.title
        if key in seen:
            continue
        seen.add(key)
        unique.append(source)
    return unique


def _build_prompt(source: ResearchSource) -> str:
    content = source.content
    if len(content) > 12000:
        content = content[:12000] + "\n[TRUNCATED]"
    return (
        "You are a research analyst. Summarize the source for NEXUS meta-memory.\n"
        "Use ASCII only. Provide a concise, actionable brief with these sections:\n"
        "- Summary\n- Key Findings\n- Relevance to NEXUS\n- Security or Blind Spots\n- Implementation Ideas\n- Citation\n\n"
        f"Title: {source.title}\nURL: {source.url}\n\n"
        f"Content:\n{content}\n"
    )


def _format_summary(source: ResearchSource, summary: str) -> str:
    lines = [
        f"# {source.title}",
        "",
        f"URL: {source.url}",
        f"Provider: {source.provider}",
        f"Published: {source.published_at}",
        f"Fetched: {_utc_now()}",
        f"Tags: {', '.join(source.tags)}",
        "",
        summary.strip(),
        "",
    ]
    return "\n".join(lines)


def _fallback_summary(source: ResearchSource, exc: Exception) -> str:
    return (
        "Summary\n"
        "- Gemini summarization failed; storing raw content instead.\n\n"
        "Key Findings\n"
        f"- Error: {exc}\n"
    )


def _fetch_text(url: str, http_config: HttpConfig) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NEXUS-MetaGraphRAG/1.0"},
    )
    with urlopen(request, timeout=60, http_config=http_config) as response:
        data = response.read().decode("utf-8", errors="ignore")
    return _sanitize_text(data)


def _fetch_json(url: str, http_config: HttpConfig) -> Dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NEXUS-MetaGraphRAG/1.0"},
    )
    with urlopen(request, timeout=60, http_config=http_config) as response:
        data = response.read().decode("utf-8", errors="ignore")
    return json.loads(data)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_text(text: str) -> str:
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"\n{3,}", "\n\n", ascii_text)
    return ascii_text.strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
