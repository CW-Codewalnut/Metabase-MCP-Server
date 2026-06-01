from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from application.services import DashboardService
from domain.models import DashboardCard, DashboardTab, EmbeddingParams


def register_dashboard_tools(mcp: FastMCP, service: DashboardService) -> None:
    @mcp.tool()
    async def get_metabase_dashboards() -> Dict[str, Any]:
        """
        Get a list of dashboards in Metabase.

        Returns:
            Dict[str, Any]: Dashboard metadata including id, name, and cards.
        """
        return await service.list_dashboards()

    @mcp.tool()
    async def get_dashboard_by_id(dashboard_id: int) -> Dict[str, Any]:
        """
        Get a dashboard by ID.

        Args:
            dashboard_id (int): ID of the dashboard.

        Returns:
            Dict[str, Any]: Dashboard metadata including id, name, cards, and tabs.
        """
        return await service.get_by_id(dashboard_id)

    @mcp.tool()
    async def get_dashboard_cards(dashboard_id: int) -> Dict[str, Any]:
        """
        Get the cards (dashcards) placed on a dashboard.

        Note: there is no `GET /api/dashboard/:id/cards` endpoint in the Metabase API.
        The dashcards live inside the dashboard object, so we fetch the dashboard and
        return its `dashcards` array.

        Args:
            dashboard_id (int): ID of the dashboard.

        Returns:
            Dict[str, Any]: The dashboard's dashcards (wrapped as {"data": [...], "count": n}).
        """
        return await service.get_cards(dashboard_id)

    @mcp.tool()
    async def create_metabase_dashboard(
        name: str,
        description: Optional[str] = None,
        collection_id: Optional[int] = None,
        parameters: Optional[List] = None,
        tabs: Optional[List[Dict[str, str]]] = None,
        cache_ttl: Optional[int] = None,
        collection_position: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new dashboard in Metabase.

        Args:
            name (str): Name of the dashboard.
            description (str, optional): Dashboard description.
            collection_id (int, optional): Collection ID.
            parameters (list, optional): Parameters for the dashboard.
            tabs (list, optional): Tabs for the dashboard (list of {"name": "Tab Name"}).
            cache_ttl (int, optional): Cache time to live in seconds.
            collection_position (int, optional): Position in the collection.

        Returns:
            Dict[str, Any]: Created dashboard metadata.
        """
        return await service.create(
            name=name,
            description=description,
            collection_id=collection_id,
            parameters=parameters,
            tabs=tabs,
            cache_ttl=cache_ttl,
            collection_position=collection_position,
        )

    @mcp.tool()
    async def update_metabase_dashboard(
        dashboard_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        collection_id: Optional[int] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        tabs: Optional[List[DashboardTab]] = None,
        dashcards: Optional[List[DashboardCard]] = None,
        points_of_interest: Optional[str] = None,
        caveats: Optional[str] = None,
        enable_embedding: Optional[bool] = None,
        embedding_params: Optional[EmbeddingParams] = None,
        archived: Optional[bool] = None,
        position: Optional[int] = None,
        collection_position: Optional[int] = None,
        cache_ttl: Optional[int] = None,
        width: Optional[str] = None,
        show_in_getting_started: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing dashboard in Metabase using structured inputs and auto-fallback behavior.

        This function allows partial updates to a dashboard. If you don't pass optional fields like
        `dashcards` or `tabs`, the current values from the existing dashboard will be fetched and reused.

        Args:
            dashboard_id (int):
                The ID of the dashboard to update.

            name (str, optional):
                New name for the dashboard. If not provided, the current name will be retained.

            description (str, optional):
                Updated description for the dashboard.

            collection_id (int, optional):
                ID of the collection (folder) to move the dashboard into.
                If not provided, the existing collection is kept. However,
                if a new collection has been created,
                it is mandatory to pass the collection ID.
                Failure to do so will result in the dashboard being moved to the default collection,
                where the chart details may not exist.

            parameters (List[dict], optional):
                List of dashboard-level filters (used for interactive filtering).
                If omitted, existing parameters will be preserved.

            tabs (List[DashboardTab], optional):
                List of tabs to set on the dashboard.
                If not passed, the current tab configuration is reused.
                Each tab includes:
                    - `id`: Tab ID (optional if new)
                    - `name`: Display name of the tab

            dashcards (List[DashboardCard], optional):
                List of cards to place in the dashboard layout.
                If omitted, the existing card layout is retained.
                Each card requires:
                    - `id`: Use negative numbers to auto generate the ids
                        or use any unique value but,
                        it must be unique within the dashboard
                    - `card_id`: ID of the saved chart
                    - `row`, `col`: Grid position (top-left = 0,0)
                    - `size_x`, `size_y`: Width/height in grid cells
                    - `parameter_mappings`: List of filter mappings

            points_of_interest (str, optional):
                Free-text notes that appear in the dashboard as "Points of Interest".

            caveats (str, optional):
                Free-text notes that appear in the dashboard as "Caveats".

            enable_embedding (bool, optional):
                Whether to enable embedding for this dashboard.
                If omitted, the existing setting is reused.

            embedding_params (EmbeddingParams, optional):
                Optional embedding configuration. Includes:
                    - `url`: Optional embed URL override
                    - `custom_css`: Optional custom styling

            archived (bool, optional):
                Whether to archive the dashboard. Defaults to existing value if omitted.

            position (int, optional):
                Optional global ordering value (affects dashboard listing).

            collection_position (int, optional):
                Sort order inside its collection folder.

            cache_ttl (int, optional):
                Result caching time in seconds (e.g., 3600 = 1 hour). 0 disables caching.

            width (str, optional):
                Dashboard layout mode: "fixed" (grid) or "full" (fluid width).
                Defaults to existing setting if omitted.

            show_in_getting_started (bool, optional):
                Whether to show this dashboard in Metabase’s “Getting Started” view.

        Returns:
            Dict[str, Any]:
                JSON object containing updated dashboard metadata from Metabase.
                Includes fields like:
                - `id`, `name`, `description`
                - `dashcards`, `tabs`, `parameters`
                - `updated_at`, `created_at`, etc.

        Behavior:
            - If `dashcards` is omitted, the existing layout will be preserved.
            - Each `DashboardCard` must carry an `id`; use a negative value (e.g. -1)
              for new cards so Metabase assigns the real id. None-valued optional
              fields (`dashboard_tab_id`, `inline_parameters`) are dropped before sending.
            - If `tabs` are omitted, current dashboard tabs are reused.
            - All unspecified fields fall back to the dashboard's current value.

        Example:
            >>> await update_metabase_dashboard(
                    dashboard_id=1,
                    name="Updated Flight Dashboard",
                    dashcards=[
                        DashboardCard(card_id=123, row=0, col=0, size_x=4, size_y=3),
                        DashboardCard(card_id=124, row=0, col=4, size_x=4, size_y=3)
                    ],
                    tabs=[DashboardTab(name="Overview")],
                    width="fixed"
                )
        """
        return await service.update(
            dashboard_id=dashboard_id,
            name=name,
            description=description,
            collection_id=collection_id,
            parameters=parameters,
            tabs=tabs,
            dashcards=dashcards,
            points_of_interest=points_of_interest,
            caveats=caveats,
            enable_embedding=enable_embedding,
            embedding_params=embedding_params,
            archived=archived,
            position=position,
            collection_position=collection_position,
            cache_ttl=cache_ttl,
            width=width,
            show_in_getting_started=show_in_getting_started,
        )

    @mcp.tool()
    async def delete_metabase_dashboard(dashboard_id: int) -> Dict[str, Any]:
        """
        Delete a dashboard from Metabase.

        Args:
            dashboard_id (int): ID of the dashboard to delete.

        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        return await service.delete(dashboard_id)

    @mcp.tool()
    async def copy_metabase_dashboard(
        from_dashboard_id: int,
        name: str,
        description: Optional[str] = None,
        collection_id: Optional[int] = None,
        is_deep_copy: bool = False,
        collection_position: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Copy a dashboard.

        Args:
            from_dashboard_id (int): ID of the source dashboard to copy.
            name (str): Name for the new dashboard.
            description (str, optional): Description for the new dashboard.
            collection_id (int, optional): Collection ID for the new dashboard.
            is_deep_copy (bool, optional): Whether to perform a deep copy (copy linked cards too).
            collection_position (int, optional): Position in the collection.

        Returns:
            Dict[str, Any]: New dashboard metadata.
        """
        return await service.copy(
            from_dashboard_id=from_dashboard_id,
            name=name,
            description=description,
            collection_id=collection_id,
            is_deep_copy=is_deep_copy,
            collection_position=collection_position,
        )
