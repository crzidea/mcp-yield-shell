"""CLI entrypoint: start the Yield Shell MCP stdio server."""

from __future__ import annotations

from .config import Config
from .server import create_server


def main() -> None:
    """Start the Yield Shell MCP server on stdio."""
    config = Config()
    server = create_server(config)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
