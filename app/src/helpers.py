from opensearchpy import AsyncOpenSearch
from config import OPENSEARCH_HOST, OPENSEARCH_PORT

import json


INDEX_CONFIG_PATH = 'index_config/index_config.json'


async def create_index(index_name: str):
    with open(INDEX_CONFIG_PATH) as file:
        cfg = json.load(file)

    async with AsyncOpenSearch(hosts=[{"host": OPENSEARCH_HOST, "port": int(OPENSEARCH_PORT)}], use_ssl=False) as client:
        if await client.indices.exists(index=index_name):
            raise ValueError(f"Index [{index_name}] has already exist")
        await client.indices.create(
            index=index_name,
            body=cfg
        )

