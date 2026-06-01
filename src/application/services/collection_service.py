from typing import Any, Dict, Optional

from application.ports.metabase_gateway import MetabaseGateway


class CollectionService:
    """Use cases for Metabase collections (`/api/collection`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def get(self, collection_id: int) -> Dict[str, Any]:
        return await self._gw.get(f"/api/collection/{collection_id}")

    async def create(
        self,
        name: str,
        color: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name}
        if color:
            payload["color"] = color
        if parent_id:
            payload["parent_id"] = parent_id
        return await self._gw.post("/api/collection", json=payload)

    async def update(
        self,
        collection_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None,
        parent_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if name:
            payload["name"] = name
        if color:
            payload["color"] = color
        if parent_id:
            payload["parent_id"] = parent_id
        return await self._gw.put(f"/api/collection/{collection_id}", json=payload)

    async def delete(self, collection_id: int) -> Dict[str, Any]:
        return await self._gw.delete(f"/api/collection/{collection_id}")
