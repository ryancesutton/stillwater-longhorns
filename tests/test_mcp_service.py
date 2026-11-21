"""Real MCP discovery across the socket relay; no database or model API calls."""
import asyncio
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from briefing import ALLOWED_TOOLS, WorkflowError, mcp_server_parameters
from mcp import Client


class MCPServiceTests(unittest.TestCase):
    def test_default_and_invalid_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mcp_server_parameters().args, [str(ROOT / "scripts/mcp_server.py")])
        for path in ("", "relative.sock"):
            with patch.dict(os.environ, {"STILLWATER_MCP_SOCKET": path}):
                with self.assertRaises(WorkflowError):
                    mcp_server_parameters()

    def test_real_mcp_discovery_through_socket(self):
        # TemporaryDirectory under /tmp keeps the Unix socket path short on macOS.
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            path = str(Path(directory) / "mcp.sock")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(path)
                listener.listen(1)
                listener.settimeout(15)
                failures = []

                def serve():
                    try:
                        connection, _ = listener.accept()
                        with connection, subprocess.Popen(
                            [sys.executable, str(ROOT / "scripts/mcp_server.py")],
                            stdin=connection, stdout=connection, stderr=subprocess.DEVNULL,
                        ) as process:
                            try:
                                process.wait(timeout=15)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                                raise
                    except Exception as error:
                        failures.append(error)

                thread = threading.Thread(target=serve, daemon=True)
                thread.start()

                async def check():
                    with patch.dict(os.environ, {
                        "STILLWATER_MCP_SOCKET": path,
                        "OPENAI_API_KEY": "DUMMY_SHOULD_NOT_REACH_RELAY",
                    }):
                        parameters = mcp_server_parameters()
                    self.assertNotIn("OPENAI_API_KEY", parameters.env)
                    async with Client(parameters, read_timeout_seconds=10) as client:
                        tools = await client.list_tools()
                        self.assertEqual({tool.name for tool in tools.tools}, ALLOWED_TOOLS)
                        # Unknown tools are rejected without a database lookup.
                        result = await client.call_tool("arbitrary_sql", {"sql": "SELECT 1"})
                        self.assertTrue(result.is_error)

                try:
                    asyncio.run(asyncio.wait_for(check(), timeout=15))
                finally:
                    thread.join(timeout=17)
                self.assertFalse(thread.is_alive())
                self.assertEqual(failures, [])
