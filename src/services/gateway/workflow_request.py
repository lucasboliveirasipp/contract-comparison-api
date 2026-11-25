"""Microserviço Workflow-Request da Gateway — dispara e consulta workflows.

Shape do payload de start-workflow em assets/gateway-payloads (skill bff-gateway):
input_collection.input_properties[].workflow_step_properties[] = {full_path, actual_value}.
"""

from src.services.core.client import request_json


def start_workflow(payload, auth):
    """Dispara um workflow; devolve o JSON (contém o workflow_execution_id)."""
    url = f"{auth.workflow_request_url}/request/start-workflow"
    return request_json("POST", url, auth.get_token(), json=payload)


def get_workflow_status(execution_id, auth):
    """Consulta status/resultado de um workflow (usado em polling)."""
    url = f"{auth.workflow_request_url}/request/workflow-status/{execution_id}"
    return request_json("GET", url, auth.get_token())
