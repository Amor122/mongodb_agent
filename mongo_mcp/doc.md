# MongoDB MCP Server - 部署与使用指南 / Deployment & Usage Guide

## 目录结构 / Directory Structure

```
mongo_mcp/
├── __init__.py    # 模块入口 / Module entry point
├── client.py      # HTTP 客户端，封装 FastAPI 端点调用 / HTTP client wrapping FastAPI endpoints
├── server.py      # FastMCP 服务创建 / FastMCP server creation
├── tools.py       # MCP 工具定义 + MongoHooks 扩展钩子 / MCP tool definitions + MongoHooks extension hooks
├── run.py         # 启动脚本 / Launcher script
└── doc.md         # 本文档 / This file
```

## 前置条件 / Prerequisites

1. 确保 MongoDB FastAPI 代理服务已运行（默认：`http://localhost:8000`）
   Ensure the MongoDB FastAPI proxy service is running (default: `http://localhost:8000`)
2. 安装依赖 / Install dependencies:
   ```bash
   pip install fastmcp httpx
   ```

## 启动方式 / Running Locally

### STDIO 模式（推荐，适用于 Claude Desktop、Cursor、OpenCode 等）
### STDIO Mode (Recommended for Claude Desktop, Cursor, OpenCode, etc.)

```bash
python -m mongo_mcp.run
```

### HTTP/SSE 模式 / HTTP/SSE Mode

```bash
python -m mongo_mcp.run --transport sse --port 8765
```

### 指定 MongoDB API 地址 / Specify MongoDB API Address

```bash
# 方式一：环境变量 / Option 1: Environment variable
export MONGO_API_BASE_URL=http://your-server:8000
python -m mongo_mcp.run

# 方式二：命令行参数 / Option 2: CLI argument
python -m mongo_mcp.run --base-url http://your-server:8000
```

## 在 OpenCode 中配置 / Configuring in OpenCode

将以下配置添加到 OpenCode 配置文件（通常为项目根目录的 `opencode.json` 或 `~/.opencode/config.json`）：
Add the MCP server configuration to your OpenCode config file (typically `opencode.json` in the project root or `~/.opencode/config.json`):

```json
{
  "mcp": {
    "mongodb": {
      "type": "local",
      "command": ["python", "-m", "mongo_mcp.run"],
      "enabled": true,
      "environment": {
        "MONGO_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## 可用工具一览 / Available Tools

| 工具名 / Tool | 功能 / Description | 参数 / Parameters |
|------|------|------|
| `mongo_query` | 查询集合文档，支持过滤、投影、排序、分页 / Query collection with filter, projection, sort, pagination | `collection`, `filter`, `projection`, `sort`, `limit`, `skip` |
| `mongo_count` | 统计符合条件的文档数量 / Count matching documents | `collection`, `filter` |
| `mongo_insert_one` | 插入单条文档 / Insert single document | `collection`, `document` |
| `mongo_insert_many` | 批量插入多条文档 / Insert multiple documents | `collection`, `documents` |
| `mongo_update_one` | 更新第一条匹配的文档 / Update first matching document | `collection`, `filter`, `update`, `upsert` |
| `mongo_update_many` | 更新所有匹配的文档 / Update all matching documents | `collection`, `filter`, `update`, `upsert` |
| `mongo_delete_one` | 删除第一条匹配的文档 / Delete first matching document | `collection`, `filter` |
| `mongo_delete_many` | 删除所有匹配的文档 / Delete all matching documents | `collection`, `filter` |
| `gridfs_upload` | 上传文件到 GridFS / Upload file to GridFS | `bucket_name`, `filename`, `content_base64`, `content_type` |
| `gridfs_search` | 搜索 GridFS 中的文件 / Search files in GridFS | `bucket_name`, `filename_filter` |
| `gridfs_delete` | 从 GridFS 删除文件 / Delete file from GridFS | `bucket_name`, `file_id` |

## 工具使用示例 / Tool Usage Examples

### 查询操作 / Query Operations

```python
# 查询所有活跃用户，按创建时间降序，返回前 10 条
# Query active users, sorted by created_at desc, top 10
mongo_query(
    collection="users",
    filter={"status": "active"},
    sort=[["created_at", -1]],
    limit=10
)

# 分页查询，第 2 页，每页 20 条
# Pagination: page 2, 20 per page
mongo_query(collection="questions", skip=20, limit=20)

# 只返回指定字段
# Return only specified fields
mongo_query(collection="users", projection={"name": 1, "email": 1, "_id": 0})

