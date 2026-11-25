from unittest.mock import MagicMock

import pytest
import requests

from src.services.core import client
from src.services.core.errors import (
    GatewayError,
    GatewayTimeoutError,
    GatewayUnavailableError,
    MalformedGatewayResponseError,
)


def _fake_response(status_code=200, json_value=None, json_exc=None, raise_for_status_exc=None):
    resp = MagicMock(status_code=status_code)
    if raise_for_status_exc is not None:
        resp.raise_for_status.side_effect = raise_for_status_exc
    else:
        resp.raise_for_status.return_value = None
    if json_exc is not None:
        resp.json.side_effect = json_exc
    else:
        resp.json.return_value = json_value
    return resp


# --- L8: sucesso devolve o dict do json (nunca o Response) ---

def test_request_json_returns_dict_on_success(monkeypatch):
    resp = _fake_response(json_value={"ok": True})
    monkeypatch.setattr(client._session, "request", MagicMock(return_value=resp))

    result = client.request_json("GET", "https://x", "tok")

    assert result == {"ok": True}


# --- monta o header Authorization a partir do token ---

def test_request_json_builds_authorization_header_from_token(monkeypatch):
    resp = _fake_response(json_value={})
    mock_request = MagicMock(return_value=resp)
    monkeypatch.setattr(client._session, "request", mock_request)

    client.request_json("POST", "https://x", "meu-token", json={"a": 1})

    _, kwargs = mock_request.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer meu-token"
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_request_json_omits_content_type_for_multipart(monkeypatch):
    resp = _fake_response(json_value={})
    mock_request = MagicMock(return_value=resp)
    monkeypatch.setattr(client._session, "request", mock_request)

    client.request_json("POST", "https://x", "tok", files={"file": ("a.pdf", b"x")})

    _, kwargs = mock_request.call_args
    assert "Content-Type" not in kwargs["headers"]


# --- L3: cada falha vira a exceção tipada certa ---

def test_request_json_timeout_raises_gateway_timeout(monkeypatch):
    monkeypatch.setattr(
        client._session, "request",
        MagicMock(side_effect=requests.exceptions.Timeout("t")),
    )
    with pytest.raises(GatewayTimeoutError):
        client.request_json("GET", "https://x", "tok")


def test_request_json_http_503_raises_unavailable(monkeypatch):
    resp = _fake_response(
        status_code=503,
        raise_for_status_exc=requests.exceptions.HTTPError("503"),
    )
    monkeypatch.setattr(client._session, "request", MagicMock(return_value=resp))
    with pytest.raises(GatewayUnavailableError):
        client.request_json("GET", "https://x", "tok")


def test_request_json_http_500_raises_gateway_error_502(monkeypatch):
    resp = _fake_response(
        status_code=500,
        raise_for_status_exc=requests.exceptions.HTTPError("500"),
    )
    monkeypatch.setattr(client._session, "request", MagicMock(return_value=resp))
    with pytest.raises(GatewayError) as exc:
        client.request_json("GET", "https://x", "tok")
    assert exc.value.status_code == 502


def test_request_json_connection_error_raises_unavailable(monkeypatch):
    monkeypatch.setattr(
        client._session, "request",
        MagicMock(side_effect=requests.exceptions.ConnectionError("down")),
    )
    with pytest.raises(GatewayUnavailableError):
        client.request_json("GET", "https://x", "tok")


def test_request_json_invalid_json_raises_malformed(monkeypatch):
    resp = _fake_response(json_exc=ValueError("no json"))
    monkeypatch.setattr(client._session, "request", MagicMock(return_value=resp))
    with pytest.raises(MalformedGatewayResponseError):
        client.request_json("GET", "https://x", "tok")
