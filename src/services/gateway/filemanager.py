"""Microserviço FileManager da Gateway — upload de arquivos.

Função fina; recebe o Autenticator. Toda chamada passa por request_json (L7/L8/L11).
"""

from src.services.core.client import request_json


def upload_file(file_name, file_bytes, container, auth):
    """Sobe um arquivo e devolve o JSON com id do arquivo / container."""
    url = f"{auth.file_manager_url}/files/upload"
    files = {"file": (file_name, file_bytes)}
    data = {"container_name": container, "create_container": True, "overwrite": False}
    return request_json("POST", url, auth.get_token(), data=data, files=files)
