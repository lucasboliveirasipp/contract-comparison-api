from unittest.mock import MagicMock, patch


def _auth():
    auth = MagicMock()
    auth.workflow_request_url = "https://wf"
    auth.get_token.return_value = "tok"
    return auth


@patch("src.services.gateway.workflow_request.request_json")
def test_start_workflow_posts_payload_to_start_url(mock_req):
    from src.services.gateway.workflow_request import start_workflow
    mock_req.return_value = {"workflow_execution_id": "exec-1"}
    payload = {"workflow_configuration_code": "CD_X"}

    out = start_workflow(payload, _auth())

    assert out == {"workflow_execution_id": "exec-1"}
    args, kwargs = mock_req.call_args
    assert args == ("POST", "https://wf/request/start-workflow", "tok")
    assert kwargs["json"] == payload


@patch("src.services.gateway.workflow_request.request_json")
def test_get_workflow_status_gets_status_url_with_exec_id(mock_req):
    from src.services.gateway.workflow_request import get_workflow_status
    mock_req.return_value = {"status": "SUCCESS"}

    out = get_workflow_status("exec-1", _auth())

    assert out == {"status": "SUCCESS"}
    args, _ = mock_req.call_args
    assert args == ("GET", "https://wf/request/workflow-status/exec-1", "tok")
