"""Microserviço orchestrator-agent da Gateway — invocação de agente (Fase 2).

Shape do payload é específico do agente publicado (refs de arquivos, índice
semântico a usar etc.) — montagem isolada no service, não aqui.
"""

from src.services.core.client import request_json


def call_agent(code, version, payload, auth):
    """Envia o payload ao agente `code`/`version` e devolve o JSON da resposta."""
    url = f"{auth.orchestrator_agent_url}/orchestrators/{code}/task/send"
    return request_json("POST", url, auth.get_token(), json=payload, params={"version": version})
