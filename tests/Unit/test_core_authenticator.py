from unittest.mock import MagicMock

import pytest

from src.services.core.authenticator import Autenticator
from src.services.core.errors import GatewayAuthError


def _fake_response(json_body):
    resp = MagicMock()
    resp.json.return_value = json_body
    resp.raise_for_status.return_value = None
    return resp


def test_rejects_invalid_connection_mode():
    with pytest.raises(ValueError):
        Autenticator("FOO")


def test_resolves_juridico_urls_by_apim_prefix(monkeypatch):
    monkeypatch.setenv("APIM_URL", "https://base")
    monkeypatch.setenv("APIM_QA_URL", "/qa/v1")
    monkeypatch.setenv("APIM_FILEMANAGER_URL", "/fm/v1")
    monkeypatch.setenv("APIM_INDEXER_URL", "/idx/v1")
    monkeypatch.setenv("APIM_ORCHESTRATOR_AGENT_URL", "/orch/v1")

    auth = Autenticator("APIM")

    assert auth.qa_url == "https://base/qa/v1"
    assert auth.file_manager_url == "https://base/fm/v1"
    assert auth.indexer_url == "https://base/idx/v1"
    assert auth.orchestrator_agent_url == "https://base/orch/v1"


def test_resolves_urls_by_gateway_prefix(monkeypatch):
    monkeypatch.setenv("GATEWAY_URL", "https://gateway")
    monkeypatch.setenv("GATEWAY_QA_URL", "/qa")
    auth = Autenticator("GATEWAY")
    assert auth.qa_url == "https://gateway/qa"


def test_missing_env_does_not_crash(monkeypatch):
    monkeypatch.delenv("APIM_URL", raising=False)
    monkeypatch.delenv("APIM_QA_URL", raising=False)
    # não deve levantar TypeError por concatenar None
    auth = Autenticator("APIM")
    assert isinstance(auth.qa_url, str)


def test_get_token_caches_within_ttl(monkeypatch):
    monkeypatch.setenv("APIM_URL", "https://base")
    auth = Autenticator("APIM")
    calls = []

    def fake_fetch():
        calls.append(1)
        return "tok-cached"

    auth._fetch_token = fake_fetch  # injeta o fetch sem rede

    assert auth.get_token() == "tok-cached"
    assert auth.get_token() == "tok-cached"
    assert len(calls) == 1  # L2: reautentica só ao expirar


def test_authenticate_apim_returns_access_token(monkeypatch):
    monkeypatch.setenv("APIM_URL", "https://base")
    auth = Autenticator("APIM")
    monkeypatch.setattr(auth._session, "post", lambda *a, **k: _fake_response({"access_token": "tok"}))
    assert auth.authenticate_apim() == "tok"


def test_authenticate_apim_raises_when_token_missing(monkeypatch):
    monkeypatch.setenv("APIM_URL", "https://base")
    auth = Autenticator("APIM")
    monkeypatch.setattr(auth._session, "post", lambda *a, **k: _fake_response({}))
    with pytest.raises(GatewayAuthError):
        auth.authenticate_apim()


def test_authenticate_gateway_returns_token(monkeypatch):
    monkeypatch.setenv("GATEWAY_URL", "https://gateway")
    auth = Autenticator("GATEWAY")
    monkeypatch.setattr(auth._session, "post", lambda *a, **k: _fake_response({"token": "btok"}))
    assert auth.authenticate_gateway() == "btok"


def test_authenticate_gateway_raises_when_token_missing(monkeypatch):
    monkeypatch.setenv("GATEWAY_URL", "https://gateway")
    auth = Autenticator("GATEWAY")
    monkeypatch.setattr(auth._session, "post", lambda *a, **k: _fake_response({}))
    with pytest.raises(GatewayAuthError):
        auth.authenticate_gateway()


def test_fetch_token_dispatches_by_mode(monkeypatch):
    monkeypatch.setenv("GATEWAY_URL", "https://gateway")
    auth = Autenticator("GATEWAY")
    monkeypatch.setattr(auth, "authenticate_gateway", lambda: "via-gateway")
    assert auth._fetch_token() == "via-gateway"
