from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP

from application.services import CardService


def register_card_tools(mcp: FastMCP, service: CardService) -> None:
    @mcp.tool()
    async def get_metabase_cards() -> Dict[str, Any]:
        """
        Get a list of all saved questions (cards).

        Returns:
            Dict[str, Any]: Cards metadata including names, ids, collections.
        """
        return await service.list_cards()

    @mcp.tool()
    async def get_card_query_results(card_id: int) -> Dict[str, Any]:
        """
        Get the results of a card's query.

        Args:
            card_id (int): ID of the card.

        Returns:
            Dict[str, Any]: Query result data.
        """
        return await service.query_results(card_id)

    @mcp.tool()
    async def create_metabase_card(
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
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new card (chart or table) in Metabase via the /api/card endpoint.

        This function creates a visual card using either SQL or MBQL queries and
        supports all chart types including pie, donut, bar, table, and KPI-style metrics.

        Args:
            name (str):
                Display name of the card in Metabase.

            dataset_query (dict):
                Defines the query behind the chart.
                Required structure:
                - "type": "native" or "query"
                - "native": { "query": "..." }, for SQL. For parameterized SQL using
                  `{{variable}}` placeholders, also include "template-tags": {...} inside
                  the "native" object (one entry per placeholder).
                - "query": {...}, for MBQL
                - "database": database ID

            display (str):
                Visualization type. Common values:
                - "table", "bar", "line", "pie", "area", "scatter", "funnel", "pivot-table", "map"

            type (str, optional):
                Card type, defaults to "question".
                - "question": general chart or table
                - "metric": for KPI display
                - "model": reserved/legacy

            visualization_settings (dict, optional):
                Controls chart appearance and formatting. Structure varies by chart type.

                ── 📊 Bar / Line / Area ──
                {
                  "graph": {
                    "x_axis": "destination",
                    "y_axis": ["seatsSold"],
                    "series": "flightType",
                    "metrics": ["seatsSold"],
                    "x_axis_label": "Destination",
                    "y_axis_label": "Seats Sold",
                    "x_axis_formatting": {
                      "scale": "ordinal",
                      "label_rotation": 45
                    },
                    "y_axis_formatting": {
                      "number_style": "decimal",
                      "suffix": " pax"
                    }
                  },
                  "show_legend": true,
                  "legend_position": "bottom"
                }

                ── 🥧 Pie / Donut Charts ──
                {
                  "pie": {
                    "category": "destination",         # Label or group for slices
                    "metric": "seatsSold",             # Size of each slice
                    "labels": true,                    # Show category names
                    "show_values": true,               # Show numeric values inside slices
                    "inner_radius": 0.6,               # Enables donut (0 = full pie)
                    "outer_radius": 0.95,              # Size scaling (0.0 to 1.0)
                    "outer_ring": true                 # Enables dual-ring charts
                  },
                  "show_legend": true,
                  "legend_position": "right"
                }

                Notes on ring options:
                  - `inner_radius` creates a donut shape. Recommended: 0.5–0.8.
                  - `outer_radius` controls the size of the entire chart area.
                  - `outer_ring` enables comparison across rings, useful when the query returns multiple groupings/metrics.

                ── 📋 Table ──
                {
                  "table.pivot_column": "flightType",
                  "column_settings": {
                    "seatsSold": {
                      "number_style": "decimal",
                      "suffix": " pax"
                    }
                  }
                }

            collection_id (int, optional):
                Save card into a specific Metabase collection (folder).

            description (str, optional):
                Description or help text for the card.

            parameter_mappings (list, optional):
                Used when linking dashboard filters to this card.
                Example:
                [
                  {
                    "parameter_id": "flightType",
                    "card_id": 123,
                    "target": ["dimension", ["template-tag", "flightType"]]
                  }
                ]

            collection_position (int, optional):
                Optional order in the collection.

            result_metadata (list, optional):
                Optional field metadata describing result set.

            cache_ttl (int, optional):
                Cache duration (in seconds). 0 disables caching.

            parameters (list, optional):
                List of query parameters for SQL or MBQL filters.
                Example: [{"name": "region", "type": "category", "slug": "region"}]

            dashboard_id (int, optional):
                Adds this card to an existing dashboard.

            dashboard_tab_id (int, optional):
                If the dashboard has tabs, specify the tab ID to attach the card to.

            entity_id (str, optional):
                External or custom ID for embedding/syncing cards.

        Returns:
            Dict[str, Any]:
                A dictionary representing the created card including:
                  - id (int)
                  - name (str)
                  - dataset_query (dict)
                  - visualization_settings (dict)
                  - created_at, updated_at, etc.

        Example:
            >>> await create_metabase_card(
                    name="Seats Sold by Destination (Donut with Outer Ring)",
                    display="pie",
                    dataset_query={
                        "type": "native",
                        "native": {
                            "query": "SELECT destination, SUM(\"seatsSold\") AS total_seats_sold FROM \"Flight\" GROUP BY destination"
                        },
                        "database": 2
                    },
                    visualization_settings={
                        "pie": {
                            "category": "destination",
                            "metric": "total_seats_sold",
                            "labels": true,
                            "inner_radius": 0.6,
                            "outer_radius": 0.95,
                            "show_values": true,
                            "outer_ring": true
                        },
                        "show_legend": true,
                        "legend_position": "right"
                    },
                    collection_id=3
                )
        """
        return await service.create(
            name=name,
            dataset_query=dataset_query,
            display=display,
            type=type,
            visualization_settings=visualization_settings,
            collection_id=collection_id,
            description=description,
            parameter_mappings=parameter_mappings,
            collection_position=collection_position,
            result_metadata=result_metadata,
            cache_ttl=cache_ttl,
            parameters=parameters,
            dashboard_id=dashboard_id,
            dashboard_tab_id=dashboard_tab_id,
            entity_id=entity_id,
        )

    @mcp.tool()
    async def update_metabase_card(
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
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing card in Metabase.

        Args:
            card_id (int): ID of the card to update.
            name (str, optional): New name of the card.
            dataset_query (Dict[str, Any], optional): Dataset query definition.
            display (str, optional): Display type.
            type (str, optional): Card type.
            visualization_settings (Dict[str, Any], optional): Visualization settings.
            collection_id (int, optional): ID of the collection.
            description (str, optional): Description of the card.
            parameter_mappings (list, optional): Parameter mappings.
            collection_position (int, optional): Position in the collection.
            result_metadata (list, optional): Metadata for results.
            cache_ttl (int, optional): Cache TTL.
            parameters (list, optional): Query parameters.
            dashboard_id (int, optional): Dashboard ID.
            dashboard_tab_id (int, optional): Dashboard tab ID.
            entity_id (str, optional): Entity ID.

        Returns:
            Dict[str, Any]: Updated card metadata.
        """
        return await service.update(
            card_id=card_id,
            name=name,
            dataset_query=dataset_query,
            display=display,
            type=type,
            visualization_settings=visualization_settings,
            collection_id=collection_id,
            description=description,
            parameter_mappings=parameter_mappings,
            collection_position=collection_position,
            result_metadata=result_metadata,
            cache_ttl=cache_ttl,
            parameters=parameters,
            dashboard_id=dashboard_id,
            dashboard_tab_id=dashboard_tab_id,
            entity_id=entity_id,
        )

    @mcp.tool()
    async def delete_metabase_card(card_id: int) -> Dict[str, Any]:
        """
        Delete a card from Metabase.

        Args:
            card_id (int): ID of the card to delete.

        Returns:
            Dict[str, Any]: Deletion confirmation.
        """
        return await service.delete(card_id)
