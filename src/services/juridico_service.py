"""Orquestração do fluxo Original vs Modificado (Fase 1).

upload (x2) → start_workflow → polling → parse tolerante → persist → modelo.

Shapes da Gateway ainda a confirmar no SASE (Risco #3 do plano): extração de
execution_id, estado terminal e do JSON de resultado são tolerantes; ao integrar,
ajustar aqui — NÃO nos modelos.
"""

import json
import os
import time

from pydantic import ValidationError

from src.services.core.authenticator import Autenticator
from src.services.core.errors import (
    GatewayError,
    GatewayTimeoutError,
    MalformedGatewayResponseError,
)
from src.services.gateway.filemanager import upload_file
from src.services.gateway.workflow_request import start_workflow, get_workflow_status
from src.services.gateway.qa import ask_question
from src.services.gateway.orchestrator_agent import call_agent
from src.services.persistence_service import save_analysis
from src.models.responses import (
    ComparacaoVersoesResponse,
    ChatResponse,
    AnalisePadraoOuroResponse,
)

ANSWER_KEYS = ("answer", "resposta", "response", "content", "message", "output", "text")
MARKDOWN_KEYS = ("analise_markdown", "markdown", "answer", "resposta", "content", "output", "text")

TERMINAL_OK = {"SUCCESS", "SUCCEEDED", "COMPLETED", "DONE", "FINISHED"}
TERMINAL_ERR = {"FAILED", "FAILURE", "ERROR", "CANCELLED", "CANCELED"}


def comparar_versoes_service(original_bytes, original_name, modificado_bytes, modificado_name, connection_mode="APIM"):
    auth = Autenticator(connection_mode)
    container = os.environ["UPLOAD_CONTAINER"]

    up_orig = upload_file(original_name, original_bytes, container, auth)
    up_mod = upload_file(modificado_name, modificado_bytes, container, auth)
    file_ids = [_file_id(up_orig), _file_id(up_mod)]
    gateway_container = _container_ref(up_orig) or container

    payload = _build_workflow_payload(file_ids, gateway_container)
    started = start_workflow(payload, auth)
    status_json = _poll_workflow(_execution_id(started), auth)

    analysis = _extract_analysis(status_json)
    try:
        model = ComparacaoVersoesResponse(**analysis)
    except ValidationError as e:
        raise MalformedGatewayResponseError(detail=str(e))

    model.id = save_analysis(model.model_dump(exclude={"id"}))
    return model


def _file_id(upload_json):
    return upload_json.get("file_id") or upload_json.get("id")


def _container_ref(upload_json):
    return upload_json.get("container") or upload_json.get("container_id")


def _execution_id(start_json):
    return (
        start_json.get("workflow_execution_id")
        or start_json.get("execution_id")
        or start_json.get("id")
    )


def _build_workflow_payload(file_ids, container):
    return {
        "workflow_configuration_code": os.environ["WORKFLOW_CODE_VERSOES"],
        "input_collection": {
            "input_properties": [
                {
                    "workflow_step_order": 0,
                    "workflow_step_properties": [
                        {"full_path": "files_id", "actual_value": file_ids},
                        {"full_path": "container", "actual_value": container},
                        # input_text="" segue o payload real de workflow-de-arquivos da
                        # Gateway (fixture gateway_ocr_payload.json). Confirmar no SASE.
                        {"full_path": "input_text", "actual_value": ""},
                    ],
                }
            ]
        },
    }


def _state_of(status_json):
    raw = status_json.get("status") or status_json.get("state") or ""
    return str(raw).upper()


def _poll_workflow(execution_id, auth):
    max_attempts = int(os.getenv("WORKFLOW_MAX_ATTEMPTS", "30"))
    interval = float(os.getenv("WORKFLOW_POLL_INTERVAL", "2"))
    for _ in range(max_attempts):
        status_json = get_workflow_status(execution_id, auth)
        state = _state_of(status_json)
        if state in TERMINAL_OK:
            return status_json
        if state in TERMINAL_ERR:
            raise GatewayError(502, "Falha no serviço de destino.", detail=f"workflow {state}")
        time.sleep(interval)
    raise GatewayTimeoutError(detail="workflow não concluiu no tempo limite")


