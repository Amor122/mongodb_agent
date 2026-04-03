from typing import Any
from fastmcp import FastMCP
from .client import MongoHTTPClient


def register_query_tools(mcp: FastMCP, client: MongoHTTPClient):
    @mcp.tool
    async def mongo_query(
        collection: str,
        filter: dict | None = None,
        projection: dict | None = None,
        sort: list | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> dict:
        """Query MongoDB collection. Supports filter, projection, sort, limit, skip."""
        hooks.before_query(collection, filter)
        result = await client.query(
            collection=collection,
            filter=filter,
            projection=projection,
            sort=sort,
            limit=limit,
            skip=skip,
        )
        return hooks.after_query(collection, result)

    @mcp.tool
    async def mongo_count(collection: str, filter: dict | None = None) -> dict:
        """Count documents in a MongoDB collection."""
        hooks.before_query(collection, filter)
        result = await client.query(
            collection=collection,
            filter=filter,
            limit=0,
        )
        return hooks.after_query(collection, {"total": result.get("total", 0)})


def register_write_tools(mcp: FastMCP, client: MongoHTTPClient):
    @mcp.tool
    async def mongo_insert_one(collection: str, document: dict) -> dict:
        """Insert a single document into a MongoDB collection."""
        hooks.before_write(collection, "insert_one", document)
        result = await client.write(
            collection=collection,
            operation="insert_one",
            data=document,
        )
        return hooks.after_write(collection, "insert_one", result)

    @mcp.tool
    async def mongo_insert_many(collection: str, documents: list[dict]) -> dict:
        """Insert multiple documents into a MongoDB collection."""
        hooks.before_write(collection, "insert_many", documents)
        result = await client.write(
            collection=collection,
            operation="insert_many",
            data=documents,
        )
        return hooks.after_write(collection, "insert_many", result)

    @mcp.tool
    async def mongo_update_one(
        collection: str,
        filter: dict,
        update: dict,
        upsert: bool = False,
    ) -> dict:
        """Update a single document in a MongoDB collection."""
        hooks.before_write(collection, "update_one", update)
        result = await client.write(
            collection=collection,
            operation="update_one",
            filter=filter,
            data=update,
            options={"upsert": upsert} if upsert else None,
        )
        return hooks.after_write(collection, "update_one", result)

    @mcp.tool
    async def mongo_update_many(
        collection: str,
        filter: dict,
        update: dict,
        upsert: bool = False,
    ) -> dict:
        """Update multiple documents in a MongoDB collection."""
        hooks.before_write(collection, "update_many", update)
        result = await client.write(
            collection=collection,
            operation="update_many",
            filter=filter,
            data=update,
            options={"upsert": upsert} if upsert else None,
        )
        return hooks.after_write(collection, "update_many", result)

    @mcp.tool
    async def mongo_delete_one(collection: str, filter: dict) -> dict:
        """Delete a single document from a MongoDB collection."""
        hooks.before_write(collection, "delete_one", None)
        result = await client.write(
            collection=collection,
            operation="delete_one",
            filter=filter,
        )
        return hooks.after_write(collection, "delete_one", result)

    @mcp.tool
    async def mongo_delete_many(collection: str, filter: dict) -> dict:
        """Delete multiple documents from a MongoDB collection."""
        hooks.before_write(collection, "delete_many", None)
        result = await client.write(
            collection=collection,
            operation="delete_many",
            filter=filter,
        )
        return hooks.after_write(collection, "delete_many", result)


def register_gridfs_tools(mcp: FastMCP, client: MongoHTTPClient):
    @mcp.tool
    async def gridfs_upload(
        bucket_name: str,
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload a file to GridFS. Content should be base64 encoded."""
        import base64
        hooks.before_gridfs(bucket_name, "upload")
        content = base64.b64decode(content_base64)
        result = await client.gridfs_upload(
            bucket_name=bucket_name,
            filename=filename,
            content=content,
            content_type=content_type,
        )
        return hooks.after_gridfs(bucket_name, "upload", result)  # type: ignore[return-value]

    @mcp.tool
    async def gridfs_search(bucket_name: str, filename_filter: str | None = None) -> list:
        """Search for files in a GridFS bucket."""
        hooks.before_gridfs(bucket_name, "search")
        query_filter = None
        if filename_filter:
            query_filter = {"filename": {"$regex": filename_filter}}
        result = await client.gridfs_search(
            bucket_name=bucket_name,
            query_filter=query_filter,
        )
        return hooks.after_gridfs(bucket_name, "search", result)  # type: ignore[return-value]

    @mcp.tool
    async def gridfs_delete(bucket_name: str, file_id: str) -> dict:
        """Delete a file from a GridFS bucket."""
        hooks.before_gridfs(bucket_name, "delete")
        result = await client.gridfs_delete(
            bucket_name=bucket_name,
            file_id=file_id,
        )
        return hooks.after_gridfs(bucket_name, "delete", result)  # type: ignore[return-value]


# ============================================================
# Predefined logic hooks - extend here for custom business logic
# ============================================================

class MongoHooks:
    """Extension hooks for MongoDB MCP tools."""

    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        """Called before any query operation. Override for logging, auth checks, filter transformation."""
        pass

    @staticmethod
    def after_query(collection: str, result: dict) -> dict:
        """Called after any query operation. Can transform result (filtering, redaction, caching)."""
        return result

    @staticmethod
    def before_write(collection: str, operation: str, data: dict | list | None) -> None:
        """Called before any write operation. Override for validation, audit logging."""
        pass

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        """Called after any write operation. Can transform result (notifications, cache invalidation)."""
        return result

    @staticmethod
    def before_gridfs(bucket_name: str, action: str) -> None:
        """Called before any GridFS operation."""
        pass

    @staticmethod
    def after_gridfs(bucket_name: str, action: str, result: dict | bytes | list) -> dict | bytes | list:
        """Called after any GridFS operation."""
        return result


hooks = MongoHooks()


def register_all_tools(mcp: FastMCP, client: MongoHTTPClient):
    register_query_tools(mcp, client)
    register_write_tools(mcp, client)
    register_gridfs_tools(mcp, client)
