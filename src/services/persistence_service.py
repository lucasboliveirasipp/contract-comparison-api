"""Persistência das análises no Azure Cosmos DB.

Config por env (L12). Testes mockam CosmosClient (patch em persistence_service.CosmosClient).
"""

import os
import uuid

from azure.cosmos import CosmosClient, exceptions


def _container(env_name: str):
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])
    db = client.get_database_client(os.environ["COSMOS_DATABASE"])
    return db.get_container_client(os.environ[env_name])


def save_analysis(analysis: dict) -> str:
    item = {"id": str(uuid.uuid4()), **analysis}
    _container("COSMOS_CONTAINER_ANALYSES").create_item(item)
    return item["id"]


def get_analysis(analysis_id: str) -> dict | None:
    try:
        return _container("COSMOS_CONTAINER_ANALYSES").read_item(
            analysis_id, partition_key=analysis_id
        )
    except exceptions.CosmosResourceNotFoundError:
        return None
