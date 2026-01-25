# SSL CA Guide (Enterprise Networks)

NEXUS supports corporate CA bundles without disabling TLS verification.
On Windows, NEXUS can auto-export the OS trust store to `workspace/ssl/corp_ca_bundle.pem`.

## Quick Start (Recommended)

1) Run NEXUS once (auto-export on Windows).
2) Verify the bundle exists:
   - `workspace/ssl/corp_ca_bundle.pem`
3) If needed, force refresh:
   - `NEXUS_CA_REFRESH=true`

## Manual Export (Windows, Python)

This mirrors the auto-export logic using Python's `ssl.enum_certificates`.

```powershell
python - <<'PY'
import ssl
from pathlib import Path

bundle = Path("workspace/ssl/corp_ca_bundle.pem")
bundle.parent.mkdir(parents=True, exist_ok=True)

pems = []
for store in ("ROOT", "CA"):
    for cert, _encoding, _trust in ssl.enum_certificates(store):
        if cert:
            pems.append(ssl.DER_cert_to_PEM_cert(cert))

bundle.write_text("".join(dict.fromkeys(pems)), encoding="utf-8")
print("Wrote:", bundle)
PY
```

## Environment Variables

Global:
- `NEXUS_CA_BUNDLE`: path to a PEM bundle
- `NEXUS_SSL_MODE`: `strict` (default), `auto`, `enterprise`, `insecure`
- `NEXUS_CA_REFRESH`: `true` to regenerate the Windows bundle

Provider-specific (overrides global):
- `DEEPSEEK_CA_BUNDLE`
- `KIMI_CA_BUNDLE` / `MOONSHOT_CA_BUNDLE`
- `META_RAG_CA_BUNDLE`

Common TLS variables honored:
- `SSL_CERT_FILE`
- `REQUESTS_CA_BUNDLE`
- `CURL_CA_BUNDLE`
- `NODE_EXTRA_CA_CERTS`
- `GIT_SSL_CAINFO`

## Notes

- Prefer CA bundles over disabling verification.
- Use `NEXUS_SSL_MODE=auto` only if your network intercepts TLS and you cannot install the corporate CA yet.
