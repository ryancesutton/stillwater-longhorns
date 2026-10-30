"""Real stdio MCP integration checks against local read-only MySQL views."""

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]


async def check():
    server = StdioServerParameters(command=sys.executable,
                                   args=[str(ROOT / "scripts/mcp_server.py")], cwd=ROOT)
    async with Client(server, read_timeout_seconds=20) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {"list_games", "get_game_data"}
        print("PASS: stdio server exposes exactly two approved tools.")
        result = await client.call_tool("list_games", {"season": 2023, "limit": 20})
        data = result.structured_content
        assert data["status"] == "ok" and len(data["games"]) == 14, data
        print("PASS: MCP returns 14 Texas 2023 games.")
        result = await client.call_tool("get_game_data", {"source_game_id": 401520183})
        data = result.structured_content
        assert data["status"] == "ok" and len(data["team_stats"]) == 2, data
        assert data["game"]["away_points"] == 34 and data["game"]["home_points"] == 24
        assert data["evidence_ref"] == "cfbd:game:401520183"
        print("PASS: Alabama game result, both teams’ stats, and source references.")
        result = await client.call_tool("get_game_data", {"source_game_id": 1})
        assert result.structured_content["status"] == "not_found"
        result = await client.call_tool("list_games", {"season": 2022})
        assert result.structured_content["games"] == []
        result = await client.call_tool("list_games", {"limit": 2})
        assert len(result.structured_content["games"]) == 2 and result.structured_content["truncated"]
        print("PASS: missing game/season and capped result count.")
        for name, arguments in (
            ("list_games", {"limit": 10000}),
            ("list_games", {"season": "2023"}),
            ("get_game_data", {"source_game_id": "1; SELECT * FROM private_security_fixture"}),
            ("arbitrary_sql", {"sql": "SELECT * FROM private_security_fixture"}),
        ):
            result = await client.call_tool(name, arguments)
            assert result.is_error, f"Expected rejection: {name}"
        print("PASS: oversized/type-invalid inputs and unregistered tool rejected over MCP.")


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(check(), timeout=90))
