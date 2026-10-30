"""Run the real MCP/database path with a fake model. No paid model requests."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

from mcp import Client, StdioServerParameters

from briefing import Audit, ROOT, minimal_mcp_environment, run_workflow


class FakeModel:
    def __init__(self):
        self.turn = 0

    async def respond(self, payload):
        self.turn += 1
        if "tools" not in payload:
            evidence = json.loads(payload["input"][0]["content"])["evidence"][0]
            game = evidence["game"]
            result = {"title": "OFFLINE TEST — simulated writer",
                      "claims": [
                          {"text": f"{game['away_team']} scored {game['away_points']}.",
                           "evidence_ref": evidence["evidence_ref"]},
                          {"text": f"{game['home_team']} scored {game['home_points']}.",
                           "evidence_ref": evidence["evidence_ref"]}],
                      "limitations": ["Fake model; this is not a generated briefing."]}
            output = [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(result)}]}]
        elif self.turn <= 2:
            name, arguments = (("list_games", {"season": 2023, "limit": 20}) if self.turn == 1
                               else ("get_game_data", {"source_game_id": 401520183}))
            output = [{"type": "function_call", "name": name, "call_id": f"fake-{self.turn}",
                       "arguments": json.dumps(arguments)}]
        else:
            output = []
        return {"status": "completed", "output": output,
                "usage": {"input_tokens": 0, "output_tokens": 0}}


async def main():
    server = StdioServerParameters(command=sys.executable, args=[str(ROOT / "scripts/mcp_server.py")],
                                   cwd=ROOT, env=minimal_mcp_environment())
    with tempfile.TemporaryDirectory() as directory:
        audit = Audit(Path(directory) / "audit.jsonl")
        try:
            async with Client(server, read_timeout_seconds=20) as tools:
                result = await run_workflow("Brief Texas-Alabama 2023", FakeModel(), tools, audit)
            assert len(result["evidence"]) == 1 and result["model_calls"] == 4
            print("PASS: fake research -> real stdio MCP -> read-only MySQL -> fake writer.")
            print("Evidence and citation checks passed; no model API requests or model key access.")
        finally:
            audit.close()


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=90))
