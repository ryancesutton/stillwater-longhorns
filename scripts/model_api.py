"""Small Responses API adapter: fixed HTTPS destination, no automatic retries."""

import asyncio
import json
import stat
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-luna"


class ModelError(RuntimeError):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ResponsesModel:
    def __init__(self):
        path = ROOT / "secrets/openai-api-key"
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise ModelError("Model key file requires owner-only permissions.")
        self._key = path.read_text().strip()
        if not self._key or any(c.isspace() for c in self._key):
            raise ModelError("Invalid model key file format.")

    async def respond(self, payload):
        # Caller also sets a whole-workflow deadline. A timed-out already-sent
        # request may still incur provider usage; never retry automatically.
        return await asyncio.to_thread(self._send, payload)

    def _send(self, payload):
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"},
        )
        try:
            with build_opener(NoRedirects()).open(request, timeout=30) as response:
                body = response.read(1_000_001)
            if len(body) > 1_000_000:
                raise ModelError("Model response exceeded the size limit.")
            return json.loads(body)
        except HTTPError as error:
            raise ModelError(f"Model API returned HTTP {error.code}; response body suppressed.") from None
        except ModelError:
            raise
        except Exception:
            raise ModelError("Model request failed; details suppressed. No automatic retry.") from None
