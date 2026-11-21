"""Linux deployment check: real MCP protocol plus executing process identity.

Run as longhorns_app. No credentials, database queries or model API calls.
"""
import asyncio
import os
from pathlib import Path
import pwd
import subprocess
import sys

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]


async def check():
    if os.geteuid() != pwd.getpwnam("longhorns_app").pw_uid:
        raise RuntimeError("Run as longhorns_app")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "scripts/mcp_socket_bridge.py"), "/run/longhorns-mcp.sock"],
        env={"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1"},
    )
    async with Client(parameters, read_timeout_seconds=15) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {"list_games", "get_game_data"}
        print("PASS: managed MCP exposes exactly the two approved tools", flush=True)
        result = await client.call_tool("arbitrary_sql", {"sql": "SELECT 1"})
        assert result.is_error
        print("PASS: unregistered tool rejected without database access", flush=True)

        units = subprocess.check_output(
            ["systemctl", "list-units", "--no-legend", "--plain", "--type=service",
             "--state=running", "longhorns-mcp@*.service"], text=True, timeout=5,
        ).splitlines()
        assert units, "No active managed MCP process found"
        expected_uid = pwd.getpwnam("longhorns_mcp").pw_uid
        for line in units:
            unit = line.split()[0]
            pid = int(subprocess.check_output(
                ["systemctl", "show", "--property=MainPID", "--value", unit],
                text=True, timeout=5,
            ).strip())
            status = dict(row.split(":", 1) for row in Path(f"/proc/{pid}/status").read_text().splitlines()
                          if ":" in row)
            assert [int(value) for value in status["Uid"].split()] == [expected_uid] * 4
            assert status["NoNewPrivs"].strip() == "1"
            assert int(status["CapEff"].strip(), 16) == 0
        print("PASS: active MCP process uses longhorns_mcp, no-new-privileges, no effective capabilities",
              flush=True)


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(check(), timeout=30))
