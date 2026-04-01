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
    ) -> str:
        """Query MongoDB collection. Supports filter, projection, sort, limit, skip."""
        import json
        result = await client.query(
            collection=collection,
            filter=filter,
            projection=projection,
            sort=sort,
            limit=limit,
            skip=skip,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_count(collection: str, filter: dict | None = None) -> str:
        """Count documents in a MongoDB collection."""
        import json
        result = await client.query(
            collection=collection,
            filter=filter,
            limit=0,
        )
        return json.dumps({"total": result.get("total", 0)}, ensure_ascii=False, indent=2)


def register_write_tools(mcp: FastMCP, client: MongoHTTPClient):
    @mcp.tool
    async def mongo_insert_one(collection: str, document: dict) -> str:
        """Insert a single document into a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="insert_one",
            data=document,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_insert_many(collection: str, documents: list[dict]) -> str:
        """Insert multiple documents into a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="insert_many",
            data=documents,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_update_one(
        collection: str,
        filter: dict,
        update: dict,
        upsert: bool = False,
    ) -> str:
        """Update a single document in a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="update_one",
            filter=filter,
            data=update,
            options={"upsert": upsert} if upsert else None,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_update_many(
        collection: str,
        filter: dict,
        update: dict,
        upsert: bool = False,
    ) -> str:
        """Update multiple documents in a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="update_many",
            filter=filter,
            data=update,
            options={"upsert": upsert} if upsert else None,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_delete_one(collection: str, filter: dict) -> str:
        """Delete a single document from a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="delete_one",
            filter=filter,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def mongo_delete_many(collection: str, filter: dict) -> str:
        """Delete multiple documents from a MongoDB collection."""
        import json
        result = await client.write(
            collection=collection,
            operation="delete_many",
            filter=filter,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


def register_gridfs_tools(mcp: FastMCP, client: MongoHTTPClient):
    @mcp.tool
    async def gridfs_upload(
        bucket_name: str,
        filename: str,
        content_base64: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to GridFS. Content should be base64 encoded."""
        import base64
        import json
        content = base64.b64decode(content_base64)
        result = await client.gridfs_upload(
            bucket_name=bucket_name,
            filename=filename,
            content=content,
            content_type=content_type,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def gridfs_search(bucket_name: str, filename_filter: str | None = None) -> str:
        """Search for files in a GridFS bucket."""
        import json
        query_filter = None
        if filename_filter:
            query_filter = {"filename": {"$regex": filename_filter}}
        result = await client.gridfs_search(
            bucket_name=bucket_name,
            query_filter=query_filter,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool
    async def gridfs_delete(bucket_name: str, file_id: str) -> str:
        """Delete a file from a GridFS bucket."""
        import json
        result = await client.gridfs_delete(
            bucket_name=bucket_name,
            file_id=file_id,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# Predefined logic hooks - extend here for custom business logic
# ============================================================
# These hooks provide extension points for adding pre-defined
# business logic without modifying the core tool implementations.
#
# Example usage:
#   def before_query_hook(collection: str, filter: dict):
#       # Add logging, validation, or transformation
#       pass
#
#   def after_write_hook(result: dict):
#       # Add notifications, caching invalidation, etc.
#       pass
# ============================================================

class MongoHooks:
    """Extension hooks for MongoDB MCP tools."""

    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        """Called before any query operation. Override for custom logic."""
        pass

    @staticmethod
    def after_query(collection: str, result: dict) -> dict:
        """Called after any query operation. Can transform result."""
        return result

    @staticmethod
    def before_write(collection: str, operation: str, data: dict | list | None) -> None:
        """Called before any write operation. Override for validation/logging."""
        pass

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        """Called after any write operation. Can transform result."""
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
