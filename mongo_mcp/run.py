import os
import argparse
from .server import create_server


def main():
    parser = argparse.ArgumentParser(description="MongoDB MCP Server")
    parser.add_argument("--base-url", default=os.getenv("MONGO_API_BASE_URL"), help="MongoDB FastAPI base URL")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"], help="Transport protocol")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP transport host")
    parser.add_argument("--port", type=int, default=8765, help="HTTP transport port")
    args = parser.parse_args()

    mcp = create_server(base_url=args.base_url)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
