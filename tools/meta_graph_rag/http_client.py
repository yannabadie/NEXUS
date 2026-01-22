"""HTTP utilities with enterprise SSL handling for Meta GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import os
import ssl
import sys
import urllib.request


@dataclass(frozen=True)
class HttpConfig:
    ssl_mode: str = "strict"
    ca_bundle_path: Optional[Path] = None

    @classmethod
    def from_env(cls) -> "HttpConfig":
        ssl_mode = os.getenv("META_RAG_SSL_MODE", "strict").lower()
        ca_bundle = (
            os.getenv("META_RAG_CA_BUNDLE")
            or os.getenv("SSL_CERT_FILE")
            or os.getenv("REQUESTS_CA_BUNDLE")
            or os.getenv("CURL_CA_BUNDLE")
        )
        ca_bundle_path = Path(ca_bundle) if ca_bundle else None
        if not ca_bundle_path:
            ca_bundle_path = _auto_windows_ca_bundle()
        return cls(ssl_mode=ssl_mode, ca_bundle_path=ca_bundle_path)


def build_ssl_context(config: HttpConfig) -> ssl.SSLContext:
    if config.ssl_mode in {"insecure", "skip_verify", "disabled"}:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    context = ssl.create_default_context()
    if config.ca_bundle_path:
        if not config.ca_bundle_path.exists():
            raise RuntimeError(f"CA bundle not found: {config.ca_bundle_path}")
        context.load_verify_locations(cafile=str(config.ca_bundle_path))
    return context


def _auto_windows_ca_bundle() -> Optional[Path]:
    if sys.platform != "win32":
        return None
    workspace = Path(os.getenv("WORKSPACE_PATH", "./workspace"))
    bundle_path = workspace / "meta_rag" / "corp_ca_bundle.pem"
    refresh = os.getenv("META_RAG_CA_REFRESH", "false").lower() == "true"
    if bundle_path.exists() and not refresh:
        return bundle_path

    if not hasattr(ssl, "enum_certificates"):
        return None

    pem_certs = []
    for store in ("ROOT", "CA"):
        try:
            for cert, _encoding, _trust in ssl.enum_certificates(store):
                if not cert:
                    continue
                pem_certs.append(ssl.DER_cert_to_PEM_cert(cert))
        except Exception:
            continue

    if not pem_certs:
        return None

    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    unique = list(dict.fromkeys(pem_certs))
    bundle_path.write_text("".join(unique), encoding="utf-8")
    return bundle_path


def urlopen(
    request_or_url: Union[str, urllib.request.Request],
    timeout: int,
    http_config: Optional[HttpConfig] = None,
):
    config = http_config or HttpConfig.from_env()
    context = build_ssl_context(config)
    return urllib.request.urlopen(request_or_url, timeout=timeout, context=context)
