"""Actual HTTP boundary checks; mock database and paid generation only."""
import http.client
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from web_app import DemoServer, Handler

GAME = {"source_game_id": 401520183, "season": 2023, "home_team": "Alabama", "away_team": "Texas"}


class WebTests(unittest.TestCase):
    def setUp(self):
        self.server = DemoServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        defaults = {"Origin": self.server.origin, "X-Demo-Token": self.server.token,
                    "Content-Type": "application/json"}
        defaults.update(headers or {})
        connection.request("GET" if body is None else "POST", path, body, defaults)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_static_and_no_file_disclosure(self):
        status, body, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Longhorns Briefing", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for path in ("/secrets/openai-api-key", "/../secrets/mysql-root-password", "/.git/config"):
            self.assertEqual(self.request(path)[0], 404)

    def test_bad_host_origin_and_token_never_generate(self):
        with patch("web_app.generate") as generate:
            self.assertEqual(self.request("/", headers={"Host": "evil.invalid"})[0], 403)
            for headers in ({"Origin": "https://evil.invalid"}, {"X-Demo-Token": "wrong"}):
                self.assertEqual(self.request("/api/briefing", "{}", headers)[0], 403)
            generate.assert_not_called()

    def test_live_disabled_and_saved_sample(self):
        with patch("web_app.generate") as generate:
            self.assertEqual(self.request("/api/briefing", "{}")[0], 403)
            status, body, _ = self.request("/api/sample")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["briefing"]["title"], "Texas vs. Alabama")
            status, body, _ = self.request("/api/team-aliases")
            self.assertEqual(status, 200)
            self.assertTrue(any(team["canonical_name"] == "BYU" for team in json.loads(body)["teams"]))
            generate.assert_not_called()

    @patch("web_app.list_games", return_value={"status": "ok", "games": [GAME]})
    @patch("web_app.generate", return_value={"briefing": "simulated"})
    def test_inputs_busy_and_attempt_limits(self, generate, games):
        self.server.live_enabled = True
        for data in ({"source_game_id": True}, {"source_game_id": 1, "prompt": "extra"}, {"source_game_id": 1}):
            self.assertEqual(self.request("/api/briefing", json.dumps(data))[0], 400)
        generate.assert_not_called()
        self.server.busy.acquire()
        self.assertEqual(self.request("/api/briefing", json.dumps({"source_game_id": 401520183}))[0], 409)
        self.server.busy.release()
        self.assertEqual(self.request("/api/briefing", json.dumps({"source_game_id": 401520183}))[0], 200)
        generate.assert_called_once_with(GAME)
        self.assertEqual(self.request("/api/briefing", json.dumps({"source_game_id": 401520183}))[0], 429)
        self.server.last_attempt = 0
        self.server.attempts = 10
        self.assertEqual(self.request("/api/briefing", json.dumps({"source_game_id": 401520183}))[0], 429)

    @patch("web_app.list_games", return_value={"status": "ok", "games": [GAME]})
    @patch("web_app.generate", side_effect=RuntimeError("FAKE_PRIVATE_DETAIL"))
    def test_generation_failure_sanitized_and_lock_released(self, generate, games):
        self.server.live_enabled = True
        status, body, _ = self.request("/api/briefing", json.dumps({"source_game_id": 401520183}))
        self.assertEqual(status, 502)
        self.assertNotIn(b"PRIVATE", body)
        self.assertFalse(self.server.busy.locked())

    def test_oversized_or_non_json_request_is_rejected(self):
        self.server.live_enabled = True
        with patch("web_app.generate") as generate:
            self.assertEqual(self.request("/api/briefing", "x" * 1025)[0], 400)
            self.assertEqual(self.request("/api/briefing", "{}", {"Content-Type": "text/plain"})[0], 400)
            generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
