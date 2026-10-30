import copy
import json
import os
import sys
import tempfile
import unittest
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from briefing import Audit, WorkflowError, minimal_mcp_environment, run_workflow

REF = "cfbd:game:401520183"
DATA = {"status": "ok", "game": {"source_game_id": 401520183, "home_team": "Alabama",
        "away_team": "Texas", "home_points": 24, "away_points": 34}, "team_stats": [],
        "evidence_ref": REF, "private_config": "FAKE_SECRET_PRIVATE", "raw_file_path": "FAKE_SECRET_PATH"}


def response(output):
    return {"status": "completed", "usage": {"input_tokens": 100, "output_tokens": 20}, "output": output}


def tool_call(name="get_game_data", args=None):
    return {"type": "function_call", "name": name, "call_id": "call-1",
            "arguments": json.dumps(args if args is not None else {"source_game_id": 401520183})}


def writer_response(ref=REF):
    value = {"title": "Texas vs Alabama", "claims": [
        {"text": "Texas scored 34 points.", "evidence_ref": ref},
        {"text": "Alabama scored 24 points.", "evidence_ref": ref}],
        "limitations": ["Team statistics unavailable in this fixture."]}
    return response([{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}]}])


class FakeModel:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.payloads = []

    async def respond(self, payload):
        self.payloads.append(copy.deepcopy(payload))
        return next(self.replies)


class FakeTools:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return SimpleNamespace(is_error=False, structured_content=copy.deepcopy(DATA))


class BriefingTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, model, tools):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            audit = Audit(path)
            try:
                result = await run_workflow("Brief Texas-Alabama 2023", model, tools, audit)
            finally:
                audit.close()
            return result, path.read_text()

    async def test_two_stages_and_payload_hygiene(self):
        model = FakeModel([response([tool_call()]), response([]), writer_response()])
        tools = FakeTools()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "FAKE_SECRET_MODEL", "UNRELATED_SECRET": "FAKE_SECRET_ENV"}):
            result, logs = await self.run_case(model, tools)
        serialized = json.dumps(model.payloads) + logs
        self.assertNotIn("FAKE_SECRET", serialized)
        self.assertNotIn("private_config", serialized)
        self.assertNotIn("raw_file_path", serialized)
        self.assertNotIn("Texas scored", logs)
        self.assertNotIn("tools", model.payloads[-1])
        self.assertEqual(model.payloads[-1]["instructions"].split()[0], "Write")
        self.assertTrue(all(p["store"] is False and p["reasoning"]["effort"] == "low" for p in model.payloads))
        self.assertEqual(result["model_calls"], 3)

    async def test_unapproved_calls_never_dispatch(self):
        for call in (tool_call("shell"), tool_call(args={"source_game_id": "1; SQL"}),
                     tool_call(args={"source_game_id": 1, "sql": "SELECT private"})):
            tools = FakeTools()
            with self.assertRaises(WorkflowError):
                await self.run_case(FakeModel([response([call])]), tools)
            self.assertEqual(tools.calls, [])

    async def test_unknown_citation_rejected(self):
        with self.assertRaisesRegex(WorkflowError, "citations"):
            await self.run_case(FakeModel([response([tool_call()]), response([]), writer_response("invented")]), FakeTools())

    async def test_missing_evidence_stops_before_writer(self):
        model = FakeModel([response([])])
        with self.assertRaisesRegex(WorkflowError, "No game evidence"):
            await self.run_case(model, FakeTools())
        self.assertEqual(len(model.payloads), 1)

    async def test_incomplete_and_usage_failure(self):
        for r in ({"status": "incomplete", "usage": {"input_tokens": 1, "output_tokens": 2500}},
                  {"status": "completed", "usage": {"input_tokens": 25000, "output_tokens": 1}}):
            with self.assertRaises(WorkflowError):
                await self.run_case(FakeModel([r]), FakeTools())

    async def test_timeout_and_audit_field_rejection(self):
        class SlowModel:
            async def respond(self, payload):
                await asyncio.sleep(10)
        with self.assertRaises(TimeoutError):
            await asyncio.wait_for(self.run_case(SlowModel(), FakeTools()), timeout=0.02)
        with tempfile.TemporaryDirectory() as directory:
            audit = Audit(Path(directory) / "log")
            try:
                with self.assertRaises(WorkflowError):
                    audit.write("tool_call", password="FAKE_SECRET")
            finally:
                audit.close()

    def test_environment_allowlist(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "FAKE_SECRET_MODEL", "UNRELATED_SECRET": "FAKE_SECRET_ENV"}):
            env = minimal_mcp_environment()
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("UNRELATED_SECRET", env)

    async def test_actual_sdk_child_environment(self):
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "environment.json"
            # Record presence booleans only; never dump environment values.
            code = ("import os,json,sys; from pathlib import Path; "
                    "Path(sys.argv[1]).write_text(json.dumps({k:k in os.environ for k in "
                    "['OPENAI_API_KEY','UNRELATED_SECRET']})); sys.stdin.read()")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "FAKE_SECRET_MODEL", "UNRELATED_SECRET": "FAKE_SECRET_ENV"}):
                params = StdioServerParameters(command=sys.executable, args=["-c", code, str(report)],
                                               env=minimal_mcp_environment())
                async with stdio_client(params):
                    for _ in range(30):
                        if report.exists():
                            break
                        await asyncio.sleep(0.05)
                    self.assertEqual(json.loads(report.read_text()),
                                     {"OPENAI_API_KEY": False, "UNRELATED_SECRET": False})


if __name__ == "__main__":
    unittest.main()
