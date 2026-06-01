import json
import logging
from typing import Any, Dict, List, Optional, Union

from application.ports.metabase_gateway import MetabaseGateway

logger = logging.getLogger("metabase-mcp")


def _normalize_visualization_settings(
    visualization_settings: Optional[Union[Dict[str, Any], str]],
) -> Dict[str, Any]:
    """Accept a dict or a JSON string and always return a dict."""
    if visualization_settings is None:
        return {}
    if isinstance(visualization_settings, str):
        try:
            return json.loads(visualization_settings)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in visualization_settings")
            raise ValueError("visualization_settings must be a valid JSON object")
    return visualization_settings


class CardService:
    """Use cases for Metabase cards/questions (`/api/card`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def list_cards(self) -> Dict[str, Any]:
        return await self._gw.get("/api/card")

    async def query_results(self, card_id: int) -> Dict[str, Any]:
        return await self._gw.post(f"/api/card/{card_id}/query")

    async def create(
        self,
        name: str,
        dataset_query: Dict[str, Any],
        display: str,
        type: str = "question",
        visualization_settings: Optional[Union[Dict[str, Any], str]] = None,
        collection_id: Optional[int] = None,
        description: Optional[str] = None,
        parameter_mappings: Optional[List] = None,
        collection_position: Optional[int] = None,
        result_metadata: Optional[List] = None,
        cache_ttl: Optional[int] = None,
        parameters: Optional[List] = None,
        dashboard_id: Optional[int] = None,
        dashboard_tab_id: Optional[int] = None,
        entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name,
            "dataset_query": dataset_query,
            "display": display,
            "type": type,
            "visualization_settings": _normalize_visualization_settings(visualization_settings),
        }
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if description is not None:
            payload["description"] = description
        if parameter_mappings is not None:
            payload["parameter_mappings"] = parameter_mappings
        if collection_position is not None:
            payload["collection_position"] = collection_position
        if result_metadata is not None:
            payload["result_metadata"] = result_metadata
        if cache_ttl is not None:
            payload["cache_ttl"] = cache_ttl
        if parameters is not None:
            payload["parameters"] = parameters
        if dashboard_id is not None:
            payload["dashboard_id"] = dashboard_id
        if dashboard_tab_id is not None:
            payload["dashboard_tab_id"] = dashboard_tab_id
        if entity_id is not None:
            payload["entity_id"] = entity_id

        logger.info(f"Creating card '{name}'")
        return await self._gw.post("/api/card", json=payload)

    async def update(
        self,
        card_id: int,
        name: Optional[str] = None,
        dataset_query: Optional[Dict[str, Any]] = None,
        display: Optional[str] = None,
        type: Optional[str] = None,
        visualization_settings: Optional[Union[Dict[str, Any], str]] = None,
        collection_id: Optional[int] = None,
        description: Optional[str] = None,
        parameter_mappings: Optional[List] = None,
        collection_position: Optional[int] = None,
        result_metadata: Optional[List] = None,
        cache_ttl: Optional[int] = None,
        parameters: Optional[List] = None,
        dashboard_id: Optional[int] = None,
        dashboard_tab_id: Optional[int] = None,
        entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if dataset_query is not None:
            payload["dataset_query"] = dataset_query
        if display is not None:
            payload["display"] = display
        if type is not None:
            payload["type"] = type
        # Preserve original behavior: visualization_settings is always set (defaults to {}).
        payload["visualization_settings"] = _normalize_visualization_settings(visualization_settings)
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if description is not None:
            payload["description"] = description
        if parameter_mappings is not None:
            payload["parameter_mappings"] = parameter_mappings
        if collection_position is not None:
            payload["collection_position"] = collection_position
        if result_metadata is not None:
            payload["result_metadata"] = result_metadata
        if cache_ttl is not None:
            payload["cache_ttl"] = cache_ttl
        if parameters is not None:
            payload["parameters"] = parameters
        if dashboard_id is not None:
            payload["dashboard_id"] = dashboard_id
        if dashboard_tab_id is not None:
            payload["dashboard_tab_id"] = dashboard_tab_id
        if entity_id is not None:
            payload["entity_id"] = entity_id

        logger.info(f"Updating card {card_id}")
        return await self._gw.put(f"/api/card/{card_id}", json=payload)

    async def delete(self, card_id: int) -> Dict[str, Any]:
        logger.info(f"Deleting card {card_id}")
        return await self._gw.delete(f"/api/card/{card_id}")
