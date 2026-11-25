from unittest.mock import MagicMock, patch


def _auth():
    auth = MagicMock()
    auth.file_manager_url = "https://fm"
    auth.get_token.return_value = "tok"
    return auth


@patch("src.services.gateway.filemanager.request_json")
def test_upload_file_builds_url_token_and_multipart(mock_req):
    from src.services.gateway.filemanager import upload_file
    mock_req.return_value = {"file_id": "abc", "container": "cont"}

    out = upload_file("contrato.pdf", b"bytes", "contratos-juridico", _auth())

    assert out == {"file_id": "abc", "container": "cont"}
    args, kwargs = mock_req.call_args
    assert args == ("POST", "https://fm/files/upload", "tok")
    assert kwargs["files"]["file"][0] == "contrato.pdf"
    assert kwargs["files"]["file"][1] == b"bytes"
    assert kwargs["data"]["container_name"] == "contratos-juridico"


@patch("src.services.gateway.filemanager.request_json")
def test_upload_file_passes_token_from_auth(mock_req):
    from src.services.gateway.filemanager import upload_file
    mock_req.return_value = {}
    auth = _auth()

    upload_file("a.pdf", b"x", "c", auth)

    auth.get_token.assert_called_once()
