import logging
from typing import Any, Dict, Optional

import aiohttp
from yarl import URL

from domain.errors import MetabaseConnectionError, MetabaseResponseError

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


class AiohttpMetabaseGateway:
    """
    Outbound adapter implementing the MetabaseGateway port over aiohttp.

    Owns the HTTP session lifecycle (connect/close) and centralizes request
    execution, error mapping and response normalization. The Metabase API key is
    sent on every request via the `X-API-Key` header.
    """

    def __init__(self, metabase_url: str, metabase_api_key: str) -> None:
        self._metabase_url = metabase_url
        self._metabase_api_key = metabase_api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Create the underlying HTTP session. Called from the server lifespan."""
        if not self._metabase_url or not self._metabase_api_key:
            raise RuntimeError("METABASE_URL or METABASE_API_KEY is not set.")

        logger.info(f"Initializing connection to Metabase at {self._metabase_url}")
        self._session = aiohttp.ClientSession(
            base_url=URL(self._metabase_url),
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self._metabase_api_key,
            },
        )
        logger.info("Session initialized successfully")

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session:
            logger.info("Closing HTTP session")
            await self._session.close()
            self._session = None

    # --- Public port methods ---

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self._request("POST", endpoint, json=json, params=params)

    async def put(self, endpoint: str, json: Any = None) -> Dict[str, Any]:
        return await self._request("PUT", endpoint, json=json)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        return await self._request("DELETE", endpoint)

    # --- Internal ---

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request against the Metabase API.

        Raises:
            MetabaseConnectionError: When the Metabase server is unreachable
            MetabaseResponseError: When Metabase returns a non-2xx status code
            RuntimeError: For other errors
        """
        if self._session is None:
            raise RuntimeError("HTTP session is not initialized. Ensure connect() was called.")

        try:
            logger.debug(f"Making {method} request to {self._metabase_url}{endpoint}")

            # Log request payload for debugging (omit sensitive info)
            if json and logger.level <= logging.DEBUG:
                sanitized_json = {**json} if isinstance(json, dict) else json
                if isinstance(sanitized_json, dict) and "password" in sanitized_json:
                    sanitized_json["password"] = "********"
                logger.debug(f"Request payload: {sanitized_json}")

            response = await self._session.request(
                method=method,
                url=endpoint,
                timeout=aiohttp.ClientTimeout(total=30),
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
