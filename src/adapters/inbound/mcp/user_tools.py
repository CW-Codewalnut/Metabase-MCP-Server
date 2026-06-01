from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from application.services import UserService


def register_user_tools(mcp: FastMCP, service: UserService) -> None:
    @mcp.tool()
    async def get_metabase_users() -> Dict[str, Any]:
        """
        Get a list of users in Metabase.

        Returns:
            Dict[str, Any]: User metadata including id, email, groups, etc.
        """
        return await service.list_users()

    @mcp.tool()
    async def create_metabase_user(
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        login_attributes: Optional[Dict[str, Any]] = None,
        group_ids: Optional[List] = None,
        is_superuser: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Create a new user in Metabase.

        Args:
            first_name (str): User's first name.
            last_name (str): User's last name.
            email (str): Email address.
            password (str): Account password.
            login_attributes (dict, optional): Additional login metadata.
            group_ids (list, optional): List of group IDs to assign the user.
            is_superuser (bool, optional): Whether the user is a superuser.

        Returns:
            Dict[str, Any]: Created user metadata.
        """
        return await service.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            login_attributes=login_attributes,
            group_ids=group_ids,
            is_superuser=is_superuser,
        )

    @mcp.tool()
    async def update_metabase_user(
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        login_attributes: Optional[Dict[str, Any]] = None,
        group_ids: Optional[List] = None,
        is_superuser: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing user in Metabase.

        Args:
            user_id (int): ID of the user to update.
            first_name (str, optional): Updated first name.
            last_name (str, optional): Updated last name.
            email (str, optional): Updated email address.
            password (str, optional): Updated password.
            login_attributes (dict, optional): Updated login metadata.
            group_ids (list, optional): Updated group IDs.
            is_superuser (bool, optional): Updated superuser flag.

        Returns:
            Dict[str, Any]: Updated user metadata.
        """
        return await service.update(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            login_attributes=login_attributes,
            group_ids=group_ids,
            is_superuser=is_superuser,
        )

    @mcp.tool()
    async def delete_metabase_user(user_id: int) -> Dict[str, Any]:
        """
        Delete a user from Metabase.

        Args:
            user_id (int): ID of the user to delete.

        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        return await service.delete(user_id)

    @mcp.tool()
    async def get_metabase_current_user() -> Dict[str, Any]:
        """
        Get current logged-in user info from Metabase.

        Returns:
            Dict[str, Any]: User details like id, email, groups, etc.
        """
        return await service.current()
