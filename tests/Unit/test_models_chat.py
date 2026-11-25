import pytest
from pydantic import ValidationError


def test_chat_request_requires_pergunta():
    from src.models.requests import ChatRequest
    with pytest.raises(ValidationError):
        ChatRequest()


def test_chat_request_valid_with_optional_context():
    from src.models.requests import ChatRequest
    req = ChatRequest(pergunta="O que diz a cláusula 3?")
    assert req.pergunta == "O que diz a cláusula 3?"
    assert req.id_contexto is None

    req2 = ChatRequest(pergunta="x", id_contexto="abc")
    assert req2.id_contexto == "abc"


def test_chat_response_requires_resposta():
    from src.models.responses import ChatResponse
    with pytest.raises(ValidationError):
        ChatResponse()


def test_chat_response_valid():
    from src.models.responses import ChatResponse
    resp = ChatResponse(resposta="A cláusula 3 trata de...")
    assert resp.resposta == "A cláusula 3 trata de..."
    assert resp.id_contexto is None
