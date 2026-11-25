from unittest.mock import patch

import pytest

from src.services.core.errors import MalformedGatewayResponseError


@pytest.fixture
def qa_env(monkeypatch):
    monkeypatch.setenv("QA_DB_NAME", "genai-qa")
    monkeypatch.setenv("QA_DB_CONTAINER", "chat")
    monkeypatch.setenv("QA_WORKFLOW_CODE", "WF_QA_SYNC")
    monkeypatch.setenv("QA_STEP_WORKFLOW_CODE", "STEP_QA")


def _patches():
    p = {
        "auth": patch("src.services.juridico_service.Autenticator"),
        "ask": patch("src.services.juridico_service.ask_question"),
    }
    mocks = {k: v.start() for k, v in p.items()}
    mocks["ask"].return_value = {"answer": "A cláusula trata de prazo."}
    return p, mocks


def _stop(p):
    for v in p.values():
        v.stop()


def test_chat_happy_path_returns_chat_response(qa_env):
    from src.services.juridico_service import chat_analise_service
    p, mocks = _patches()
    try:
        result = chat_analise_service("O que diz a cláusula 3?", None, "APIM")
    finally:
        _stop(p)

    assert result.resposta == "A cláusula trata de prazo."
    mocks["auth"].assert_called_once_with("APIM")


def test_chat_builds_qa_payload_from_env_and_question(qa_env):
    from src.services.juridico_service import chat_analise_service
    p, mocks = _patches()
    try:
        chat_analise_service("Pergunta X", None, "APIM")
    finally:
        _stop(p)

    payload = mocks["ask"].call_args.args[0]
    assert payload["db_name"] == "genai-qa"
    assert payload["db_container"] == "chat"
    assert payload["workflow_code"] == "WF_QA_SYNC"
    assert payload["step_workflow_code"] == "STEP_QA"
    assert payload["question"] == "Pergunta X"


def test_chat_extracts_answer_from_alternative_key(qa_env):
    from src.services.juridico_service import chat_analise_service
    p, mocks = _patches()
    mocks["ask"].return_value = {"resposta": "via chave resposta"}
    try:
        result = chat_analise_service("q", None, "APIM")
    finally:
        _stop(p)
    assert result.resposta == "via chave resposta"


def test_chat_passes_through_id_contexto(qa_env):
    from src.services.juridico_service import chat_analise_service
    p, mocks = _patches()
    try:
        result = chat_analise_service("q", "ctx-123", "APIM")
    finally:
        _stop(p)
    assert result.id_contexto == "ctx-123"


def test_chat_malformed_response_raises(qa_env):
    from src.services.juridico_service import chat_analise_service
    p, mocks = _patches()
    mocks["ask"].return_value = {"sem": "resposta reconhecivel"}
    try:
        with pytest.raises(MalformedGatewayResponseError):
            chat_analise_service("q", None, "APIM")
    finally:
        _stop(p)
