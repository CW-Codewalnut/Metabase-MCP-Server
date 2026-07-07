import os
import logging
import aiohttp
import argparse
from yarl import URL
from dotenv import load_dotenv
from fastmcp import FastMCP
from enums.request_enum import RequestMethod
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from errors.metabase_errors import MetabaseConnectionError, MetabaseResponseError
from models import DashboardCard, DashboardTab, EmbeddingParams, Configuration, TransportType, LogLevelType

def parse_configuration() -> Configuration:
    """
    Parse configuration from command line arguments and environment variables.
    Command line arguments take precedence over environment variables.
    
    Returns:
        Configuration: A type-safe configuration object containing all settings.
        
    Raises:
        SystemExit: If required configuration is missing (via argparse.error).
    """

    # Load environment variables
    load_dotenv(override=True)
    
    parser = argparse.ArgumentParser(
        description="Metabase MCP Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add configuration arguments
    parser.add_argument(
        "--host", 
        type=str, 
        default=os.getenv("HOST", "localhost"),
        help="MCP server host (default: localhost)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=os.getenv("PORT", "3200"),
        help="MCP server port (default: 3200)"
    )
    parser.add_argument(
        "--transport", 
        type=str, 
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("TRANSPORT", "stdio"),
        help="Transport method for MCP server"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level"
    )
    parser.add_argument(
        "--metabase-url", 
        type=str, 
        default=os.getenv("METABASE_URL", "http://localhost:3000"),
        help="Metabase server URL (e.g., http://localhost:3000)"
    )
    parser.add_argument(
        "--metabase-api-key", 
        type=str, 
        default=os.getenv("METABASE_API_KEY", ""),
        help="Metabase API key"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate required configuration
    if not args.metabase_url:
        parser.error("--metabase-url is required (or set METABASE_URL environment variable)")
    if not args.metabase_api_key:
        parser.error("--metabase-api-key is required (or set METABASE_API_KEY environment variable)")
    
    # Type cast the transport and log_level to ensure they match the Literal types
    transport: TransportType = args.transport  # type: ignore
    log_level: LogLevelType = args.log_level  # type: ignore
    
    return Configuration(
        host=args.host,
        port=args.port,
        transport=transport,
        log_level=log_level,
        metabase_url=args.metabase_url,
        metabase_api_key=args.metabase_api_key
    )

# Parse configuration
config = parse_configuration()

# Set configuration variables
HOST = config.host
PORT = config.port
METABASE_URL = config.metabase_url
METABASE_API_KEY = config.metabase_api_key
TRANSPORT = config.transport
LOG_LEVEL = getattr(logging, config.log_level.upper())

session: Optional[aiohttp.ClientSession] = None

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metabase-mcp")


def ensure_dict_response(response: Any) -> Dict[str, Any]:
    """
    Ensure the response is a dictionary for FastMCP compatibility.
    If the response is a list, wrap it in a dictionary with a 'data' key.
    """
    if isinstance(response, list):
        return {"data": response, "count": len(response)}
    elif isinstance(response, dict):
        return response
    else:
        return {"data": response}

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """
    Lifecycle manager for the FastMCP application.
    Creates and manages the HTTP session with proper cleanup.
    """
    global session
    try:
        if not METABASE_URL or not METABASE_API_KEY:
            raise RuntimeError("METABASE_URL or METABASE_API_KEY environment variables are not set.")
            
        logger.info(f"Initializing connection to Metabase at {METABASE_URL}")
        session = aiohttp.ClientSession(
            base_url=URL(METABASE_URL),
            headers={
                "Content-Type": "application/json",
                "X-API-Key": METABASE_API_KEY
            }
        )
        logger.info("Session initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Error during session initialization: {str(e)}")
        raise
    finally:
        if session:
            logger.info("Closing HTTP session")
            await session.close()
            session = None

# Initialize FastMCP agent
mcp = FastMCP("metabase", lifespan=app_lifespan)

async def make_metabase_request(
    method: RequestMethod,
    endpoint: str,
    data: Optional[Dict[str, Any] | bytes] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Any = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Make a request to the Metabase API.
    
    Args:
        method: HTTP method to use (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        data: Request data (for form data)
        params: URL parameters
        json: JSON request body
        headers: Additional headers
        
    Returns:
        Dict[str, Any]: Response data
        
    Raises:
        MetabaseConnectionError: When the Metabase server is unreachable
        MetabaseResponseError: When Metabase returns a non-2xx status code
        RuntimeError: For other errors
    """
    
    if not METABASE_URL or not METABASE_API_KEY:
        raise RuntimeError("METABASE_URL or METABASE_API_KEY environment variable is not set. Metabase API requests will fail.")

    if session is None:
        raise RuntimeError("HTTP session is not initialized. Ensure app_lifespan was called.")

    try:
        request_headers = headers or {}
        
        logger.debug(f"Making {method.name} request to {METABASE_URL}{endpoint}")
        
        # Log request payload for debugging (omit sensitive info)
        if json and logger.level <= logging.DEBUG:
            sanitized_json = {**json}
            if 'password' in sanitized_json:
                sanitized_json['password'] = '********'
            logger.debug(f"Request payload: {sanitized_json}")
            
        response = await session.request(
            method=method.name,
            url=endpoint,
            timeout=aiohttp.ClientTimeout(total=30),
            headers=request_headers,
            data=data,
            params=params,
            json=json,
        )

        try:
            # Handle 500 errors with more detailed info
            if response.status >= 500:
                error_text = await response.text()
                logger.error(f"Server error {response.status}: {error_text[:200]}")
                raise MetabaseResponseError(response.status, f"Server Error: {error_text[:200]}", endpoint)
            
            response.raise_for_status()
            response_data = await response.json()
            
            # Ensure the response is a dictionary for FastMCP compatibility
            return ensure_dict_response(response_data)
            
        except aiohttp.ContentTypeError:
            # Handle empty responses or non-JSON responses
            content = await response.text()
            if not content:
                return {"data": {}}
            logger.warning(f"Received non-JSON response: {content}")
            return {"data": content}

    except aiohttp.ClientConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise MetabaseConnectionError("Metabase is unreachable. Is the Metabase server running?") from e
    except aiohttp.ClientResponseError as e:
        logger.error(f"Response error: {e.status}, {e.message}, {e.request_info.url}")
        raise MetabaseResponseError(e.status, e.message, str(e.request_info.url)) from e
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise RuntimeError(f"Request error: {str(e)}") from e

# --- Collections ---
@mcp.tool()
async def get_metabase_collection(collection_id: int) -> Dict[str, Any]:
    """
    Retrieve a single Metabase collection by ID.

    Args:
        collection_id (int): ID of the collection.

    Returns:
        Dict[str, Any]: Collection metadata.
    """
    logger.info(f"Getting collection with ID {collection_id}")
    return await make_metabase_request(RequestMethod.GET, f"/api/collection/{collection_id}")

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
    payload = {"name": name}
    if color:
        payload["color"] = color
    if parent_id:
        payload["parent_id"] = parent_id
    logger.info(f"Creating collection '{name}'")
    return await make_metabase_request(RequestMethod.POST, "/api/collection", json=payload)

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
    payload = {}
    if name:
        payload["name"] = name
    if color:
        payload["color"] = color
    if parent_id:
        payload["parent_id"] = parent_id
    logger.info(f"Updating collection {collection_id}")
    return await make_metabase_request(RequestMethod.PUT, f"/api/collection/{collection_id}", json=payload)

@mcp.tool()
async def delete_metabase_collection(collection_id: int) -> Dict[str, Any]:
    """
    Delete a Metabase collection.

    Args:
        collection_id (int): ID of the collection to delete.

    Returns:
        Dict[str, Any]: Confirmation of the collection deletion.
    """
    logger.info(f"Deleting collection {collection_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/collection/{collection_id}")

# --- Charts (Cards) ---
@mcp.tool()
async def get_metabase_cards() -> Dict[str, Any]:
    """
    Get a list of all saved questions (cards).

    Returns:
        Dict[str, Any]: Cards metadata including names, ids, collections.
    """
    logger.info("Getting all cards")
    return await make_metabase_request(RequestMethod.GET, "/api/card")

@mcp.tool()
async def get_card_query_results(card_id: int) -> Dict[str, Any]:
    """
    Get the results of a card's query.
    
    Args:
        card_id (int): ID of the card.
        
    Returns:
        Dict[str, Any]: Query result data.
    """
    logger.info(f"Getting query results for card {card_id}")
    return await make_metabase_request(RequestMethod.POST, f"/api/card/{card_id}/query")

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
            - "native": { "query": "..." }, for SQL
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

    payload = {
        "name": name,
        "dataset_query": dataset_query,
        "display": display,
        "type": type,
    }
    
    # Ensure visualization_settings is a proper dict and not a string
    if visualization_settings is not None:
        if isinstance(visualization_settings, str):
            try:
                import json
                visualization_settings = json.loads(visualization_settings)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in visualization_settings")
                raise ValueError("visualization_settings must be a valid JSON object")
        payload["visualization_settings"] = visualization_settings
    else:
        payload["visualization_settings"] = {}
        
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
    return await make_metabase_request(RequestMethod.POST, "/api/card", json=payload)

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
    payload = {}
    if name is not None:
        payload["name"] = name
    if dataset_query is not None:
        payload["dataset_query"] = dataset_query
    if display is not None:
        payload["display"] = display
    if type is not None:
        payload["type"] = type
    if visualization_settings is not None:
        if isinstance(visualization_settings, str):
            try:
                import json
                visualization_settings = json.loads(visualization_settings)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in visualization_settings")
                raise ValueError("visualization_settings must be a valid JSON object")
        payload["visualization_settings"] = visualization_settings
    else:
        payload["visualization_settings"] = {}
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
    return await make_metabase_request(RequestMethod.PUT, f"/api/card/{card_id}", json=payload)

@mcp.tool()
async def delete_metabase_card(card_id: int) -> Dict[str, Any]:
    """
    Delete a card from Metabase.

    Args:
        card_id (int): ID of the card to delete.

    Returns:
        Dict[str, Any]: Deletion confirmation.
    """
    logger.info(f"Deleting card {card_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/card/{card_id}")

# --- Dashboards ---

@mcp.tool()
async def get_metabase_dashboards() -> Dict[str, Any]:
    """
    Get a list of dashboards in Metabase.

    Returns:
        Dict[str, Any]: Dashboard metadata including id, name, and cards.
    """
    logger.info("Getting all dashboards")
    return await make_metabase_request(RequestMethod.GET, "/api/dashboard")

@mcp.tool()
async def get_dashboard_by_id(dashboard_id: int) -> Dict[str, Any]:
    """
    Get a dashboard by ID.

    Args:
        dashboard_id (int): ID of the dashboard.

    Returns:
        Dict[str, Any]: Dashboard metadata including id, name, cards, and tabs.
    """
    logger.info(f"Getting dashboard {dashboard_id}")
    return await make_metabase_request(RequestMethod.GET, f"/api/dashboard/{dashboard_id}")

@mcp.tool()
async def get_dashboard_cards(dashboard_id: int) -> Dict[str, Any]:
    """
    Get cards in a dashboard.

    Args:
        dashboard_id (int): ID of the dashboard.

    Returns:
        Dict[str, Any]: Cards in the dashboard.
    """
    logger.info(f"Getting cards for dashboard {dashboard_id}")
    return await make_metabase_request(RequestMethod.GET, f"/api/dashboard/{dashboard_id}/cards")

@mcp.tool()
async def get_dashboard_items(dashboard_id: int) -> Dict[str, Any]:
    """
    Get all items in a dashboard.

    Args:
        dashboard_id (int): ID of the dashboard.

    Returns:
        Dict[str, Any]: All items in the dashboard.
    """
    logger.info(f"Getting items for dashboard {dashboard_id}")
    return await make_metabase_request(RequestMethod.GET, f"/api/dashboard/{dashboard_id}/items")

@mcp.tool()
async def create_metabase_dashboard(
    name: str,
    description: Optional[str] = None,
    collection_id: Optional[int] = None,
    parameters: Optional[List] = None,
    tabs: Optional[List[Dict[str, str]]] = None,
    cache_ttl: Optional[int] = None,
    collection_position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new dashboard in Metabase.

    Args:
        name (str): Name of the dashboard.
        description (str, optional): Dashboard description.
        collection_id (int, optional): Collection ID.
        parameters (list, optional): Parameters for the dashboard.
        tabs (list, optional): Tabs for the dashboard (list of {"name": "Tab Name"}).
        cache_ttl (int, optional): Cache time to live in seconds.
        collection_position (int, optional): Position in the collection.

    Returns:
        Dict[str, Any]: Created dashboard metadata.
    """
    payload = {
        "name": name,
    }
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
    return await make_metabase_request(RequestMethod.POST, "/api/dashboard", json=payload)

@mcp.tool()
async def update_metabase_dashboard(
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
    show_in_getting_started: Optional[bool] = None
) -> Dict[str, Any]:
   
    """
    Update an existing dashboard in Metabase using structured inputs and auto-fallback behavior.

    This function allows partial updates to a dashboard. If you don't pass optional fields like
    `dashcards` or `tabs`, the current values from the existing dashboard will be fetched and reused.

    Args:
        dashboard_id (int):
            The ID of the dashboard to update.

        name (str, optional):
            New name for the dashboard. If not provided, the current name will be retained.

        description (str, optional):
            Updated description for the dashboard.

        collection_id (int, optional):
            ID of the collection (folder) to move the dashboard into.
            If not provided, the existing collection is kept. However,
            if a new collection has been created,
            it is mandatory to pass the collection ID.
            Failure to do so will result in the dashboard being moved to the default collection,
            where the chart details may not exist.

        parameters (List[dict], optional):
            List of dashboard-level filters (used for interactive filtering).
            If omitted, existing parameters will be preserved.

        tabs (List[DashboardTab], optional):
            List of tabs to set on the dashboard.
            If not passed, the current tab configuration is reused.
            Each tab includes:
                - `id`: Tab ID (optional if new)
                - `name`: Display name of the tab

        dashcards (List[DashboardCard], optional):
            List of cards to place in the dashboard layout.
            If omitted, the existing card layout is retained.
            Each card requires:
                - `id`: Use negative numbers to auto generate the ids 
                    or use any unique value but,
                    it must be unique within the dashboard
                - `card_id`: ID of the saved chart
                - `row`, `col`: Grid position (top-left = 0,0)
                - `size_x`, `size_y`: Width/height in grid cells
                - `parameter_mappings`: List of filter mappings

        points_of_interest (str, optional):
            Free-text notes that appear in the dashboard as "Points of Interest".

        caveats (str, optional):
            Free-text notes that appear in the dashboard as "Caveats".

        enable_embedding (bool, optional):
            Whether to enable embedding for this dashboard.
            If omitted, the existing setting is reused.

        embedding_params (EmbeddingParams, optional):
            Optional embedding configuration. Includes:
                - `url`: Optional embed URL override
                - `custom_css`: Optional custom styling

        archived (bool, optional):
            Whether to archive the dashboard. Defaults to existing value if omitted.

        position (int, optional):
            Optional global ordering value (affects dashboard listing).

        collection_position (int, optional):
            Sort order inside its collection folder.

        cache_ttl (int, optional):
            Result caching time in seconds (e.g., 3600 = 1 hour). 0 disables caching.

        width (str, optional):
            Dashboard layout mode: "fixed" (grid) or "full" (fluid width).
            Defaults to existing setting if omitted.

        show_in_getting_started (bool, optional):
            Whether to show this dashboard in Metabase’s “Getting Started” view.

    Returns:
        Dict[str, Any]:
            JSON object containing updated dashboard metadata from Metabase.
            Includes fields like:
            - `id`, `name`, `description`
            - `dashcards`, `tabs`, `parameters`
            - `updated_at`, `created_at`, etc.

    Behavior:
        - If `dashcards` is omitted, the existing layout will be preserved.
        - If `dashcards` are passed without an `id`, `id = -1` will be set automatically.
        - If `tabs` are omitted, current dashboard tabs are reused.
        - All unspecified fields fall back to the dashboard's current value.

    Example:
        >>> await update_metabase_dashboard(
                dashboard_id=1,
                name="Updated Flight Dashboard",
                dashcards=[
                    DashboardCard(card_id=123, row=0, col=0, size_x=4, size_y=3),
                    DashboardCard(card_id=124, row=0, col=4, size_x=4, size_y=3)
                ],
                tabs=[DashboardTab(name="Overview")],
                width="fixed"
            )
    """


    # 🧱 Fetch current dashboard to fallback for dashcards and tabs
    existing_dashboard = await make_metabase_request(RequestMethod.GET, f"/api/dashboard/{dashboard_id}")

    payload = {}

    payload["name"] = name if name is not None else existing_dashboard.get("name")
    payload["description"] = description if description is not None else existing_dashboard.get("description")
    payload["collection_id"] = collection_id if collection_id is not None else existing_dashboard.get("collection_id")
    payload["parameters"] = parameters if parameters is not None else existing_dashboard.get("parameters", [])

    payload["tabs"] = [t.__dict__ for t in tabs] if tabs is not None else existing_dashboard.get("tabs", [])

    if dashcards is not None:
        payload["dashcards"] = [d.__dict__ for d in dashcards]
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
    return await make_metabase_request(RequestMethod.PUT, f"/api/dashboard/{dashboard_id}", json=payload)

@mcp.tool()
async def delete_metabase_dashboard(dashboard_id: int) -> Dict[str, Any]:
    """
    Delete a dashboard from Metabase.

    Args:
        dashboard_id (int): ID of the dashboard to delete.

    Returns:
        Dict[str, Any]: Deletion confirmation.
    """
    logger.info(f"Deleting dashboard {dashboard_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/dashboard/{dashboard_id}")

@mcp.tool()
async def copy_metabase_dashboard(
    from_dashboard_id: int,
    name: str,
    description: Optional[str] = None,
    collection_id: Optional[int] = None,
    is_deep_copy: bool = False,
    collection_position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Copy a dashboard.

    Args:
        from_dashboard_id (int): ID of the source dashboard to copy.
        name (str): Name for the new dashboard.
        description (str, optional): Description for the new dashboard.
        collection_id (int, optional): Collection ID for the new dashboard.
        is_deep_copy (bool, optional): Whether to perform a deep copy (copy linked cards too).
        collection_position (int, optional): Position in the collection.

    Returns:
        Dict[str, Any]: New dashboard metadata.
    """
    payload = {
        "name": name,
    }
    if description is not None:
        payload["description"] = description
    if collection_id is not None:
        payload["collection_id"] = collection_id
    if is_deep_copy is not None:
        payload["is_deep_copy"] = is_deep_copy
    if collection_position is not None:
        payload["collection_position"] = collection_position

    logger.info(f"Copying dashboard {from_dashboard_id} to '{name}'")
    return await make_metabase_request(
        RequestMethod.POST,
        f"/api/dashboard/{from_dashboard_id}/copy",
        json=payload
    )

# --- Databases ---

@mcp.tool()
async def get_metabase_databases() -> Dict[str, Any]:
    """
    Get a list of connected databases in Metabase.

    Returns:
        Dict[str, Any]: List of database metadata.
    """
    logger.info("Getting all databases")
    return await make_metabase_request(RequestMethod.GET, "/api/database")

@mcp.tool()
async def create_metabase_database(
    name: str,
    engine: str,
    details: Dict[str, Any],
    auto_run_queries: Optional[bool] = None,
    cache_ttl: Optional[int] = None,
    is_full_sync: Optional[bool] = None,
    schedule: Optional[Dict[str, Any]] = None,
    timezone: Optional[str] = None,
    metadata_sync: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Create a new database connection in Metabase.

    Args:
        name (str): Name of the database.
        engine (str): Database engine.
        details (Dict[str, Any]): Connection details.
        auto_run_queries (bool, optional): Enable auto run.
        cache_ttl (int, optional): Cache time-to-live.
        is_full_sync (bool, optional): Whether to perform full sync.
        schedule (Dict[str, Any], optional): Sync schedule.
        timezone (str, optional): Timezone for the database.
        metadata_sync (bool, optional): Enable metadata sync.

    Returns:
        Dict[str, Any]: Created database metadata.
    """
    payload = {
        "name": name,
        "engine": engine,
        "details": details
    }
    if auto_run_queries is not None:
        payload["auto_run_queries"] = auto_run_queries
    if cache_ttl is not None:
        payload["cache_ttl"] = cache_ttl
    if is_full_sync is not None:
        payload["is_full_sync"] = is_full_sync
    if schedule is not None:
        payload["schedule"] = schedule
    if timezone is not None:
        payload["timezone"] = timezone
    if metadata_sync is not None:
        payload["metadata_sync"] = metadata_sync

    logger.info(f"Creating database '{name}'")
    return await make_metabase_request(RequestMethod.POST, "/api/database", json=payload)

@mcp.tool()
async def update_metabase_database(
    database_id: int,
    name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    auto_run_queries: Optional[bool] = None,
    cache_ttl: Optional[int] = None,
    is_full_sync: Optional[bool] = None,
    schedule: Optional[Dict[str, Any]] = None,
    timezone: Optional[str] = None,
    metadata_sync: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing database connection in Metabase.

    Args:
        database_id (int): ID of the database to update.
        name (str, optional): Name of the database.
        details (Dict[str, Any], optional): Connection details.
        auto_run_queries (bool, optional): Enable auto run.
        cache_ttl (int, optional): Cache time-to-live.
        is_full_sync (bool, optional): Whether to perform full sync.
        schedule (Dict[str, Any], optional): Sync schedule.
        timezone (str, optional): Timezone for the database.
        metadata_sync (bool, optional): Enable metadata sync.

    Returns:
        Dict[str, Any]: Updated database metadata.
    """
    payload = {}
    if name is not None:
        payload["name"] = name
    if details is not None:
        payload["details"] = details
    if auto_run_queries is not None:
        payload["auto_run_queries"] = auto_run_queries
    if cache_ttl is not None:
        payload["cache_ttl"] = cache_ttl
    if is_full_sync is not None:
        payload["is_full_sync"] = is_full_sync
    if schedule is not None:
        payload["schedule"] = schedule
    if timezone is not None:
        payload["timezone"] = timezone
    if metadata_sync is not None:
        payload["metadata_sync"] = metadata_sync

    logger.info(f"Updating database {database_id}")
    return await make_metabase_request(RequestMethod.PUT, f"/api/database/{database_id}", json=payload)

@mcp.tool()
async def delete_metabase_database(database_id: int) -> Dict[str, Any]:
    """
    Delete a database connection from Metabase.

    Args:
        database_id (int): ID of the database to delete.

    Returns:
        Dict[str, Any]: Deletion confirmation.
    """
    logger.info(f"Deleting database {database_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/database/{database_id}")

# --- Users ---
@mcp.tool()
async def get_metabase_users() -> Dict[str, Any]:
    """
    Get a list of users in Metabase.

    Returns:
        Dict[str, Any]: User metadata including id, email, groups, etc.
    """
    logger.info("Getting all users")
    return await make_metabase_request(RequestMethod.GET, "/api/user")

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
    payload = {
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
    return await make_metabase_request(RequestMethod.POST, "/api/user", json=payload)


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
    payload = {}
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
    return await make_metabase_request(RequestMethod.PUT, f"/api/user/{user_id}", json=payload)


@mcp.tool()
async def delete_metabase_user(user_id: int) -> Dict[str, Any]:
    """
    Delete a user from Metabase.

    Args:
        user_id (int): ID of the user to delete.

    Returns:
        Dict[str, Any]: Deletion confirmation.
    """
    logger.info(f"Deleting user {user_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/user/{user_id}")

@mcp.tool()
async def get_metabase_current_user() -> Dict[str, Any]:
    """
    Get current logged-in user info from Metabase.

    Returns:
        Dict[str, Any]: User details like id, email, groups, etc.
    """
    logger.info("Getting current user info")
    return await make_metabase_request(RequestMethod.GET, "/api/user/current")

# --- Groups (Roles) ---
@mcp.tool()
async def get_metabase_groups() -> Dict[str, Any]:
    """
    Get a list of groups (roles) in Metabase.

    Returns:
        Dict[str, Any]: Group metadata including id, name, etc.
    """
    logger.info("Getting all groups")
    return await make_metabase_request(RequestMethod.GET, "/api/permissions/group")

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
    payload = {"name": name}
    if ldap_dn is not None:
        payload["ldap_dn"] = ldap_dn

    logger.info(f"Creating group '{name}'")
    return await make_metabase_request(RequestMethod.POST, "/api/permissions/group", json=payload)

@mcp.tool()
async def delete_metabase_group(group_id: int) -> Dict[str, Any]:
    """
    Delete a group (role) from Metabase.

    Args:
        group_id (int): ID of the group to delete.

    Returns:
        Dict[str, Any]: Deletion confirmation.
    """
    logger.info(f"Deleting group {group_id}")
    return await make_metabase_request(RequestMethod.DELETE, f"/api/permissions/group/{group_id}")

# --- SQL queries (native queries through card creation) ---
@mcp.tool()
async def execute_sql_query(
    database_id: int,
    query: str,
    parameters: Optional[List] = None
) -> Dict[str, Any]:
    """
    Execute a native SQL query through Metabase.

    Args:
        database_id (int): ID of the database to execute the query on.
        native_query (str): The SQL query to execute.
        parameters (list, optional): Query parameters.

    Returns:
        Dict[str, Any]: Query execution result.
        
    Notes:
        - For PostgreSQL databases, column names are be case-sensitive
        - Use double quotes around column names with mixed case (e.g., "columnName")
        - Example with quoted column names: 
          SELECT "userId", "orderDate", COUNT(*) FROM "Orders" GROUP BY "userId", "orderDate"
    """
    query_payload = {
        "database": database_id,
        "type": "native",
        "native": {"query": query},
        "parameters": parameters or []
    }
    logger.info(f"Executing SQL query on database {database_id}")
    logger.debug(f"Query: {query[:100]}...")
    return await make_metabase_request(RequestMethod.POST, "/api/dataset", json=query_payload)


if __name__ == "__main__":
    # Start the MCP server with configuration from arguments/environment
    logger.info(f"Starting Metabase MCP Server on {HOST}:{PORT}")
    logger.info(f"Using transport: {TRANSPORT}")
    logger.info(f"Connecting to Metabase at {METABASE_URL}")
    
    # Start the MCP server
    if(TRANSPORT == "stdio"):
        mcp.run(transport=TRANSPORT)
    else:
        mcp.run(host=HOST, port=PORT, transport=TRANSPORT) 
