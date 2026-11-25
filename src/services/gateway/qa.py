"""Microserviço QA da Gateway — chat / pergunta-resposta (síncrono).

Shape do payload (exemplo real do Jack): db_name, db_container, workflow_code,
step_workflow_code, question. O workflow QA é SYNC → resposta na própria chamada,
sem polling. O histórico da conversa é mantido na Gateway (db_name/db_container).
"""

from src.services.core.client import request_json


def ask_question(payload, auth):
    """Envia uma pergunta ao chat/QA e devolve o JSON da resposta."""
    url = f"{auth.qa_url}/chats/questions"
    return request_json("POST", url, auth.get_token(), json=payload)
