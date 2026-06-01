import logging
from typing import Any, Dict, Optional

from application.ports.metabase_gateway import MetabaseGateway

logger = logging.getLogger("metabase-mcp")


class GroupService:
    """Use cases for Metabase permission groups/roles (`/api/permissions/group`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def list_groups(self) -> Dict[str, Any]:
        return await self._gw.get("/api/permissions/group")

    async def create(self, name: str, ldap_dn: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name}
        if ldap_dn is not None:
            payload["ldap_dn"] = ldap_dn

        logger.info(f"Creating group '{name}'")
        return await self._gw.post("/api/permissions/group", json=payload)

    async def delete(self, group_id: int) -> Dict[str, Any]:
        logger.info(f"Deleting group {group_id}")
        return await self._gw.delete(f"/api/permissions/group/{group_id}")
