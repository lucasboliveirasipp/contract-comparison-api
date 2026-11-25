from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def cosmos_env(monkeypatch):
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://cosmos")
    monkeypatch.setenv("COSMOS_KEY", "key")
    monkeypatch.setenv("COSMOS_DATABASE", "db")
    monkeypatch.setenv("COSMOS_CONTAINER_ANALYSES", "analyses")


def _wire_container(mock_client_cls):
    container = MagicMock()
    mock_client_cls.return_value.get_database_client.return_value.get_container_client.return_value = container
    return container


@patch("src.services.persistence_service.CosmosClient")
def test_save_analysis_generates_id_and_creates_item(mock_client_cls, cosmos_env):
    from src.services.persistence_service import save_analysis
    container = _wire_container(mock_client_cls)

    new_id = save_analysis({"modifications": []})

    assert isinstance(new_id, str) and new_id
    created = container.create_item.call_args.args[0]
    assert created["id"] == new_id
    assert created["modifications"] == []


@patch("src.services.persistence_service.CosmosClient")
def test_get_analysis_returns_item(mock_client_cls, cosmos_env):
    from src.services.persistence_service import get_analysis
    container = _wire_container(mock_client_cls)
    container.read_item.return_value = {"id": "abc", "x": 1}

    assert get_analysis("abc") == {"id": "abc", "x": 1}
    container.read_item.assert_called_once_with("abc", partition_key="abc")


@patch("src.services.persistence_service.CosmosClient")
def test_get_analysis_returns_none_when_not_found(mock_client_cls, cosmos_env):
    from azure.cosmos import exceptions
    from src.services.persistence_service import get_analysis
    container = _wire_container(mock_client_cls)
    container.read_item.side_effect = exceptions.CosmosResourceNotFoundError(message="nope")

    assert get_analysis("missing") is None
