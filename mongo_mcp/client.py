import os
import httpx
from typing import Optional


class MongoHTTPClient:
    """HTTP client for communicating with the MongoDB FastAPI proxy."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or os.getenv("MONGO_API_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def query(self, collection: str, **kwargs) -> dict:
        payload = {"collection": collection}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        client = await self._get_client()
        resp = await client.post("/api/v1/query/", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def write(self, collection: str, operation: str, **kwargs) -> dict:
        payload = {"collection": collection, "operation": operation}
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        client = await self._get_client()
        resp = await client.post("/api/v1/data/write", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def gridfs_upload(self, bucket_name: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> dict:
        client = await self._get_client()
        resp = await client.post(
            f"/api/v1/gridfs/bucket/{bucket_name}/upload",
            files={"file": (filename, content, content_type)},
        )
        resp.raise_for_status()
        return resp.json()

    async def gridfs_search(self, bucket_name: str, query_filter: Optional[dict] = None) -> list:
        client = await self._get_client()
        resp = await client.post(
            f"/api/v1/gridfs/bucket/{bucket_name}/search",
            json=query_filter or {},
        )
        resp.raise_for_status()
        return resp.json()

    async def gridfs_download(self, bucket_name: str, file_id: str) -> bytes:
        client = await self._get_client()
        resp = await client.get(f"/api/v1/gridfs/bucket/{bucket_name}/download/{file_id}")
        resp.raise_for_status()
        return resp.content

    async def gridfs_delete(self, bucket_name: str, file_id: str) -> dict:
        client = await self._get_client()
        resp = await client.delete(f"/api/v1/gridfs/bucket/{bucket_name}/delete/{file_id}")
        resp.raise_for_status()
        return resp.json()

    async def health_check(self) -> dict:
        client = await self._get_client()
        resp = await client.get("/health")
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
