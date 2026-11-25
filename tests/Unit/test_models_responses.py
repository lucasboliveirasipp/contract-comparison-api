import pytest
from pydantic import ValidationError


def test_modification_item_defaults_and_valid():
    from src.models.responses import ModificationItem
    item = ModificationItem(type="adicao")
    assert item.type == "adicao"
    assert item.risk_level == "baixo"
    assert item.original_text == ""


def test_modification_item_rejects_invalid_risk_level():
    from src.models.responses import ModificationItem
    with pytest.raises(ValidationError):
        ModificationItem(type="adicao", risk_level="critico")


def test_modification_item_rejects_invalid_type():
    from src.models.responses import ModificationItem
    with pytest.raises(ValidationError):
        ModificationItem(type="inexistente")


def test_comparacao_versoes_response_full_shape():
    from src.models.responses import ComparacaoVersoesResponse
    resp = ComparacaoVersoesResponse(
        id="abc",
        modifications=[{"type": "alteracao", "risk_level": "alto"}],
        summary={"total_modifications": 1, "high_risk_count": 1, "overall_risk": "alto"},
    )
    assert resp.id == "abc"
    assert resp.modifications[0].risk_level == "alto"
    assert resp.summary.total_modifications == 1


def test_comparacao_versoes_response_defaults_empty():
    from src.models.responses import ComparacaoVersoesResponse
    resp = ComparacaoVersoesResponse()
    assert resp.id is None
    assert resp.modifications == []
    assert resp.summary.overall_risk == "baixo"


def test_analise_padrao_ouro_response_requires_markdown():
    from src.models.responses import AnalisePadraoOuroResponse
    with pytest.raises(ValidationError):
        AnalisePadraoOuroResponse()


def test_analise_padrao_ouro_response_full_shape():
    from src.models.responses import AnalisePadraoOuroResponse
    resp = AnalisePadraoOuroResponse(
        id="abc", analise_markdown="# Análise", indice_utilizado="idx-padrao-ouro"
    )
    assert resp.id == "abc"
    assert resp.analise_markdown == "# Análise"
    assert resp.indice_utilizado == "idx-padrao-ouro"


def test_analise_padrao_ouro_response_indice_utilizado_defaults_empty():
    from src.models.responses import AnalisePadraoOuroResponse
    resp = AnalisePadraoOuroResponse(analise_markdown="# Análise")
    assert resp.id is None
    assert resp.indice_utilizado == ""
