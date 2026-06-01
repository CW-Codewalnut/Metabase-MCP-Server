import logging

from .config import LogLevelType


def setup_logging(log_level: LogLevelType) -> logging.Logger:
    """
    Configure root logging and return the application logger.

    Args:
        log_level: One of "DEBUG", "INFO", "WARNING", "ERROR".

    Returns:
        logging.Logger: The "metabase-mcp" logger.
    """
    level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("metabase-mcp")
