# MongoDB MCP Server - Deployment & Usage Guide

## Directory Structure

```
mongo_mcp/
├── __init__.py    # Module entry point
├── client.py      # HTTP client wrapping FastAPI endpoints
├── server.py      # FastMCP server creation
├── tools.py       # MCP tool definitions + MongoHooks extension hooks
├── run.py         # Launcher script
└── doc.md         # This file
```

## Prerequisites

1. Ensure the MongoDB FastAPI proxy service is running (default: `http://localhost:8000`)
2. Install dependencies:
   ```bash
   pip install fastmcp httpx
   ```

## Running Locally

### STDIO Mode (Recommended for Claude Desktop, Cursor, etc.)

```bash
python -m mongo_mcp.run
```

### HTTP/SSE Mode

```bash
python -m mongo_mcp.run --transport sse --port 8765
```

### Specify MongoDB API Address

```bash
# Option 1: Environment variable
export MONGO_API_BASE_URL=http://your-server:8000
python -m mongo_mcp.run

# Option 2: CLI argument
python -m mongo_mcp.run --base-url http://your-server:8000
```

## Configuring in OpenCode

Add the MCP server configuration to your OpenCode config file (typically `~/.opencode/config.json` or `opencode.json` in the project root):

```json
{
  "mcp": {
    "mongodb": {
      "type": "local",
      "command":["python","-m", "mongo_mcp.run"],
      "enabled": true,
      "environment": {
        "MONGO_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `mongo_query` | Query a collection with filter, projection, sort, limit, skip |
| `mongo_count` | Count documents in a collection |
| `mongo_insert_one` | Insert a single document |
| `mongo_insert_many` | Insert multiple documents |
| `mongo_update_one` | Update a single document (supports upsert) |
| `mongo_update_many` | Update multiple documents (supports upsert) |
| `mongo_delete_one` | Delete a single document |
| `mongo_delete_many` | Delete multiple documents |
| `gridfs_upload` | Upload a file to GridFS (base64 encoded content) |
| `gridfs_search` | Search files in a GridFS bucket |
| `gridfs_delete` | Delete a file from a GridFS bucket |

## Extending Custom Logic

The `MongoHooks` class in `mongo_mcp/tools.py` provides extension points for injecting custom logic without modifying core tool code:

```python
# MongoHooks class in mongo_mcp/tools.py

class MongoHooks:
    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        """Before query - use for logging, auth checks, filter transformation"""
        pass

    @staticmethod
    def after_query(collection: str, result: dict) -> dict:
        """After query - use for result filtering, redaction, caching"""
        return result

    @staticmethod
    def before_write(collection: str, operation: str, data: dict | list | None) -> None:
        """Before write - use for validation, audit logging"""
        pass

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        """After write - use for notifications, cache invalidation"""
        return result

    @staticmethod
    def before_gridfs(bucket_name: str, action: str) -> None:
        """Before GridFS operation"""
        pass

    @staticmethod
    def after_gridfs(bucket_name: str, action: str, result: dict | bytes | list) -> dict | bytes | list:
        """After GridFS operation"""
        return result
```

### Example: Adding Query Audit Logging

```python
class MongoHooks:
    @staticmethod
    def before_query(collection: str, filter: dict | None) -> None:
        import logging
        logging.info(f"[AUDIT] Query on '{collection}' with filter: {filter}")

    @staticmethod
    def after_write(collection: str, operation: str, result: dict) -> dict:
        import logging
        logging.info(f"[AUDIT] {operation} on '{collection}' result: {result}")
        return result
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ImportError: cannot import name 'McpError'` | Folder cannot be named `mcp` (conflicts with SDK). Use `mongo_mcp` instead. |
| Connection refused | Verify the FastAPI proxy is running. Check `MONGO_API_BASE_URL`. |
| Tools not showing | Restart the MCP client (Claude Desktop / Cursor / etc.). |
| Python module not found | Use absolute Python path in config, or set `cwd` to the project root. |
