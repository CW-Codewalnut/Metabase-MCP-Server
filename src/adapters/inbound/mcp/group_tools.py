from typing import Any, Dict, Optional

from fastmcp import FastMCP

from application.services import GroupService


def register_group_tools(mcp: FastMCP, service: GroupService) -> None:
    @mcp.tool()
    async def get_metabase_groups() -> Dict[str, Any]:
        """
        Get a list of groups (roles) in Metabase.

        Returns:
            Dict[str, Any]: Group metadata including id, name, etc.
        """
        return await service.list_groups()

    @mcp.tool()
    async def create_metabase_group(
        name: str,
        ldap_dn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new group (role) in Metabase.

        Args:
            name (str): Name of the group to create.
            ldap_dn (str, optional): LDAP Distinguished Name if applicable.

        Returns:
            Dict[str, Any]: Created group metadata.
        """
        return await service.create(name=name, ldap_dn=ldap_dn)

    @mcp.tool()
    async def delete_metabase_group(group_id: int) -> Dict[str, Any]:
        """
        Delete a group (role) from Metabase.

        Args:
            group_id (int): ID of the group to delete.

        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        return await service.delete(group_id)
