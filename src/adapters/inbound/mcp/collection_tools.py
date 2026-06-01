from typing import Any, Dict, Optional

from fastmcp import FastMCP

from application.services import CollectionService


def register_collection_tools(mcp: FastMCP, service: CollectionService) -> None:
    @mcp.tool()
    async def get_metabase_collection(collection_id: int) -> Dict[str, Any]:
        """
        Retrieve a single Metabase collection by ID.

        Args:
            collection_id (int): ID of the collection.

        Returns:
            Dict[str, Any]: Collection metadata.
        """
        return await service.get(collection_id)

    @mcp.tool()
    async def create_metabase_collection(name: str, color: Optional[str] = None, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new Metabase collection.

        Args:
            name (str): Name of the collection.
            color (str, optional): Hex color code.
            parent_id (int, optional): ID of the parent collection.

        Returns:
            Dict[str, Any]: Newly created collection metadata.
        """
        return await service.create(name=name, color=color, parent_id=parent_id)

    @mcp.tool()
    async def update_metabase_collection(collection_id: int, name: Optional[str] = None, color: Optional[str] = None, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Update an existing Metabase collection.

        Args:
            collection_id (int): ID of the collection to update.
            name (str, optional): New name.
            color (str, optional): New color.
            parent_id (int, optional): New parent collection ID.

        Returns:
            Dict[str, Any]: Updated collection metadata.
        """
        return await service.update(collection_id=collection_id, name=name, color=color, parent_id=parent_id)

    @mcp.tool()
    async def delete_metabase_collection(collection_id: int) -> Dict[str, Any]:
        """
        Delete a Metabase collection.

        Args:
            collection_id (int): ID of the collection to delete.

        Returns:
            Dict[str, Any]: Confirmation of the collection deletion.
        """
        return await service.delete(collection_id)
