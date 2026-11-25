from unittest.mock import MagicMock, patch

import pytest

from src.services.core.errors import GatewayError, GatewayTimeoutError, MalformedGatewayResponseError


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("WORKFLOW_CODE_VERSOES", "WF_VERSOES")
    monkeypatch.setenv("UPLOAD_CONTAINER", "contratos-juridico")
    monkeypatch.setenv("WORKFLOW_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("WORKFLOW_POLL_INTERVAL", "0")


def _ok_status():
    return {
        "status": "SUCCESS",
        "result": {
            "modifications": [{"type": "alteracao", "risk_level": "alto"}],
            "summary": {"total_modifications": 1, "high_risk_count": 1, "overall_risk": "alto"},
        },
    }


def _patches():
    """Patcha as dependências externas do service. Retorna o dict de mocks."""
    p = {
        "auth": patch("src.services.juridico_service.Autenticator"),
        "upload": patch("src.services.juridico_service.upload_file"),
        "start": patch("src.services.juridico_service.start_workflow"),
        "status": patch("src.services.juridico_service.get_workflow_status"),
        "save": patch("src.services.juridico_service.save_analysis"),
        "sleep": patch("src.services.juridico_service.time.sleep"),
    }
    mocks = {k: v.start() for k, v in p.items()}
    mocks["upload"].return_value = {"file_id": "f1", "container": "cont-123"}
    mocks["start"].return_value = {"workflow_execution_id": "exec-1"}
    mocks["status"].return_value = _ok_status()
    mocks["save"].return_value = "saved-id"
    return p, mocks


def _stop(p):
    for v in p.values():
        v.stop()


def test_comparar_versoes_happy_path(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    try:
        result = comparar_versoes_service(b"orig", "orig.pdf", b"mod", "mod.pdf", "APIM")
    finally:
        _stop(p)

    assert result.id == "saved-id"
    assert result.modifications[0].risk_level == "alto"
    assert result.summary.total_modifications == 1
    assert mocks["upload"].call_count == 2          # original + modificado
    mocks["auth"].assert_called_once_with("APIM")   # connection_mode repassado
    mocks["save"].assert_called_once()


def test_comparar_versoes_builds_payload_with_file_refs(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    try:
        comparar_versoes_service(b"orig", "orig.pdf", b"mod", "mod.pdf", "APIM")
    finally:
        _stop(p)

    payload = mocks["start"].call_args.args[0]
    assert payload["workflow_configuration_code"] == "WF_VERSOES"
    props = payload["input_collection"]["input_properties"][0]["workflow_step_properties"]
    by_path = {p_["full_path"]: p_["actual_value"] for p_ in props}
    assert by_path["files_id"] == ["f1", "f1"]   # 2 uploads
    assert by_path["container"] == "cont-123"


def test_comparar_versoes_malformed_result_raises(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {"status": "SUCCESS", "result": {"sem": "modifications"}}
    try:
        with pytest.raises(MalformedGatewayResponseError):
            comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)


def test_comparar_versoes_timeout_when_never_terminal(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {"status": "RUNNING"}
    try:
        with pytest.raises(GatewayTimeoutError):
            comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)


def test_comparar_versoes_workflow_error_state_raises(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {"status": "FAILED"}
    try:
        with pytest.raises(GatewayError):
            comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)


def test_comparar_versoes_invalid_field_raises_malformed(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    # risk_level inválido → ValidationError do Pydantic → MalformedGatewayResponseError
    mocks["status"].return_value = {
        "status": "SUCCESS",
        "result": {"modifications": [{"type": "alteracao", "risk_level": "critico"}]},
    }
    try:
        with pytest.raises(MalformedGatewayResponseError):
            comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)


def test_comparar_versoes_accepts_result_as_json_string(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {
        "status": "DONE",
        "result": '{"modifications": [{"type": "remocao"}], "summary": {"total_modifications": 1}}',
    }
    try:
        result = comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)
    assert result.modifications[0].type == "remocao"


def test_comparar_versoes_accepts_modifications_at_top_level(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {"status": "COMPLETED", "modifications": []}
    try:
        result = comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)
    assert result.modifications == []


def test_comparar_versoes_invalid_json_string_raises_malformed(env):
    from src.services.juridico_service import comparar_versoes_service
    p, mocks = _patches()
    mocks["status"].return_value = {"status": "SUCCESS", "result": "{nao eh json valido"}
    try:
        with pytest.raises(MalformedGatewayResponseError):
            comparar_versoes_service(b"o", "o.pdf", b"m", "m.pdf", "APIM")
    finally:
        _stop(p)


# --- Fase 2: Padrão Ouro vs Contratada --------------------------------------

@pytest.fixture
def env_po(monkeypatch):
    monkeypatch.setenv("UPLOAD_CONTAINER", "contratos-juridico")
    monkeypatch.setenv("AGENT_CODE_JURIDICO", "AG_JURIDICO")
    monkeypatch.setenv("AGENT_VERSION", "1")
    monkeypatch.setenv("PADRAO_OURO_INDEX", "idx-padrao-ouro-juridico")


def _patches_po():
    p = {
        "auth": patch("src.services.juridico_service.Autenticator"),
        "upload": patch("src.services.juridico_service.upload_file"),
        "call_agent": patch("src.services.juridico_service.call_agent"),
        "save": patch("src.services.juridico_service.save_analysis"),
    }
    mocks = {k: v.start() for k, v in p.items()}
    mocks["upload"].return_value = {"file_id": "f1", "container": "cont-123"}
    mocks["call_agent"].return_value = {"analise_markdown": "# Análise\nPonto de atenção."}
    mocks["save"].return_value = "saved-id"
    return p, mocks


def test_comparar_padrao_ouro_happy_path(env_po):
    from src.services.juridico_service import comparar_padrao_ouro_service
    p, mocks = _patches_po()
    try:
        result = comparar_padrao_ouro_service(b"padrao", "padrao.pdf", b"contratada", "contratada.pdf", "APIM")
    finally:
        _stop(p)

    assert result.id == "saved-id"
    assert result.analise_markdown == "# Análise\nPonto de atenção."
    assert result.indice_utilizado == "idx-padrao-ouro-juridico"
    assert mocks["upload"].call_count == 2
    mocks["auth"].assert_called_once_with("APIM")
    mocks["call_agent"].assert_called_once()
    mocks["save"].assert_called_once()


def test_comparar_padrao_ouro_calls_agent_with_code_version_and_refs(env_po):
    from src.services.juridico_service import comparar_padrao_ouro_service
    p, mocks = _patches_po()
    try:
        comparar_padrao_ouro_service(b"padrao", "padrao.pdf", b"contratada", "contratada.pdf", "APIM")
    finally:
        _stop(p)

    args, _ = mocks["call_agent"].call_args
    code, version, payload, _auth = args
    assert code == "AG_JURIDICO"
    assert version == "1"
    assert payload["files_id"] == ["f1", "f1"]
    assert payload["index"] == "idx-padrao-ouro-juridico"


def test_comparar_padrao_ouro_missing_markdown_raises_malformed(env_po):
    from src.services.juridico_service import comparar_padrao_ouro_service
    p, mocks = _patches_po()
    mocks["call_agent"].return_value = {"sem": "markdown"}
    try:
        with pytest.raises(MalformedGatewayResponseError):
            comparar_padrao_ouro_service(b"p", "p.pdf", b"c", "c.pdf", "APIM")
    finally:
        _stop(p)
