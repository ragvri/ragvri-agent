"""Filesystem MCP server - provides file operations via MCP protocol."""

import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Create MCP server
server = Server("filesystem-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available filesystem tools."""
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        ),
        Tool(
            name="list_directory",
            description="List files and directories in a path",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list",
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="file_info",
            description="Get information about a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check",
                    }
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a filesystem tool."""
    try:
        if name == "read_file":
            path = Path(arguments["path"]).expanduser().resolve()
            if not path.exists():
                return [TextContent(type="text", text=f"Error: File not found: {path}")]
            content = path.read_text()
            return [TextContent(type="text", text=content)]

        elif name == "write_file":
            path = Path(arguments["path"]).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(arguments["content"])
            return [TextContent(type="text", text=f"Successfully wrote to {path}")]

        elif name == "list_directory":
            path = Path(arguments["path"]).expanduser().resolve()
            if not path.is_dir():
                return [TextContent(type="text", text=f"Error: Not a directory: {path}")]
            entries = []
            for item in sorted(path.iterdir()):
                prefix = "📁" if item.is_dir() else "📄"
                entries.append(f"{prefix} {item.name}")
            return [TextContent(type="text", text="\n".join(entries))]

        elif name == "file_info":
            path = Path(arguments["path"]).expanduser().resolve()
            if not path.exists():
                return [TextContent(type="text", text=f"Error: Path not found: {path}")]
            stat = path.stat()
            info = f"""Path: {path}
Type: {'Directory' if path.is_dir() else 'File'}
Size: {stat.st_size} bytes
Modified: {stat.st_mtime}"""
            return [TextContent(type="text", text=info)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def main():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
