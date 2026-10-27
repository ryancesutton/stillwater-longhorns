"""Fetch a fixed CFBD sample; preserve the response and sanitized provenance."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = {"year": 2023, "team": "Texas", "seasonType": "both"}
ENDPOINT = "https://api.collegefootballdata.com/games"


class NoRedirects(HTTPRedirectHandler):
    """Do not forward an authenticated request to a redirected destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_sample(endpoint, parameters, prefix):
    if endpoint not in (ENDPOINT, ENDPOINT + "/teams"):
        raise SystemExit("Refusing to send credentials to an unapproved endpoint.")
    try:
        key = (ROOT / "secrets/cfbd-api-key").read_text().strip()
    except OSError:
        raise SystemExit("Cannot read secrets/cfbd-api-key; check local setup.") from None
    if not key or any(character.isspace() for character in key):
        raise SystemExit("The API key file must contain one nonempty token.")

    request = Request(
        endpoint + "?" + urlencode(parameters),
        headers={"Authorization": "Bearer " + key, "Accept": "application/json"},
    )
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            # Bound memory use even if the source unexpectedly returns a large body.
            body = response.read(5_000_001)
            status = response.status
    except HTTPError as error:
        raise SystemExit(f"CFBD returned HTTP {error.code}; no response body logged.") from None
    except (URLError, TimeoutError, OSError):
        raise SystemExit("Request failed; check network access and certificates. No automatic retry.") from None
    if len(body) > 5_000_000:
        raise SystemExit("Response exceeded the 5 MB safety limit; nothing saved.")

    retrieved = datetime.now(timezone.utc)
    folder = ROOT / "data/raw" / retrieved.strftime(prefix + "-%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "response.json").write_bytes(body)
    metadata = {
        "source": "CollegeFootballData",
        "endpoint": endpoint,
        "parameters": parameters,
        "retrieved_at_utc": retrieved.isoformat(),
        "http_status": status,
        "sha256": hashlib.sha256(body).hexdigest(),
        "byte_count": len(body),
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Original response and provenance saved: {folder.relative_to(ROOT)}")

    try:
        games = json.loads(body)
    except (ValueError, UnicodeError):
        raise SystemExit("Validation failed: response is not valid JSON. Original preserved.") from None
    if not isinstance(games, list) or not games:
        raise SystemExit("Validation failed: expected a nonempty list of games.")

    return games


def main():
    games = fetch_sample(ENDPOINT, PARAMETERS, "cfbd-games")
    ids = set()
    for game in games:
        if not isinstance(game, dict):
            raise SystemExit("Validation failed: a game is not an object.")
        game_id = game.get("id")
        if type(game_id) is not int or game_id in ids:
            raise SystemExit("Validation failed: missing, invalid, or duplicate game ID.")
        ids.add(game_id)
        if game.get("season") != 2023 or "Texas" not in (game.get("homeTeam"), game.get("awayTeam")):
            raise SystemExit("Validation failed: unexpected season or team.")
        if not game.get("startDate") or game.get("seasonType") not in ("regular", "postseason"):
            raise SystemExit("Validation failed: missing date or unexpected season type.")
        if game.get("completed") is not True or any(
            type(game.get(field)) is not int or game[field] < 0
            for field in ("homePoints", "awayPoints")
        ):
            raise SystemExit("Validation failed: expected completed games with nonnegative integer scores.")

    postseason = sum(game["seasonType"] == "postseason" for game in games)
    print(f"Structural checks passed: {len(games)} unique games; {postseason} postseason games.")
    print("Completeness and accuracy still require comparison with official records.")


if __name__ == "__main__":
    main()
