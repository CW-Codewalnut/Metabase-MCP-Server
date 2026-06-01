import logging
from typing import Any, Dict, Optional

from application.ports.metabase_gateway import MetabaseGateway

logger = logging.getLogger("metabase-mcp")


class DatabaseService:
    """Use cases for Metabase database connections (`/api/database`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def list_databases(self) -> Dict[str, Any]:
        return await self._gw.get("/api/database")

    async def create(
        self,
        name: str,
        engine: str,
        details: Dict[str, Any],
        auto_run_queries: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        is_full_sync: Optional[bool] = None,
        schedule: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        metadata_sync: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name,
            "engine": engine,
            "details": details,
        }
        if auto_run_queries is not None:
            payload["auto_run_queries"] = auto_run_queries
        if cache_ttl is not None:
            payload["cache_ttl"] = cache_ttl
        if is_full_sync is not None:
            payload["is_full_sync"] = is_full_sync
        if schedule is not None:
            payload["schedule"] = schedule
        if timezone is not None:
            payload["timezone"] = timezone
        if metadata_sync is not None:
            payload["metadata_sync"] = metadata_sync

        logger.info(f"Creating database '{name}'")
        return await self._gw.post("/api/database", json=payload)

    async def update(
        self,
        database_id: int,
        name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        auto_run_queries: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        is_full_sync: Optional[bool] = None,
        schedule: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        metadata_sync: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if details is not None:
            payload["details"] = details
        if auto_run_queries is not None:
            payload["auto_run_queries"] = auto_run_queries
        if cache_ttl is not None:
            payload["cache_ttl"] = cache_ttl
        if is_full_sync is not None:
            payload["is_full_sync"] = is_full_sync
        if schedule is not None:
            payload["schedule"] = schedule
        if timezone is not None:
            payload["timezone"] = timezone
        if metadata_sync is not None:
            payload["metadata_sync"] = metadata_sync

        logger.info(f"Updating database {database_id}")
        return await self._gw.put(f"/api/database/{database_id}", json=payload)

    async def delete(self, database_id: int) -> Dict[str, Any]:
        logger.info(f"Deleting database {database_id}")
        return await self._gw.delete(f"/api/database/{database_id}")
