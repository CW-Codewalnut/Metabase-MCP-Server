import logging
from typing import Any, Dict, List, Optional

from application.ports.metabase_gateway import MetabaseGateway

logger = logging.getLogger("metabase-mcp")


class DatasetService:
    """Use cases for ad-hoc query execution (`/api/dataset`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def execute_sql_query(
        self,
        database_id: int,
        query: str,
        parameters: Optional[List] = None,
        template_tags: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        native: Dict[str, Any] = {"query": query}
        if template_tags is not None:
            native["template-tags"] = template_tags

        query_payload = {
            "database": database_id,
            "type": "native",
            "native": native,
            "parameters": parameters or [],
        }
        logger.info(f"Executing SQL query on database {database_id}")
        logger.debug(f"Query: {query[:100]}...")
        return await self._gw.post("/api/dataset", json=query_payload)
