import asyncio
import os
import sys
from pathlib import Path


os.environ.setdefault("METABASE_API_KEY", "test-key")
os.environ.setdefault("LOG_LEVEL", "INFO")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import metabase_mcp_server as server  # noqa: E402


async def main():
    calls = []

    async def fake_request(method, endpoint, **kwargs):
        calls.append((method.name, endpoint, kwargs.get("json")))
        return {"ok": True}

    server.make_metabase_request = fake_request

    await server.update_metabase_card.run({"card_id": 10, "name": "Only name"})
    await server.update_metabase_collection.run(
        {"collection_id": 11, "name": "Root move", "parent_id": 0}
    )

    assert calls == [
        ("PUT", "/api/card/10", {"name": "Only name"}),
        ("PUT", "/api/collection/11", {"name": "Root move", "parent_id": 0}),
    ]


if __name__ == "__main__":
    asyncio.run(main())
