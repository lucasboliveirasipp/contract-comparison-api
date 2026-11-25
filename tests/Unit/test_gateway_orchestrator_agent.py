from unittest.mock import MagicMock, patch


def _auth():
    auth = MagicMock()
    auth.orchestrator_agent_url = "https://agent"
    auth.get_token.return_value = "tok"
    return auth


@patch("src.services.gateway.orchestrator_agent.request_json")
def test_call_agent_posts_payload_to_task_send_with_code_and_version(mock_req):
    from src.services.gateway.orchestrator_agent import call_agent
    mock_req.return_value = {"analise_markdown": "# Análise"}
    payload = {"files_id": ["f1", "f2"], "index": "idx-padrao-ouro"}

    out = call_agent("AG_JURIDICO", 2, payload, _auth())

    assert out == {"analise_markdown": "# Análise"}
    args, kwargs = mock_req.call_args
    assert args == ("POST", "https://agent/orchestrators/AG_JURIDICO/task/send", "tok")
    assert kwargs["json"] == payload
    assert kwargs["params"] == {"version": 2}
