import pytest

from src.services.core.errors import (
    GatewayError,
    GatewayTimeoutError,
    GatewayUnavailableError,
    GatewayAuthError,
    MalformedGatewayResponseError,
)


def test_gateway_error_keeps_detail_for_log_separate_from_client_message():
    err = GatewayError(status_code=502, client_message="Falha no gateway", detail="stack interno")
    # L6: detalhe interno não vaza para o cliente
    assert err.status_code == 502
    assert err.client_message == "Falha no gateway"
    assert err.detail == "stack interno"
    assert "stack interno" not in err.client_message


def test_timeout_maps_to_504_with_generic_message():
    err = GatewayTimeoutError(detail="connect timeout filemanager")
    assert err.status_code == 504
    assert "tempo" in err.client_message.lower()


def test_unavailable_maps_to_503():
    err = GatewayUnavailableError(detail="upstream 503")
    assert err.status_code == 503


def test_auth_error_maps_to_502():
    err = GatewayAuthError(detail="token nulo")
    assert err.status_code == 502


def test_malformed_response_maps_to_502():
    err = MalformedGatewayResponseError(detail="json invalido")
    assert err.status_code == 502


def test_subclasses_are_gateway_errors():
    assert issubclass(GatewayTimeoutError, GatewayError)
    assert isinstance(GatewayAuthError(detail="x"), GatewayError)
