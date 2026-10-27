"""Fetch Texas 2023 team box scores and compare them with a saved schedule."""

import argparse
import json

from fetch_games import PARAMETERS, ROOT, fetch_sample


def validate(games, schedule):
    expected = {game["id"]: game for game in schedule}
    seen = set()
    categories = set()
    for game in games:
        if not isinstance(game, dict) or type(game.get("id")) is not int:
            raise ValueError("Invalid game object or ID.")
        game_id = game["id"]
        if game_id in seen or game_id not in expected:
            raise ValueError("Duplicate or unexpected game ID.")
        seen.add(game_id)
        teams = game.get("teams")
        if not isinstance(teams, list) or len(teams) != 2:
            raise ValueError("Expected both teams for every game.")
        reference = expected[game_id]
        sides = set()
        for team in teams:
            if not isinstance(team, dict):
                raise ValueError("Invalid team object.")
            side = team.get("homeAway")
            if side not in ("home", "away") or side in sides:
                raise ValueError("Invalid or duplicate team side.")
            sides.add(side)
            if any(team.get(field) != reference[side + suffix] for field, suffix in
                   (("teamId", "Id"), ("team", "Team"), ("points", "Points"))):
                raise ValueError("Team identity or score differs from saved schedule.")
            stats = team.get("stats")
            if not isinstance(stats, list) or not stats:
                raise ValueError("Missing team statistics.")
            team_categories = set()
            for stat in stats:
                if not isinstance(stat, dict):
                    raise ValueError("Invalid statistic object.")
                category = stat.get("category")
                if not isinstance(category, str) or not category or category in team_categories:
                    raise ValueError("Missing or duplicate stat category for a team.")
                if not isinstance(stat.get("stat"), str) or not stat["stat"].strip():
                    raise ValueError("Expected nonempty source stat values as strings.")
                team_categories.add(category)
                categories.add(category)
    missing = set(expected) - seen
    if missing:
        raise ValueError(f"Statistics missing for {len(missing)} schedule games.")
    return len(seen), len(categories)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", help="Path to the previously validated schedule response.json")
    args = parser.parse_args()
    try:
        schedule = json.loads((ROOT / args.schedule).read_text())
        if not isinstance(schedule, list) or not schedule:
            raise ValueError()
        if any(not isinstance(game, dict) for game in schedule):
            raise ValueError()
        ids = [game["id"] for game in schedule]
        if any(type(i) is not int for i in ids) or len(set(ids)) != len(ids):
            raise ValueError()
        if any(game.get("season") != 2023 or "Texas" not in
               (game.get("homeTeam"), game.get("awayTeam")) for game in schedule):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise SystemExit("Cannot load a valid, unique Texas 2023 schedule; no request made.") from None

    games = fetch_sample(
        "https://api.collegefootballdata.com/games/teams", PARAMETERS, "cfbd-team-stats"
    )
    try:
        count, category_count = validate(games, schedule)
    except (ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Statistics validation failed: {error}") from None
    print(f"Cross-checks passed: {count} games, both teams per game; {category_count} distinct stat categories.")
    print("Statistical values still require inspection and official box-score comparison.")


if __name__ == "__main__":
    main()
