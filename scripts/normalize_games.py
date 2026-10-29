"""Offline, verified dry run of Texas 2023 teams, games, and statistics."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from normalize_stats import normalize as normalize_stats


def unsigned(value, maximum=18446744073709551615):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("Expected an unsigned integer within the SQL column range.")
    return value


def text(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("Missing or oversized text field.")
    return value


def utc_datetime(value):
    """Require a timezone; return naive UTC for the proposed SQL DATETIME."""
    parsed = datetime.fromisoformat(text(value, 64).replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone.")
    result = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    if result.year < 1000 or result.microsecond % 1000:
        raise ValueError("Timestamp cannot be represented exactly in DATETIME(3).")
    return result


def load_verified(path, endpoint):
    """Verify bytes and request scope against adjacent retrieval metadata."""
    body = path.read_bytes()
    metadata = json.loads(path.with_name("metadata.json").read_text())
    if (metadata.get("sha256") != hashlib.sha256(body).hexdigest()
            or metadata.get("byte_count") != len(body)):
        raise ValueError("Response does not match its recorded hash or size.")
    if (metadata.get("source") != "CollegeFootballData"
            or metadata.get("endpoint") != endpoint
            or metadata.get("parameters") != {"year": 2023, "team": "Texas", "seasonType": "both"}
            or metadata.get("http_status") != 200):
        raise ValueError("Unexpected source, request scope, or response status.")
    # Retrieval timestamps may have microseconds, unlike game DATETIME(3).
    retrieved = datetime.fromisoformat(metadata["retrieved_at_utc"])
    if retrieved.utcoffset() is None:
        raise ValueError("Retrieval timestamp must include a timezone.")
    return json.loads(body)


def normalize_schedule(schedule):
    if not isinstance(schedule, list) or not schedule:
        raise ValueError("Expected a nonempty schedule list.")
    teams, games, seen = {}, [], set()
    for game in schedule:
        source_id = unsigned(game["id"])
        if source_id in seen:
            raise ValueError("Duplicate source game ID.")
        seen.add(source_id)
        if game.get("season") != 2023 or game.get("completed") is not True:
            raise ValueError("Expected completed season-2023 games.")
        if "Texas" not in (game.get("homeTeam"), game.get("awayTeam")):
            raise ValueError("Expected Texas in each game.")
        if game.get("seasonType") not in ("regular", "postseason"):
            raise ValueError("Unsupported season classification.")
        if type(game.get("neutralSite")) is not bool:
            raise ValueError("Neutral-site flag must be a boolean.")
        for side in ("home", "away"):
            team_id = unsigned(game[side + "Id"])
            name = text(game[side + "Team"], 128)
            if team_id in teams and teams[team_id]["name"] != name:
                raise ValueError("One source team ID has conflicting names.")
            teams[team_id] = {"source_team_id": team_id, "name": name}
        if game["homeId"] == game["awayId"]:
            raise ValueError("A team cannot play itself.")
        venue = game.get("venue")
        games.append({
            "source_game_id": source_id, "season": unsigned(game["season"], 65535),
            "season_type": game["seasonType"], "start_time_utc": utc_datetime(game["startDate"]),
            # Source references are resolved to internal foreign keys during import.
            "home_source_team_id": game["homeId"], "away_source_team_id": game["awayId"],
            "home_points": unsigned(game["homePoints"], 65535),
            "away_points": unsigned(game["awayPoints"], 65535),
            "neutral_site": game["neutralSite"], "venue": None if venue is None else text(venue, 255),
        })
    return sorted(teams.values(), key=lambda row: row["source_team_id"]), sorted(
        games, key=lambda row: row["source_game_id"]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("stats", type=Path)
    args = parser.parse_args()
    try:
        schedule = load_verified(args.schedule, "https://api.collegefootballdata.com/games")
        stats = load_verified(args.stats, "https://api.collegefootballdata.com/games/teams")
        teams, games = normalize_schedule(schedule)
        rows = normalize_stats(stats, schedule)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        raise SystemExit("Dry run failed: check archive integrity, metadata, and record values.") from None
    print("Both response hashes, sizes, and request scopes verified.")
    print(f"Dry run: {len(teams)} teams, {len(games)} games, {len(rows)} team-game stat rows.")
    print("No API calls, credentials, database connections, or file writes.")
    print("Internal IDs and import-run references remain to be assigned during database loading.")


if __name__ == "__main__":
    main()
