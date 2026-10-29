"""Offline conversion of selected CFBD stats; no secrets, network, or SQL."""

import argparse
import json
import re
from pathlib import Path

from fetch_team_stats import validate


SCALARS = {
    "firstDowns": "first_downs", "totalYards": "total_yards",
    "netPassingYards": "passing_yards", "rushingYards": "rushing_yards",
    "rushingAttempts": "rushing_attempts", "interceptions": "interceptions_thrown",
    "fumblesLost": "fumbles_lost", "turnovers": "turnovers",
}
PAIRS = {
    "completionAttempts": ("pass_completions", "pass_attempts"),
    "thirdDownEff": ("third_down_conversions", "third_down_attempts"),
    "fourthDownEff": ("fourth_down_conversions", "fourth_down_attempts"),
    "totalPenaltiesYards": ("penalty_count", "penalty_yards"),
}


def integer(value, *, signed=False):
    """Missing is None; malformed or out-of-column-range values are rejected."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+" if signed else r"\d+", value, flags=re.ASCII):
        raise ValueError("Expected an integer stat string.")
    number = int(value)
    low, high = (-2147483648, 2147483647) if signed else (0, 65535)
    if not low <= number <= high:
        raise ValueError("Stat exceeds its proposed SQL column range.")
    return number


def pair(value, *, bounded=True):
    if value is None:
        return None, None
    if not isinstance(value, str) or not re.fullmatch(r"\d+-\d+", value, flags=re.ASCII):
        raise ValueError("Expected two counts separated by a hyphen.")
    first, second = map(integer, value.split("-"))
    if bounded and first > second:
        raise ValueError("Completions or conversions exceed attempts.")
    return first, second


def possession(value):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d+:[0-5]\d", value, flags=re.ASCII):
        raise ValueError("Expected possession time as minutes:seconds.")
    minutes, seconds = map(int, value.split(":"))
    result = minutes * 60 + seconds
    if result > 4294967295:
        raise ValueError("Possession time exceeds its proposed SQL column range.")
    return result


def normalize_team(stats):
    values = {}
    for stat in stats:
        category = stat["category"]
        if category in values:
            raise ValueError("Duplicate stat category.")
        values[category] = stat["stat"]
    row = {
        column: integer(values.get(category), signed=column.endswith("_yards"))
        for category, column in SCALARS.items()
    }
    for category, columns in PAIRS.items():
        row.update(zip(columns, pair(values.get(category), bounded=category != "totalPenaltiesYards")))
    row["possession_seconds"] = possession(values.get("possessionTime"))
    for total, components in (
        ("total_yards", ("passing_yards", "rushing_yards")),
        ("turnovers", ("interceptions_thrown", "fumbles_lost")),
    ):
        if all(row[key] is not None for key in (total, *components)):
            if row[total] != sum(row[key] for key in components):
                raise ValueError("Stat totals are inconsistent.")
    return row


def normalize(games, schedule):
    """Verify coverage, duplicate IDs, participants and scores before conversion."""
    if not isinstance(schedule, list) or not schedule or not isinstance(games, list) or not games:
        raise ValueError("Expected nonempty schedule and stat lists.")
    ids = [game["id"] for game in schedule]
    if any(type(i) is not int for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Schedule IDs must be unique integers.")
    validate(games, schedule)
    rows = []
    for game in games:
        for team in game["teams"]:
            if type(team["teamId"]) is not int or team["teamId"] < 0:
                raise ValueError("Invalid source team ID.")
            rows.append({
                "source_game_id": game["id"], "source_team_id": team["teamId"],
                **normalize_team(team["stats"]),
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("stats", type=Path)
    args = parser.parse_args()
    try:
        rows = normalize(json.loads(args.stats.read_text()), json.loads(args.schedule.read_text()))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise SystemExit("Normalization failed: check input structure, relationships, and stat values.") from None
    print(f"Normalized {len(rows)} team-game records in memory; no files or database modified.")
    print("Source IDs are retained; internal database IDs and ingestion_run_id are assigned during import.")
    print(json.dumps(rows[0], indent=2))


if __name__ == "__main__":
    main()
