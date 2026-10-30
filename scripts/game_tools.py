"""Bounded retrieval functions: approved views only, no arbitrary SQL interface."""

from datetime import datetime

from local_db import connect_mcp

GAME_SELECT = """SELECT /*+ MAX_EXECUTION_TIME(2000) */
 g.source_game_id, g.season, g.season_type, g.start_time_utc,
 h.name AS home_team, a.name AS away_team, g.home_points, g.away_points,
 g.neutral_site, g.venue, g.source, g.endpoint,
 g.source_retrieved_at_utc, g.response_sha256
 FROM briefing_games AS g
 JOIN briefing_teams AS h ON h.team_id=g.home_team_id
 JOIN briefing_teams AS a ON a.team_id=g.away_team_id
"""
STAT_SELECT = """SELECT /*+ MAX_EXECUTION_TIME(2000) */
 t.source_team_id, t.name AS team, s.first_downs, s.total_yards,
 s.passing_yards, s.rushing_yards, s.rushing_attempts, s.pass_completions,
 s.pass_attempts, s.third_down_conversions, s.third_down_attempts,
 s.fourth_down_conversions, s.fourth_down_attempts, s.penalty_count,
 s.penalty_yards, s.interceptions_thrown, s.fumbles_lost, s.turnovers,
 s.possession_seconds, s.source, s.endpoint,
 s.source_retrieved_at_utc, s.response_sha256
 FROM briefing_team_game_stats AS s
 JOIN briefing_teams AS t ON t.team_id=s.team_id
 JOIN briefing_games AS g ON g.game_id=s.game_id
 WHERE g.source_game_id=%s ORDER BY t.source_team_id LIMIT 2
"""


def _bounded_int(value, low, high, field):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{field} must be an integer from {low} to {high}.")


def _rows(cursor):
    # DATETIME columns follow our UTC convention; explicit Z avoids ambiguity.
    return [{key: value.isoformat(timespec="milliseconds") + "Z" if isinstance(value, datetime)
             else value for key, value in row.items()} for row in cursor.fetchall()]


def _query(operation):
    connection = None
    try:
        connection = connect_mcp()  # Only MCP credential is read on this path.
        connection.start_transaction(readonly=True)
        cursor = connection.cursor(dictionary=True)
        try:
            result = operation(cursor)
        finally:
            cursor.close()
        connection.rollback()
        return result
    except Exception:
        # Do not send SQL, connection strings, credentials or raw exceptions to models.
        return {"status": "error", "code": "retrieval_unavailable"}
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def list_games(season=2023, limit=20):
    """List Texas games for one season, with a hard maximum of 25 records."""
    _bounded_int(season, 1869, 2100, "season")
    _bounded_int(limit, 1, 25, "limit")

    def operation(cursor):
        cursor.execute(GAME_SELECT + """ WHERE g.season=%s
         AND (h.name=%s OR a.name=%s)
         ORDER BY g.start_time_utc,g.source_game_id LIMIT %s""", (season, "Texas", "Texas", limit + 1))
        rows = _rows(cursor)
        return {"status": "ok", "games": rows[:limit], "truncated": len(rows) > limit}
    return _query(operation)


def get_game_data(source_game_id):
    """Retrieve one Texas game by CFBD source ID, not the internal MySQL ID."""
    _bounded_int(source_game_id, 1, 9223372036854775807, "source_game_id")

    def operation(cursor):
        cursor.execute(GAME_SELECT + """ WHERE g.source_game_id=%s
         AND (h.name=%s OR a.name=%s) LIMIT 1""", (source_game_id, "Texas", "Texas"))
        games = _rows(cursor)
        if not games:
            return {"status": "not_found", "source_game_id": source_game_id}
        cursor.execute(STAT_SELECT, (source_game_id,))
        stats = _rows(cursor)
        return {"status": "ok", "game": games[0], "team_stats": stats,
                "missing_team_stats": len(stats) != 2,
                "evidence_ref": f"cfbd:game:{source_game_id}",
                "limitations": ["Selected team stats only; return and detailed defensive stats excluded."]}
    return _query(operation)
