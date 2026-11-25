"""Cliente HTTP compartilhado e autenticado para a Gateway.

Corrige os achados da vitrine:
- L1: TLS ligado (verify=True / CA configurável); nunca verify=False.
- L2: cache de token com TTL (TokenCache).
- L9/L10: log estruturado com Authorization mascarado (mask_headers), sem print.
- L11: cliente único reutilizado pelos módulos de services/gateway.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Callable, Optional

import requests

logger = logging.getLogger("GatewayHttpClient")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _console = logging.StreamHandler(sys.stdout)
    _console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(_console)


def mask_headers(headers: Optional[dict]) -> Optional[dict]:
    """Mascara o header Authorization para log (L10). Não muta o original."""
    if not headers:
        return headers
    masked = dict(headers)
    if "Authorization" in masked:
        masked["Authorization"] = "***"
    return masked


class TokenCache:
    """Cache de token com TTL (L2). Só reautentica ao expirar."""

    def __init__(self, ttl_seconds: int = 300, time_fn: Callable[[], float] = time.time):
        self._ttl = ttl_seconds
        self._time_fn = time_fn
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get_or_refresh(self, fetch_fn: Callable[[], str]) -> str:
        now = self._time_fn()
        if self._token is None or now >= self._expires_at:
            self._token = fetch_fn()
            self._expires_at = now + self._ttl
        return self._token


def _tls_verify():
    """L1: usa o CA bundle configurado, ou True (verifica TLS) por padrão."""
    return os.getenv("PATH_ROOT_CA") or True


class LoggedSession(requests.Session):
    """requests.Session com log estruturado e TLS sempre ligado."""

    def __init__(self):
        super().__init__()
        self.verify = _tls_verify()

    def request(self, method, url, **kwargs):
        start = time.time()
        response = super().request(method, url, **kwargs)
        elapsed = round(time.time() - start, 2)
        logger.info(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    "request": {
                        "method": method,
                        "url": url,
                        "params": kwargs.get("params"),
                        "headers": mask_headers(kwargs.get("headers")),
                    },
                    "response": {"status_code": response.status_code},
                    "elapsed_time": f"{elapsed} segundos",
                },
                ensure_ascii=False,
            )
        )
        return response
