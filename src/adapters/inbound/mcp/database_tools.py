from typing import Any, Dict, Optional

from fastmcp import FastMCP

from application.services import DatabaseService


def register_database_tools(mcp: FastMCP, service: DatabaseService) -> None:
    @mcp.tool()
    async def get_metabase_databases() -> Dict[str, Any]:
        """
        Get a list of connected databases in Metabase.

        Returns:
            Dict[str, Any]: List of database metadata.
        """
        return await service.list_databases()

    @mcp.tool()
    async def create_metabase_database(
        name: str,
        engine: str,
        details: Dict[str, Any],
        auto_run_queries: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        is_full_sync: Optional[bool] = None,
        schedule: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        metadata_sync: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Create a new database connection in Metabase.

        Args:
            name (str): Name of the database.
            engine (str): Database engine.
            details (Dict[str, Any]): Connection details.
            auto_run_queries (bool, optional): Enable auto run.
            cache_ttl (int, optional): Cache time-to-live.
            is_full_sync (bool, optional): Whether to perform full sync.
            schedule (Dict[str, Any], optional): Sync schedule.
            timezone (str, optional): Timezone for the database.
            metadata_sync (bool, optional): Enable metadata sync.

        Returns:
            Dict[str, Any]: Created database metadata.
        """
        return await service.create(
            name=name,
            engine=engine,
            details=details,
            auto_run_queries=auto_run_queries,
            cache_ttl=cache_ttl,
            is_full_sync=is_full_sync,
            schedule=schedule,
            timezone=timezone,
            metadata_sync=metadata_sync,
        )

    @mcp.tool()
    async def update_metabase_database(
        database_id: int,
        name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        auto_run_queries: Optional[bool] = None,
        cache_ttl: Optional[int] = None,
        is_full_sync: Optional[bool] = None,
        schedule: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        metadata_sync: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing database connection in Metabase.

        Args:
            database_id (int): ID of the database to update.
            name (str, optional): Name of the database.
            details (Dict[str, Any], optional): Connection details.
            auto_run_queries (bool, optional): Enable auto run.
            cache_ttl (int, optional): Cache time-to-live.
            is_full_sync (bool, optional): Whether to perform full sync.
            schedule (Dict[str, Any], optional): Sync schedule.
            timezone (str, optional): Timezone for the database.
            metadata_sync (bool, optional): Enable metadata sync.

        Returns:
            Dict[str, Any]: Updated database metadata.
        """
        return await service.update(
            database_id=database_id,
            name=name,
            details=details,
            auto_run_queries=auto_run_queries,
            cache_ttl=cache_ttl,
            is_full_sync=is_full_sync,
            schedule=schedule,
            timezone=timezone,
            metadata_sync=metadata_sync,
        )

    @mcp.tool()
    async def delete_metabase_database(database_id: int) -> Dict[str, Any]:
        """
        Delete a database connection from Metabase.

        Args:
            database_id (int): ID of the database to delete.

        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        return await service.delete(database_id)
