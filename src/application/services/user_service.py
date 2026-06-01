import logging
from typing import Any, Dict, List, Optional

from application.ports.metabase_gateway import MetabaseGateway

logger = logging.getLogger("metabase-mcp")


class UserService:
    """Use cases for Metabase users (`/api/user`)."""

    def __init__(self, gateway: MetabaseGateway) -> None:
        self._gw = gateway

    async def list_users(self) -> Dict[str, Any]:
        return await self._gw.get("/api/user")

    async def create(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        login_attributes: Optional[Dict[str, Any]] = None,
        group_ids: Optional[List] = None,
        is_superuser: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
        }
        if login_attributes is not None:
            payload["login_attributes"] = login_attributes
        if group_ids is not None:
            payload["group_ids"] = group_ids
        if is_superuser is not None:
            payload["is_superuser"] = is_superuser

        logger.info(f"Creating user '{email}'")
        return await self._gw.post("/api/user", json=payload)

    async def update(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        login_attributes: Optional[Dict[str, Any]] = None,
        group_ids: Optional[List] = None,
        is_superuser: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if email is not None:
            payload["email"] = email
        if password is not None:
            payload["password"] = password
        if login_attributes is not None:
            payload["login_attributes"] = login_attributes
        if group_ids is not None:
            payload["group_ids"] = group_ids
        if is_superuser is not None:
            payload["is_superuser"] = is_superuser

        logger.info(f"Updating user {user_id}")
        return await self._gw.put(f"/api/user/{user_id}", json=payload)

    async def delete(self, user_id: int) -> Dict[str, Any]:
        logger.info(f"Deleting user {user_id}")
        return await self._gw.delete(f"/api/user/{user_id}")

    async def current(self) -> Dict[str, Any]:
        logger.info("Getting current user info")
        return await self._gw.get("/api/user/current")
