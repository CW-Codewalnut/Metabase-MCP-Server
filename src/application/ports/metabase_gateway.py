from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class MetabaseGateway(Protocol):
    """
    Outbound port: an abstraction over HTTP access to the Metabase REST API.

    The application layer (services) depends only on this interface, never on a
    concrete HTTP client. Implementations live in adapters/outbound. Every method
    returns the parsed JSON response normalized to a dict (lists are wrapped as
    {"data": [...], "count": n} for MCP compatibility).
    """

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Issue a GET request to `endpoint`."""
        ...

    async def post(
        self,
        endpoint: str,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Issue a POST request to `endpoint` with an optional JSON body."""
        ...

    async def put(self, endpoint: str, json: Any = None) -> Dict[str, Any]:
        """Issue a PUT request to `endpoint` with an optional JSON body."""
        ...

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Issue a DELETE request to `endpoint`."""
        ...