# 统计数量 / Count
mongo_count(collection="users", filter={"status": "active"})
```

### 写入操作 / Write Operations

```python
# 插入单条 / Insert single
mongo_insert_one(
    collection="users",
    document={"name": "张三", "age": 25, "email": "zhangsan@example.com"}
)

# 批量插入 / Insert many
mongo_insert_many(
    collection="users",
    documents=[
        {"name": "张三", "age": 25},
        {"name": "李四", "age": 30}
    ]
)

# 更新文档（注意：update 参数必须包含 MongoDB 更新操作符）
# Update document (note: update MUST include MongoDB update operators like $set, $inc, etc.)
mongo_update_one(
    collection="users",
    filter={"name": "张三"},
    update={"$set": {"email": "new@example.com"}}
)

# 批量更新 / Update many
mongo_update_many(
    collection="articles",
    filter={"status": "draft"},
    update={"$set": {"status": "published"}}
)

# Upsert：不存在则插入 / Upsert: insert if not exists
mongo_update_one(
    collection="counters",
    filter={"name": "daily_visits"},
    update={"$inc": {"count": 1}},
    upsert=True
)

# 删除 / Delete
mongo_delete_one(collection="users", filter={"name": "张三"})
mongo_delete_many(collection="sessions", filter={"expired": True})
```

### GridFS 文件操作 / GridFS File Operations

```python
# 上传文件（内容需 base64 编码）
# Upload file (content must be base64 encoded)
gridfs_upload(
    bucket_name="documents",
    filename="report.pdf",
    content_base64="JVBERi0xLjQK...",
    content_type="application/pdf"
)

# 搜索文件 / Search files
gridfs_search(bucket_name="documents", filename_filter="report")

# 删除文件 / Delete file
gridfs_delete(bucket_name="documents", file_id="69cfe8fe444c9e09c73f91ec")
```

## 扩展自定义逻辑 / Extending Custom Logic

`MongoHooks` 类提供了扩展点，可在不修改核心代码的情况下注入自定义逻辑：
The `MongoHooks` class provides extension points for injecting custom logic without modifying core code:

```python
# 在 mongo_mcp/tools.py 中修改 MongoHooks 类
# Modify the MongoHooks class in mongo_mcp/tools.py

class MongoHooks:
    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        """查询前钩子 / Before query hook - 日志审计、权限检查、过滤条件转换 / logging, auth checks, filter transformation"""
        import logging
        logging.info(f"[审计/AUDIT] Query on '{collection}' with filter: {filter}")

    @staticmethod
    def after_query(collection: str, result: dict) -> dict:
        """查询后钩子 / After query hook - 结果脱敏、字段过滤 / result redaction, field filtering"""
        # 示例：移除敏感字段 / Example: remove sensitive fields
        for doc in result.get("data", []):
            doc.pop("password", None)
        return result

    @staticmethod
    def before_write(collection: str, operation: str, data: dict | list | None) -> None:
        """写入前钩子 / Before write hook - 数据校验、审计日志 / validation, audit logging"""
        import logging
        logging.info(f"[审计/AUDIT] {operation} on '{collection}'")

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        """写入后钩子 / After write hook - 通知、缓存失效 / notifications, cache invalidation"""
        return result
```

## 常见问题 / Troubleshooting

| 问题 / Issue | 解决方案 / Solution |
|------|----------|
| `ImportError: cannot import name 'McpError'` | 文件夹不能命名为 `mcp`（与 SDK 冲突），请使用 `mongo_mcp` / Folder cannot be named `mcp` (conflicts with SDK). Use `mongo_mcp` |
| Connection refused | 确认 FastAPI 代理服务正在运行，检查 `MONGO_API_BASE_URL` / Verify FastAPI proxy is running. Check `MONGO_API_BASE_URL` |
| 工具未显示 / Tools not showing | 重启 MCP 客户端（Claude Desktop / Cursor / OpenCode 等）/ Restart MCP client |
| Python module not found | 在配置中使用 Python 绝对路径，或将 `cwd` 设置为项目根目录 / Use absolute Python path in config, or set `cwd` to project root |
| 上传文件失败 / Upload fails | 确保 `Content-Type` 头未被全局覆盖，httpx 需要自动设置 `multipart/form-data` / Ensure `Content-Type` header is not globally set; httpx needs to auto-set `multipart/form-data` |
| `update` 操作报错 / `update` errors | `update` 参数必须包含 MongoDB 更新操作符，如 `{"$set": {...}}`，不能直接传文档 / `update` param MUST include MongoDB operators like `{"$set": {...}}`, not raw document |
