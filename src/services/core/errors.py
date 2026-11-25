"""Exceções tipadas da integração com a Gateway.

L3: erros viram exceção tipada (não `None`), convertida em HTTP pelo handler em main.
L6: a mensagem ao cliente é genérica; o detalhe interno fica só em `detail` (para log).
"""


class GatewayError(Exception):
    """Erro base de integração com a Gateway."""

    def __init__(self, status_code: int, client_message: str, detail: str = ""):
        self.status_code = status_code
        self.client_message = client_message
        self.detail = detail
        super().__init__(detail or client_message)


class GatewayTimeoutError(GatewayError):
    def __init__(self, detail: str = ""):
        super().__init__(
            status_code=504,
            client_message="Tempo de resposta excedido. Tente novamente.",
            detail=detail,
        )


class GatewayUnavailableError(GatewayError):
    def __init__(self, detail: str = ""):
        super().__init__(
            status_code=503,
            client_message="Serviço temporariamente indisponível. Tente novamente.",
            detail=detail,
        )


class GatewayAuthError(GatewayError):
    def __init__(self, detail: str = ""):
        super().__init__(
            status_code=502,
            client_message="Falha ao autenticar no serviço de destino.",
            detail=detail,
        )


class MalformedGatewayResponseError(GatewayError):
    def __init__(self, detail: str = ""):
        super().__init__(
            status_code=502,
            client_message="Resposta inválida do serviço de destino.",
            detail=detail,
        )
