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
    server.TRANSPORT = "streamable-http"
    server.ALLOW_WRITE_TOOLS = False
    server.ALLOW_ADMIN_TOOLS = False
    server.ALLOW_SQL_TOOL = False

    for tool, arguments, expected in [
        (
            server.create_metabase_collection,
            {"name": "Remote Write"},
            "Write tools are disabled",
        ),
        (
            server.create_metabase_user,
            {
                "first_name": "A",
                "last_name": "User",
                "email": "a@example.com",
                "password": "secret",
            },
            "Admin tools are disabled",
        ),
        (
            server.execute_sql_query,
            {"database_id": 1, "query": "SELECT 1"},
            "SQL tools are disabled",
        ),
    ]:
        try:
            await tool.run(arguments)
        except PermissionError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"{tool.name} should have been disabled")

    assert calls == []

    server.ALLOW_WRITE_TOOLS = True
    await server.create_metabase_collection.run({"name": "Allowed"})
    assert calls == [("POST", "/api/collection", {"name": "Allowed"})]


if __name__ == "__main__":
    asyncio.run(main())
