"""Local stdio MCP server exposing exactly two read-only tools."""

import logging
from typing import Annotated, Any

from mcp.server import MCPServer
from pydantic import Field

import game_tools

logging.getLogger("mysql.connector").setLevel(logging.WARNING)

mcp = MCPServer("Stillwater game evidence")


@mcp.tool(structured_output=True)
def list_games(
    season: Annotated[int, Field(strict=True, ge=1869, le=2100)] = 2023,
    limit: Annotated[int, Field(strict=True, ge=1, le=25)] = 20,
) -> dict[str, Any]:
    """List Texas games for a season. Maximum 25 results; reports truncation."""
    return game_tools.list_games(season, limit)


@mcp.tool(structured_output=True)
def get_game_data(
    source_game_id: Annotated[int, Field(strict=True, ge=1, le=9223372036854775807)],
) -> dict[str, Any]:
    """Get result, selected stats and source provenance for one CFBD game ID."""
    return game_tools.get_game_data(source_game_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
