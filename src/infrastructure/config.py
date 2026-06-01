import os
import argparse
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

TransportType = Literal["stdio", "streamable-http"]
LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


@dataclass(frozen=True)
class Configuration:
    """Type-safe configuration container."""
    host: str
    port: int
    transport: TransportType
    log_level: LogLevelType
    metabase_url: str
    metabase_api_key: str

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not isinstance(self.port, int) or self.port <= 0:
            raise ValueError(f"Port must be a positive integer, got {self.port}")

        if not self.metabase_url:
            raise ValueError("Metabase URL is required")

        if not self.metabase_api_key:
            raise ValueError("Metabase API key is required")


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
        default=os.getenv("LOG_LEVEL", "DEBUG"),
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
