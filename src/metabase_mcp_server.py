from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastmcp import FastMCP

from infrastructure.config import parse_configuration
from infrastructure.logging import setup_logging
from adapters.outbound.metabase import AiohttpMetabaseGateway
from application.services import (
    CollectionService,
    CardService,
    DashboardService,
    DatabaseService,
    UserService,
    GroupService,
    DatasetService,
)
from adapters.inbound.mcp import (
    register_collection_tools,
    register_card_tools,
    register_dashboard_tools,
    register_database_tools,
    register_user_tools,
    register_group_tools,
    register_dataset_tools,
)

# --- Configuration & logging ---
config = parse_configuration()
logger = setup_logging(config.log_level)

# --- Outbound adapter (driven side) ---
gateway = AiohttpMetabaseGateway(config.metabase_url, config.metabase_api_key)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage the gateway's HTTP session lifecycle."""
    try:
        await gateway.connect()
        yield
    except Exception as e:
        logger.error(f"Error during session initialization: {str(e)}")
        raise
    finally:
        await gateway.close()


# --- MCP server (inbound side) ---
mcp = FastMCP("metabase", lifespan=app_lifespan)

# --- Wire services and register tools ---
register_collection_tools(mcp, CollectionService(gateway))
register_card_tools(mcp, CardService(gateway))
register_dashboard_tools(mcp, DashboardService(gateway))
register_database_tools(mcp, DatabaseService(gateway))
register_user_tools(mcp, UserService(gateway))
register_group_tools(mcp, GroupService(gateway))
register_dataset_tools(mcp, DatasetService(gateway))


if __name__ == "__main__":
    logger.info(f"Starting Metabase MCP Server on {config.host}:{config.port}")
    logger.info(f"Using transport: {config.transport}")
    logger.info(f"Connecting to Metabase at {config.metabase_url}")

    if config.transport == "stdio":
        mcp.run(transport=config.transport)
    else:
        mcp.run(host=config.host, port=config.port, transport=config.transport)
