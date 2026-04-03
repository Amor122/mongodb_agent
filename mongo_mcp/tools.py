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
        """查询 MongoDB 集合中的文档 / Query documents in a MongoDB collection.

        支持过滤、投影、排序、分页等完整查询功能。当不指定 limit 时，默认最多返回 1000 条文档。
        Supports filter, projection, sort, and pagination. Default max limit is 1000 when not specified.

        Args:
            collection: 集合名称 / Collection name, e.g. "users", "questions"
            filter: MongoDB 查询过滤条件 / MongoDB query filter, e.g. {"status": "active", "age": {"$gte": 18}}
            projection: 指定返回的字段 / Fields to return, e.g. {"name": 1, "email": 1, "_id": 0}
            sort: 排序规则，格式为 [[字段, 方向], ...]，1=升序，-1=降序 / Sort rules as [[field, direction], ...], 1=asc, -1=desc
            limit: 限制返回文档数量，不传则默认上限 1000 / Max documents to return, defaults to 1000
            skip: 跳过的文档数量，用于分页 / Documents to skip for pagination

        Examples:
            # 查询所有活跃用户，按创建时间降序，返回前 10 条
            # Query active users, sorted by created_at desc, top 10
            mongo_query(collection="users", filter={"status": "active"}, sort=[["created_at", -1]], limit=10)

            # 分页查询，第 2 页，每页 20 条
            # Pagination: page 2, 20 per page
            mongo_query(collection="questions", skip=20, limit=20)

        Returns:
            {"data": [文档列表 / document list], "total": 符合条件的总文档数 / total matching count}
        """
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
        """统计集合中符合条件的文档数量 / Count documents matching a filter.

        Args:
            collection: 集合名称 / Collection name
            filter: MongoDB 查询过滤条件，不传则统计集合中文档总数 / Query filter, omit for total count

        Examples:
            # 统计用户总数 / Count all users
            mongo_count(collection="users")

            # 统计活跃用户数量 / Count active users
            mongo_count(collection="users", filter={"status": "active"})

        Returns:
            {"total": 符合条件的文档数量 / count of matching documents}
        """
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
        """向集合中插入单条文档 / Insert a single document into a collection.

        Args:
            collection: 集合名称 / Collection name
            document: 要插入的文档（字典），无需手动指定 _id，MongoDB 会自动生成 / Document dict, _id is auto-generated

        Examples:
            mongo_insert_one(
                collection="users",
                document={"name": "张三", "age": 25, "email": "zhangsan@example.com"}
            )

        Returns:
            {"status": "success", "inserted_id": "插入文档的 ObjectId / inserted document ObjectId"}
        """
        hooks.before_write(collection, "insert_one", document)
        result = await client.write(
            collection=collection,
            operation="insert_one",
            data=document,
        )
        return hooks.after_write(collection, "insert_one", result)

    @mcp.tool
    async def mongo_insert_many(collection: str, documents: list[dict]) -> dict:
        """向集合中批量插入多条文档 / Insert multiple documents into a collection.

        Args:
            collection: 集合名称 / Collection name
            documents: 要插入的文档列表，每个元素是一个字典 / List of document dicts

        Examples:
            mongo_insert_many(
                collection="users",
                documents=[
                    {"name": "张三", "age": 25},
                    {"name": "李四", "age": 30},
                    {"name": "王五", "age": 28}
                ]
            )

        Returns:
            {"status": "success", "inserted_ids": ["ObjectId1", "ObjectId2", ...]}
        """
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
        """更新集合中符合条件的第一条文档 / Update the first matching document.

        Args:
            collection: 集合名称 / Collection name
            filter: 查询条件，用于定位要更新的文档 / Query filter to locate the document
            update: 更新操作符字典，必须包含 MongoDB 更新操作符，如 {"$set": {...}}、{"$inc": {...}} / Update operators dict, MUST include MongoDB operators like {"$set": {...}}
            upsert: 如果为 True，当没有匹配的文档时会自动插入新文档 / If True, insert a new document when no match found

        Examples:
            # 更新用户的邮箱 / Update user's email
            mongo_update_one(
                collection="users",
                filter={"name": "张三"},
                update={"$set": {"email": "new_email@example.com"}}
            )

            # 给文章增加阅读量 / Increment article views
            mongo_update_one(
                collection="articles",
                filter={"_id": "69cfe8fe444c9e09c73f91ec"},
                update={"$inc": {"views": 1}}
            )

            # upsert：不存在则插入 / Upsert: insert if not exists
            mongo_update_one(
                collection="counters",
                filter={"name": "daily_visits"},
                update={"$inc": {"count": 1}},
                upsert=True
            )

        Returns:
            {"status": "success", "matched_count": 匹配的文档数, "modified_count": 实际修改的文档数, "upserted_id": "upsert 插入的 ObjectId 或 None"}
        """
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
        """更新集合中符合条件的所有文档 / Update all matching documents.

        Args:
            collection: 集合名称 / Collection name
            filter: 查询条件，用于定位要更新的文档 / Query filter to locate documents
            update: 更新操作符字典，必须包含 MongoDB 更新操作符，如 {"$set": {...}} / Update operators dict, MUST include MongoDB operators
            upsert: 如果为 True，当没有匹配的文档时会自动插入新文档 / If True, insert when no match

        Examples:
            # 批量更新所有非活跃用户的状态 / Batch update all inactive users
            mongo_update_many(
                collection="users",
                filter={"status": "inactive"},
                update={"$set": {"status": "archived"}}
            )

            # 给所有未读消息标记为已读 / Mark all unread messages as read
            mongo_update_many(
                collection="messages",
                filter={"user_id": "123", "read": False},
                update={"$set": {"read": True}}
            )

        Returns:
            {"status": "success", "matched_count": 匹配的文档数, "modified_count": 实际修改的文档数, "upserted_id": "upsert 插入的 ObjectId 或 None"}
        """
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
        """删除集合中符合条件的第一条文档 / Delete the first matching document.

        Args:
            collection: 集合名称 / Collection name
            filter: 查询条件，用于定位要删除的文档 / Query filter to locate the document

        Examples:
            # 删除指定用户 / Delete a specific user
            mongo_delete_one(collection="users", filter={"name": "张三"})

            # 按 ObjectId 删除 / Delete by ObjectId
            mongo_delete_one(collection="questions", filter={"_id": "69cfe8fe444c9e09c73f91ec"})

        Returns:
            {"status": "success", "deleted_count": 删除的文档数量（0 或 1）/ count of deleted documents (0 or 1)}
        """
        hooks.before_write(collection, "delete_one", None)
        result = await client.write(
            collection=collection,
            operation="delete_one",
            filter=filter,
        )
        return hooks.after_write(collection, "delete_one", result)

    @mcp.tool
    async def mongo_delete_many(collection: str, filter: dict) -> dict:
        """删除集合中符合条件的所有文档 / Delete all matching documents.

        ⚠️ 注意：此操作会删除所有匹配的文档，请谨慎使用。建议先用 mongo_query 确认要删除的数据范围。
        ⚠️ Warning: This deletes ALL matching documents. Use mongo_query first to verify the scope.

        Args:
            collection: 集合名称 / Collection name
            filter: 查询条件。传入空字典 {} 会删除集合中所有文档 / Query filter. Empty dict {} deletes all documents

        Examples:
            # 删除所有已过期的会话 / Delete all expired sessions
            mongo_delete_many(collection="sessions", filter={"expires_at": {"$lt": "2024-01-01"}})

            # 清空集合（谨慎使用！）/ Empty a collection (use with caution!)
            mongo_delete_many(collection="temp_data", filter={})

        Returns:
            {"status": "success", "deleted_count": 删除的文档数量 / count of deleted documents}
        """
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
        """上传文件到 MongoDB GridFS / Upload a file to MongoDB GridFS.

        GridFS 是 MongoDB 用于存储和检索大文件（超过 BSON 文档 16MB 限制）的规范。文件内容需要以 base64 编码的字符串传入。
        GridFS is MongoDB's specification for storing and retrieving large files (exceeding the 16MB BSON limit).
        File content must be passed as a base64-encoded string.

        Args:
            bucket_name: GridFS 存储桶名称 / GridFS bucket name, e.g. "documents", "images", "default"
            filename: 文件名 / File name, e.g. "report.pdf"
            content_base64: 文件内容的 base64 编码字符串 / Base64-encoded file content
            content_type: MIME 类型 / MIME type. Common types:
                - 文本 / Text: "text/plain"
                - JSON: "application/json"
                - PDF: "application/pdf"
                - 图片 / Image: "image/png", "image/jpeg"
                - Word: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        Examples:
            # 上传文本文件 / Upload a text file
            gridfs_upload(
                bucket_name="documents",
                filename="readme.txt",
                content_base64="SGVsbG8gV29ybGQ=",
                content_type="text/plain"
            )

        Returns:
            {"status": "success", "file_id": "文件 ObjectId", "filename": "文件名"}
        """
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
        """搜索 GridFS 存储桶中的文件 / Search files in a GridFS bucket.

        Args:
            bucket_name: GridFS 存储桶名称 / GridFS bucket name
            filename_filter: 文件名模糊搜索关键词（支持正则），不传则返回桶中所有文件 / Filename regex filter, omit to list all files

        Examples:
            # 搜索包含 "report" 的文件 / Search files containing "report"
            gridfs_search(bucket_name="documents", filename_filter="report")

            # 列出桶中所有文件 / List all files in bucket
            gridfs_search(bucket_name="images")

        Returns:
            文件元数据列表 / List of file metadata, each containing:
            - _id: 文件 ObjectId / File ObjectId
            - filename: 文件名 / File name
            - length: 文件大小（字节）/ File size in bytes
            - uploadDate: 上传时间 / Upload timestamp
            - contentType: MIME 类型 / MIME type
            - metadata: 自定义元数据 / Custom metadata
        """
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
        """从 GridFS 存储桶中删除文件 / Delete a file from a GridFS bucket.

        Args:
            bucket_name: GridFS 存储桶名称 / GridFS bucket name
            file_id: 文件的 ObjectId 字符串，可通过 gridfs_search 获取 / File ObjectId string, obtainable via gridfs_search

        Examples:
            gridfs_delete(bucket_name="documents", file_id="69cfe8fe444c9e09c73f91ec")

        Returns:
            {"status": "success", "message": "File deleted"}
        """
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
    """MongoDB MCP 工具扩展钩子 / Extension hooks for MongoDB MCP tools.

    通过继承并重写此类的方法，可以在不修改核心代码的情况下注入自定义逻辑，
    例如：审计日志、权限校验、数据脱敏、缓存等。

    By extending and overriding this class, you can inject custom logic without modifying core code,
    such as: audit logging, permission checks, data redaction, caching, etc.

    Example:
        class AuditHooks(MongoHooks):
            @staticmethod
            def before_query(collection: str, filter: dict | None) -> None:
                import logging
                logging.info(f"[审计/AUDIT] Query on '{collection}' with filter: {filter}")

            @staticmethod
            def after_write(collection: str, operation: str, result: dict) -> dict:
                import logging
                logging.info(f"[审计/AUDIT] {operation} on '{collection}' result: {result}")
                return result
    """

    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        """查询前钩子 / Before query hook. 可用于日志审计、权限检查、过滤条件转换 / For logging, auth checks, filter transformation."""
        pass

    @staticmethod
    def after_query(collection: str, result: dict) -> dict:
        """查询后钩子 / After query hook. 可用于结果过滤、字段脱敏、缓存等 / For result filtering, redaction, caching."""
        return result

    @staticmethod
    def before_write(collection: str, operation: str, data: dict | list | None) -> None:
        """写入前钩子 / Before write hook. 可用于数据校验、审计日志、写入限制等 / For validation, audit logging, write limits."""
        pass

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        """写入后钩子 / After write hook. 可用于通知、缓存失效、审计记录等 / For notifications, cache invalidation, audit records."""
        return result

    @staticmethod
    def before_gridfs(bucket_name: str, action: str) -> None:
        """GridFS 操作前钩子 / Before GridFS hook. action 值为 "upload"、"search" 或 "delete"."""
        pass

    @staticmethod
    def after_gridfs(bucket_name: str, action: str, result: dict | bytes | list) -> dict | bytes | list:
        """GridFS 操作后钩子 / After GridFS hook."""
        return result


hooks = MongoHooks()


def register_all_tools(mcp: FastMCP, client: MongoHTTPClient):
    register_query_tools(mcp, client)
    register_write_tools(mcp, client)
    register_gridfs_tools(mcp, client)
