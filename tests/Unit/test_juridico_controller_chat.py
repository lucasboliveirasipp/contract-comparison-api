from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app
from src.models.responses import ChatResponse
from src.services.core.errors import GatewayUnavailableError

client = TestClient(app)


def test_chat_analise_returns_200_with_answer():
    fake = ChatResponse(resposta="A cláusula 3 trata de prazo.", id_contexto="ctx-1")
    with patch("src.controllers.juridico_controller.chat_analise_service", return_value=fake) as svc:
        resp = client.post("/chat/analise", json={"pergunta": "O que diz a cláusula 3?", "id_contexto": "ctx-1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["resposta"] == "A cláusula 3 trata de prazo."
    assert body["id_contexto"] == "ctx-1"
    # pergunta e id_contexto repassados ao service
    args = svc.call_args.args
    assert "O que diz a cláusula 3?" in args
    assert "ctx-1" in args


def test_chat_analise_requires_pergunta():
    resp = client.post("/chat/analise", json={})
    assert resp.status_code == 422  # validação Pydantic (L4)


def test_chat_analise_maps_gateway_error_to_status():
    with patch(
        "src.controllers.juridico_controller.chat_analise_service",
        side_effect=GatewayUnavailableError(detail="down"),
    ):
        resp = client.post("/chat/analise", json={"pergunta": "x"})
    assert resp.status_code == 503
    assert resp.json() == {"message": "Serviço temporariamente indisponível. Tente novamente."}
