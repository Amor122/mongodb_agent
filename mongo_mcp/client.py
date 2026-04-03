import os
import httpx
import asyncio
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.5  # seconds
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


class MongoHTTPClient:
    """HTTP client for communicating with the MongoDB FastAPI proxy."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = MAX_RETRIES,
    ):
        self.base_url = (base_url or os.getenv("MONGO_API_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Execute an HTTP request with automatic retry on transient failures."""
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                resp = await client.request(method, url, **kwargs)
                if resp.status_code < 400 or not _is_retryable(resp.status_code):
                    return resp
                logger.warning(
                    "Retryable HTTP %d on %s (attempt %d/%d)",
                    resp.status_code, url, attempt + 1, self.max_retries,
                )
                last_exception = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp
                )
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as e:
                logger.warning(
                    "Transient network error on %s (attempt %d/%d): %s",
                    url, attempt + 1, self.max_retries, e,
                )
                last_exception = e

            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))

        raise last_exception or httpx.HTTPError(f"Request failed after {self.max_retries} retries")

    async def _safe_json(self, method: str, url: str, **kwargs) -> Any:
        """Execute request and return parsed JSON response, raising MCP-friendly errors."""
        try:
            resp = await self._request_with_retry(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            detail = f"HTTP {e.response.status_code}"
            try:
                body = e.response.json()
                detail = body.get("detail", detail)
            except Exception:
                pass
            raise RuntimeError(f"{method} {url} failed: {detail}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Request to {self.base_url}{url} failed: {e}") from e

    async def _safe_bytes(self, method: str, url: str, **kwargs) -> bytes:
        """Execute request and return raw bytes."""
        try:
            resp = await self._request_with_retry(method, url, **kwargs)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPStatusError as e:
            detail = f"HTTP {e.response.status_code}"
            try:
                body = e.response.json()
                detail = body.get("detail", detail)
            except Exception:
                pass
            raise RuntimeError(f"{method} {url} failed: {detail}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Request to {self.base_url}{url} failed: {e}") from e

    async def query(self, collection: str, **kwargs) -> dict:
        payload = {"collection": collection}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        return await self._safe_json("POST", "/api/v1/query/", json=payload)

    async def write(self, collection: str, operation: str, **kwargs) -> dict:
        payload = {"collection": collection, "operation": operation}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        return await self._safe_json("POST", "/api/v1/data/write", json=payload)

    async def gridfs_upload(self, bucket_name: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
        return await self._safe_json(
            "POST",
            f"/api/v1/gridfs/bucket/{bucket_name}/upload",
            files={"file": (filename, content, content_type)},
        )

    async def gridfs_search(self, bucket_name: str, query_filter: Optional[dict] = None) -> list[dict]:
        return await self._safe_json(
            "POST",
            f"/api/v1/gridfs/bucket/{bucket_name}/search",
            json=query_filter or {},
        )

    async def gridfs_download(self, bucket_name: str, file_id: str) -> bytes:
        return await self._safe_bytes(
            "GET",
            f"/api/v1/gridfs/bucket/{bucket_name}/download/{file_id}",
        )

    async def gridfs_delete(self, bucket_name: str, file_id: str) -> dict:
        return await self._safe_json(
            "DELETE",
            f"/api/v1/gridfs/bucket/{bucket_name}/delete/{file_id}",
        )

    async def health_check(self) -> dict:
        return await self._safe_json("GET", "/health")

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
