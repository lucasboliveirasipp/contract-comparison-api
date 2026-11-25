from fastapi.testclient import TestClient

from src.main import app
from src.services.core.errors import GatewayError, GatewayUnavailableError


# rota temporária só para exercitar o handler registrado em main.py
@app.get("/_raise_unavailable")
def _raise_unavailable():
    raise GatewayUnavailableError(detail="segredo-interno")


@app.get("/_raise_generic")
def _raise_generic():
    raise GatewayError(502, "Falha no serviço de destino.", detail="stacktrace")


client = TestClient(app)


def test_gateway_error_maps_to_status_code():
    resp = client.get("/_raise_unavailable")
    assert resp.status_code == 503


def test_gateway_error_returns_generic_message_without_detail():
    resp = client.get("/_raise_unavailable")
    body = resp.json()
    assert body == {"message": "Serviço temporariamente indisponível. Tente novamente."}
    assert "segredo-interno" not in resp.text  # L6: detail nunca vaza ao cliente


def test_generic_gateway_error_uses_its_status_and_message():
    resp = client.get("/_raise_generic")
    assert resp.status_code == 502
    assert resp.json() == {"message": "Falha no serviço de destino."}
