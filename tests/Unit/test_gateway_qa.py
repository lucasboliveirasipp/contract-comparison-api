from unittest.mock import MagicMock, patch


def _auth():
    auth = MagicMock()
    auth.qa_url = "https://qa"
    auth.get_token.return_value = "tok"
    return auth


@patch("src.services.gateway.qa.request_json")
def test_ask_question_posts_payload_to_chats_questions(mock_req):
    from src.services.gateway.qa import ask_question
    mock_req.return_value = {"answer": "olá"}
    payload = {"question": "Resumo?"}

    out = ask_question(payload, _auth())

    assert out == {"answer": "olá"}
    args, kwargs = mock_req.call_args
    assert args == ("POST", "https://qa/chats/questions", "tok")
    assert kwargs["json"] == payload