def _extract_analysis(status_json):
    candidate = None
    for key in ("result", "output", "data", "response", "analysis"):
        if key in status_json:
            candidate = status_json[key]
            break
    if candidate is None:
        candidate = status_json  # talvez modifications no topo
    if isinstance(candidate, str):
        try:
            candidate = json.loads(candidate)
        except ValueError as e:
            raise MalformedGatewayResponseError(detail=str(e))
    if not isinstance(candidate, dict) or "modifications" not in candidate:
        raise MalformedGatewayResponseError(detail="resultado sem 'modifications'")
    return candidate


# --- Fase 3A: Chat de análise (workflow QA síncrono) -----------------------
def chat_analise_service(pergunta, id_contexto=None, connection_mode="APIM"):
    """Envia a pergunta ao workflow QA (síncrono) e devolve a resposta natural.

    O histórico da conversa é mantido na Gateway (db_name/db_container). O workflow
    QA é SYNC: a resposta volta na própria chamada, sem polling.
    """
    auth = Autenticator(connection_mode)
    payload = {
        "db_name": os.environ["QA_DB_NAME"],
        "db_container": os.environ["QA_DB_CONTAINER"],
        "workflow_code": os.environ["QA_WORKFLOW_CODE"],
        "step_workflow_code": os.getenv("QA_STEP_WORKFLOW_CODE", ""),
        "question": pergunta,
    }
    # id_contexto: mapeamento exato no payload QA a confirmar no SASE; por ora,
    # repassado apenas à resposta para o cliente correlacionar a conversa.
    raw = ask_question(payload, auth)
    return ChatResponse(resposta=_extract_answer(raw), id_contexto=id_contexto)


def _extract_answer(qa_json):
    if isinstance(qa_json, dict):
        for key in ANSWER_KEYS:
            value = qa_json.get(key)
            if isinstance(value, str) and value.strip():
                return value
    raise MalformedGatewayResponseError(detail="resposta do QA sem texto reconhecível")


# --- Fase 2: Padrão Ouro vs Contratada --------------------------------------
def comparar_padrao_ouro_service(
    padrao_bytes, padrao_name, contratada_bytes, contratada_name, connection_mode="APIM"
):
    """Upload dos 2 contratos → call_agent (retrieval semântico na Gateway) → shaping.

    Decisão de design: invocação do agente isolada em `call_agent` (ver
    Seção "Decisão a confirmar" do plano) para trocar por `start_workflow` sem
    tocar neste service, caso o fluxo seja publicado como workflow no SASE.
    """
    auth = Autenticator(connection_mode)
    container = os.environ["UPLOAD_CONTAINER"]
    index = os.environ["PADRAO_OURO_INDEX"]

    up_padrao = upload_file(padrao_name, padrao_bytes, container, auth)
    up_contratada = upload_file(contratada_name, contratada_bytes, container, auth)
    file_ids = [_file_id(up_padrao), _file_id(up_contratada)]

    payload = {"files_id": file_ids, "index": index}
    raw = call_agent(
        os.environ["AGENT_CODE_JURIDICO"], os.environ["AGENT_VERSION"], payload, auth
    )

    model = AnalisePadraoOuroResponse(
        analise_markdown=_extract_markdown(raw), indice_utilizado=index
    )
    model.id = save_analysis(model.model_dump(exclude={"id"}))
    return model


def _extract_markdown(agent_json):
    if isinstance(agent_json, dict):
        for key in MARKDOWN_KEYS:
            value = agent_json.get(key)
            if isinstance(value, str) and value.strip():
                return value
    raise MalformedGatewayResponseError(detail="resposta do agente sem markdown reconhecível")
