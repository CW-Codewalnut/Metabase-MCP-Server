from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from application.services import DatasetService


def register_dataset_tools(mcp: FastMCP, service: DatasetService) -> None:
    @mcp.tool()
    async def execute_sql_query(
        database_id: int,
        query: str,
        parameters: Optional[List] = None,
        template_tags: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a native SQL query through Metabase.

        Args:
            database_id (int): ID of the database to execute the query on.
            query (str): The SQL query to execute.
            parameters (list, optional): Runtime parameter values supplied to the query.
            template_tags (dict, optional): Template tag definitions for parameterized
                SQL that uses `{{variable}}` / `[[optional]]` placeholders. Keys are the
                tag names; values describe each tag. Example:
                {
                  "region": {
                    "id": "a1b2", "name": "region", "display-name": "Region",
                    "type": "text"
                  }
                }
                Required whenever `query` contains `{{...}}` placeholders.

        Returns:
            Dict[str, Any]: Query execution result.

        Notes:
            - For PostgreSQL databases, column names are case-sensitive
            - Use double quotes around column names with mixed case (e.g., "columnName")
            - Example with quoted column names:
              SELECT "userId", "orderDate", COUNT(*) FROM "Orders" GROUP BY "userId", "orderDate"
        """
        return await service.execute_sql_query(
            database_id=database_id,
            query=query,
            parameters=parameters,
            template_tags=template_tags,
        )
