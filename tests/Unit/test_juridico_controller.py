from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app
from src.models.responses import AnalisePadraoOuroResponse, ComparacaoVersoesResponse
from src.services.core.errors import GatewayUnavailableError

client = TestClient(app)


def _files():
    return {"original": ("orig.pdf", b"x"), "modificado": ("mod.pdf", b"y")}


def _files_po():
    return {"padrao_ouro": ("padrao.pdf", b"x"), "contratada": ("contratada.pdf", b"y")}


def test_comparar_versoes_returns_200_with_model():
    fake = ComparacaoVersoesResponse(
        id="abc",
        modifications=[{"type": "alteracao", "risk_level": "alto"}],
        summary={"total_modifications": 1},
    )
    with patch("src.controllers.juridico_controller.comparar_versoes_service", return_value=fake):
        resp = client.post("/comparar/versoes", files=_files())

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "abc"
    assert body["modifications"][0]["risk_level"] == "alto"


def test_comparar_versoes_maps_gateway_error_to_status():
    with patch(
        "src.controllers.juridico_controller.comparar_versoes_service",
        side_effect=GatewayUnavailableError(detail="down"),
    ):
        resp = client.post("/comparar/versoes", files=_files())

    assert resp.status_code == 503
    assert resp.json() == {"message": "Serviço temporariamente indisponível. Tente novamente."}


def test_obter_analise_returns_200_when_found():
    with patch(
        "src.controllers.juridico_controller.get_analysis",
        return_value={"id": "abc", "modifications": []},
    ):
        resp = client.get("/analises/abc")

    assert resp.status_code == 200
    assert resp.json()["id"] == "abc"


def test_obter_analise_returns_404_when_missing():
    with patch("src.controllers.juridico_controller.get_analysis", return_value=None):
        resp = client.get("/analises/missing")

    assert resp.status_code == 404


def test_comparar_padrao_ouro_returns_200_with_model():
    fake = AnalisePadraoOuroResponse(
        id="abc", analise_markdown="# Análise", indice_utilizado="idx-padrao-ouro"
    )
    with patch(
        "src.controllers.juridico_controller.comparar_padrao_ouro_service", return_value=fake
    ):
        resp = client.post("/comparar/padrao-ouro", files=_files_po())

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "abc"
    assert body["analise_markdown"] == "# Análise"


def test_comparar_padrao_ouro_maps_gateway_error_to_status():
    with patch(
        "src.controllers.juridico_controller.comparar_padrao_ouro_service",
        side_effect=GatewayUnavailableError(detail="down"),
    ):
        resp = client.post("/comparar/padrao-ouro", files=_files_po())

    assert resp.status_code == 503
    assert resp.json() == {"message": "Serviço temporariamente indisponível. Tente novamente."}
