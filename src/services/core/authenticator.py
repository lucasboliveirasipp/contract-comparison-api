"""Autenticação e resolução de URLs dos microserviços GenAI da Gateway.

Subconjunto jurídico: filemanager, indexer, orchestrator_agent, qa,
workflow_request, workflow_response, plataforma.

Correções vs. vitrine: sem print (L9), sem verify=False (L1), sem fallback de
secret no código (L12), com cache de token (L2).
"""

import os
from typing import Optional

from src.services.core.errors import GatewayAuthError
from src.services.core.http_client import LoggedSession, TokenCache

VALID_MODES = ("APIM", "GATEWAY")


class Autenticator:
    def __init__(self, connection_mode: str = "APIM", token_cache: Optional[TokenCache] = None):
        if connection_mode not in VALID_MODES:
            raise ValueError("Modo inválido. Use 'APIM' ou 'GATEWAY'.")

        self.connection_mode = connection_mode
        self._session = LoggedSession()
        self._cache = token_cache or TokenCache()

        prefix = "GATEWAY_" if connection_mode == "GATEWAY" else "APIM_"
        self.base_url = os.getenv(f"{prefix}URL") or ""

        self.file_manager_url = self._resolve(prefix, "FILEMANAGER_URL")
        self.indexer_url = self._resolve(prefix, "INDEXER_URL")
        self.orchestrator_agent_url = self._resolve(prefix, "ORCHESTRATOR_AGENT_URL")
        self.qa_url = self._resolve(prefix, "QA_URL")
        self.workflow_request_url = self._resolve(prefix, "WORKFLOW-REQUEST_URL")
        self.workflow_response_url = self._resolve(prefix, "WORKFLOW-RESPONSE_URL")
        self.plataforma_url = self._resolve(prefix, "PLATAFORMA_URL")

        self.gateway_auth_url = self.base_url + (os.getenv("GATEWAY_AUTH_URL") or "")

    def _resolve(self, prefix: str, suffix: str) -> str:
        return self.base_url + (os.getenv(f"{prefix}{suffix}") or "")

    def authenticate_apim(self) -> str:
        tenant_id = os.getenv("TENANTID")
        scope = os.getenv("SCOPEAPIMID") or ""
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": os.getenv("HUBCOMPARADORAPPID"),
            "client_secret": os.getenv("HUBCOMPARADORCLIENTSECRET"),
            "scope": scope.replace("APIMAuth.Read", ".default"),
        }
        response = self._session.post(token_url, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise GatewayAuthError(detail="APIM não retornou access_token")
        return token

    def authenticate_gateway(self) -> str:
        response = self._session.post(
            self.gateway_auth_url,
            json={"identificador": os.getenv("GATEWAY_USUARIO"), "senha": os.getenv("GATEWAY_SENHA")},
            headers={"Content-Type": "application/json"},
            cert=(os.getenv("PATH_CRT_FILE"), os.getenv("PATH_KEY_FILE")),
        )
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            raise GatewayAuthError(detail="Gateway não retornou token")
        return token

    def _fetch_token(self) -> str:
        if self.connection_mode == "APIM":
            return self.authenticate_apim()
        return self.authenticate_gateway()

    def get_token(self) -> str:
        return self._cache.get_or_refresh(self._fetch_token)
