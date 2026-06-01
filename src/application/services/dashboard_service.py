import logging
from typing import Any, Dict, List, Optional

from application.ports.metabase_gateway import MetabaseGateway
from domain.models import DashboardCard, DashboardTab, EmbeddingParams

logger = logging.getLogger("metabase-mcp")


class DashboardService:
    """Use cases for Metabase dashboards (`/api/dashboard`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def list_dashboards(self) -> Dict[str, Any]:
        return await self._gw.get("/api/dashboard")

    async def get_by_id(self, dashboard_id: int) -> Dict[str, Any]:
        return await self._gw.get(f"/api/dashboard/{dashboard_id}")

    async def get_cards(self, dashboard_id: int) -> Dict[str, Any]:
        """
        There is no `GET /api/dashboard/:id/cards` endpoint; the dashcards live
        inside the dashboard object, so fetch the dashboard and return them.
        """
        dashboard = await self._gw.get(f"/api/dashboard/{dashboard_id}")
        dashcards = dashboard.get("dashcards", [])
        return {"data": dashcards, "count": len(dashcards)}

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        collection_id: Optional[int] = None,
        parameters: Optional[List] = None,
        tabs: Optional[List[Dict[str, str]]] = None,
        cache_ttl: Optional[int] = None,
        collection_position: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if parameters is not None:
            payload["parameters"] = parameters
        if tabs is not None:
            payload["tabs"] = tabs
        if cache_ttl is not None:
            payload["cache_ttl"] = cache_ttl
        if collection_position is not None:
            payload["collection_position"] = collection_position

        logger.info(f"Creating dashboard '{name}'")
        return await self._gw.post("/api/dashboard", json=payload)

    async def update(
        self,
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
        show_in_getting_started: Optional[bool] = None,
    ) -> Dict[str, Any]:
        # Fetch current dashboard to fall back for dashcards and tabs.
        existing_dashboard = await self._gw.get(f"/api/dashboard/{dashboard_id}")

        payload: Dict[str, Any] = {}

        payload["name"] = name if name is not None else existing_dashboard.get("name")
        payload["description"] = description if description is not None else existing_dashboard.get("description")
        payload["collection_id"] = collection_id if collection_id is not None else existing_dashboard.get("collection_id")
        payload["parameters"] = parameters if parameters is not None else existing_dashboard.get("parameters", [])

        payload["tabs"] = [t.__dict__ for t in tabs] if tabs is not None else existing_dashboard.get("tabs", [])

        if dashcards is not None:
            # Drop None-valued fields (e.g. dashboard_tab_id / inline_parameters on
            # dashboards without tabs) so we don't send nulls Metabase doesn't expect.
            # `series` ([]) and `visualization_settings` ({}) are kept intentionally.
            payload["dashcards"] = [
                {k: v for k, v in d.__dict__.items() if v is not None} for d in dashcards
            ]
        else:
            payload["dashcards"] = existing_dashboard.get("dashcards", [])

        if points_of_interest is not None:
            payload["points_of_interest"] = points_of_interest
        if caveats is not None:
            payload["caveats"] = caveats
        if enable_embedding is not None:
            payload["enable_embedding"] = enable_embedding
        else:
            payload["enable_embedding"] = existing_dashboard.get("enable_embedding", False)

        if embedding_params is not None:
            payload["embedding_params"] = {
                k: v for k, v in embedding_params.__dict__.items() if v is not None
            }
        else:
            payload["embedding_params"] = existing_dashboard.get("embedding_params", {})

        payload["archived"] = archived if archived is not None else existing_dashboard.get("archived", False)
        payload["position"] = position if position is not None else existing_dashboard.get("position", 0)
        payload["collection_position"] = collection_position if collection_position is not None else existing_dashboard.get("collection_position", 0)
        payload["cache_ttl"] = cache_ttl if cache_ttl is not None else existing_dashboard.get("cache_ttl", 0)

        if width is not None:
            if width not in ["fixed", "full"]:
                raise ValueError("width must be either 'fixed' or 'full'")
            payload["width"] = width
        else:
            payload["width"] = existing_dashboard.get("width", "fixed")

        payload["show_in_getting_started"] = show_in_getting_started if show_in_getting_started is not None else existing_dashboard.get("show_in_getting_started", False)

        logger.info(f"Updating dashboard {dashboard_id}")
        return await self._gw.put(f"/api/dashboard/{dashboard_id}", json=payload)

    async def delete(self, dashboard_id: int) -> Dict[str, Any]:
        logger.info(f"Deleting dashboard {dashboard_id}")
        return await self._gw.delete(f"/api/dashboard/{dashboard_id}")

    async def copy(
        self,
        from_dashboard_id: int,
        name: str,
        description: Optional[str] = None,
        collection_id: Optional[int] = None,
        is_deep_copy: bool = False,
        collection_position: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if is_deep_copy is not None:
            payload["is_deep_copy"] = is_deep_copy
        if collection_position is not None:
            payload["collection_position"] = collection_position

        logger.info(f"Copying dashboard {from_dashboard_id} to '{name}'")
        return await self._gw.post(f"/api/dashboard/{from_dashboard_id}/copy", json=payload)
