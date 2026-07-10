from dataclasses import dataclass
from typing import Literal

TransportType = Literal["stdio", "sse", "streamable-http"]
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
    allow_write_tools: bool
    allow_admin_tools: bool
    allow_sql_tool: bool
    
    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not isinstance(self.port, int) or self.port <= 0:
            raise ValueError(f"Port must be a positive integer, got {self.port}")
        
        if not self.metabase_url:
            raise ValueError("Metabase URL is required")
        
        if not self.metabase_api_key:
            raise ValueError("Metabase API key is required")
