"""Local demonstration UI. Standard library only; not a public deployment server."""
import argparse
import asyncio
import json
import secrets
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from briefing import Audit, ROOT, live
from game_tools import list_games

WEB = ROOT / "web"
FILES = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
         "/game_search.js": ("game_search.js", "text/javascript"),
         "/style.css": ("style.css", "text/css")}


def generate(game):
    path = ROOT / "logs" / ("web-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".jsonl")
    audit = Audit(path)
    try:
        request = (f"Brief the {game['season']} Texas game against "
                   f"{game['home_team']} / {game['away_team']}; "
                   f"CFBD source_game_id {game['source_game_id']}. Retrieve only this game.")
        result = asyncio.run(asyncio.wait_for(live(request, audit), timeout=180))
        if len(result["evidence"]) != 1 or result["evidence"][0]["game"]["source_game_id"] != game["source_game_id"]:
            raise ValueError("Selected game mismatch")
        return result
    except Exception:
        audit.write("workflow", outcome="failed")
        raise
    finally:
        audit.close()


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, *, live_enabled=False):
        super().__init__(address, handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.host_header = f"127.0.0.1:{self.server_port}"
        self.token = secrets.token_urlsafe(32)
        self.live_enabled = live_enabled
        self.busy = threading.Lock()
        self.attempts = 0
        self.last_attempt = 0


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass  # Do not log URLs, payloads, or arbitrary request text.

    def send(self, status, body, content_type="application/json"):
        data = json.dumps(body).encode() if content_type == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def allowed_host(self):
        if self.headers.get("Host") != self.server.host_header:
            self.send(403, {"error": "Unrecognized local host."})
            return False
        return True

    def do_GET(self):
        if not self.allowed_host():
            return
        if self.path in FILES:
            filename, content_type = FILES[self.path]
            self.send(200, (WEB / filename).read_bytes(), content_type)
        elif self.path == "/api/config":
            self.send(200, {"token": self.server.token, "live_enabled": self.server.live_enabled})
        elif self.path == "/api/games":
            data = list_games(2023, 25)
            self.send(200 if data.get("status") == "ok" else 503, data)
        elif self.path == "/api/sample":
            self.send(200, json.loads((WEB / "sample.json").read_text()))
        elif self.path == "/api/team-aliases":
            self.send(200, json.loads((WEB / "team_aliases.json").read_text()))
        else:
            self.send(404, {"error": "Not found."})

    def do_POST(self):
        if not self.allowed_host():
            return
        # Browser-origin and per-start token checks prevent cross-site paid requests.
        if self.headers.get("Origin") != self.server.origin or not secrets.compare_digest(
                self.headers.get("X-Demo-Token", ""), self.server.token):
            self.send(403, {"error": "Local request verification failed."})
            return
        if self.path != "/api/briefing":
            self.send(404, {"error": "Not found."})
            return
        if not self.server.live_enabled:
            self.send(403, {"error": "Live generation is disabled. Restart with --live to enable paid calls."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 1024 or self.headers.get("Content-Type") != "application/json" or self.headers.get("Transfer-Encoding"):
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict) or set(data) != {"source_game_id"} or type(data["source_game_id"]) is not int:
                raise ValueError()
        except (ValueError, TimeoutError):
            self.send(400, {"error": "Choose a valid game."})
            return
        if not self.server.busy.acquire(blocking=False):
            self.send(409, {"error": "A briefing is already running. Please wait."})
            return
        try:
            if self.server.attempts >= 10 or time.monotonic() - self.server.last_attempt < 10:
                self.send(429, {"error": "Demo limit reached or requests too close together. Wait ten seconds; ten attempts allowed per server start."})
                return
            games = list_games(2023, 25)
            if games.get("status") != "ok":
                self.send(503, {"error": "Game data is unavailable. Check local MySQL."})
                return
            game = next((g for g in games["games"] if g["source_game_id"] == data["source_game_id"]), None)
            if game is None:
                self.send(400, {"error": "Choose a game in the imported 2023 season."})
                return
            self.server.attempts += 1
            self.server.last_attempt = time.monotonic()
            try:
                result = generate(game)
            except Exception:
                self.send(502, {"error": "Briefing stopped: model access, timeout, retrieval, budget, or output validation failed. No automatic retry."})
                return
            self.send(200, result)
        finally:
            self.server.busy.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Enable paid generation from the button")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = DemoServer(("127.0.0.1", args.port), Handler, live_enabled=args.live)
    print(f"Stillwater: {server.origin} (live generation {'enabled' if args.live else 'disabled'})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
