from fastmcp import FastMCP
from .client import MongoHTTPClient


def create_server(
    name: str = "MongoDB MCP Server",
    base_url: str | None = None,
) -> FastMCP:
    mcp = FastMCP(name=name)
    client = MongoHTTPClient(base_url=base_url)

    @mcp.resource("mongo://config")
    def get_config() -> dict:
        return {
            "base_url": client.base_url,
            "timeout": client.timeout,
        }

    from .tools import register_all_tools
    register_all_tools(mcp, client)

    return mcp
