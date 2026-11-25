"""Helper único de chamada HTTP à Gateway — base de TODOS os módulos services/gateway/*.

Mata L7/L8/L11/L3 de uma vez:
- L7: uma única chamada HTTP por operação.
- L8: sempre retorna `response.json()`, nunca o objeto `Response`.
- L11: cliente HTTP único reutilizável (`_session`).
- L3: qualquer falha vira exceção tipada (nunca `None`/HTTP 200 nulo).
"""

import requests

from src.services.core.http_client import LoggedSession
from src.services.core.errors import (
    GatewayError,
    GatewayTimeoutError,
    GatewayUnavailableError,
    MalformedGatewayResponseError,
)

_session = LoggedSession()  # cliente único reutilizado (L11)


def request_json(method, url, token, *, json=None, data=None, files=None, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    if json is not None and files is None:
        headers["Content-Type"] = "application/json"
    try:
        response = _session.request(
            method, url, headers=headers, json=json, data=data, files=files, params=params
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        raise GatewayTimeoutError(detail=str(e))
    except requests.exceptions.HTTPError as e:
        if response.status_code == 503:
            raise GatewayUnavailableError(detail=str(e))
        raise GatewayError(502, "Falha no serviço de destino.", detail=str(e))
    except requests.exceptions.RequestException as e:
        raise GatewayUnavailableError(detail=str(e))
    try:
        return response.json()  # L8: sempre json, nunca o Response
    except ValueError as e:
        raise MalformedGatewayResponseError(detail=str(e))
