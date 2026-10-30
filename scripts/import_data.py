"""Prepare verified archives offline; import through a supplied dedicated connection.

The CLI is dry-run only. Connection setup and credentials are deliberately absent.
"""

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from normalize_games import load_verified, normalize_schedule
from normalize_stats import normalize as normalize_stats

ROOT = Path(__file__).resolve().parents[1]
GAME_COLUMNS = (
    "source_game_id", "season", "season_type", "start_time_utc", "home_team_id",
    "away_team_id", "home_points", "away_points", "neutral_site", "venue", "ingestion_run_id",
)
STAT_COLUMNS = (
    "game_id", "team_id", "ingestion_run_id", "first_downs", "total_yards",
    "passing_yards", "rushing_yards", "rushing_attempts", "pass_completions",
    "pass_attempts", "third_down_conversions", "third_down_attempts",
    "fourth_down_conversions", "fourth_down_attempts", "penalty_count", "penalty_yards",
    "interceptions_thrown", "fumbles_lost", "turnovers", "possession_seconds",
)


def _upsert(table, columns, keys):
    # Identifiers come ONLY from developer-owned constants, never downloaded data.
    assignments = ", ".join(f"{column}=incoming.{column}" for column in columns if column not in keys)
    return (f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join(['%s'] * len(columns))}) AS incoming "
            f"ON DUPLICATE KEY UPDATE {assignments}")


TEAM_SQL = _upsert("teams", ("source_team_id", "name", "ingestion_run_id"), ("source_team_id",))
GAME_SQL = _upsert("games", GAME_COLUMNS, ("source_game_id",))
STAT_SQL = _upsert("team_game_stats", STAT_COLUMNS, ("game_id", "team_id"))
RUN_SQL = """INSERT INTO ingestion_runs
    (source, endpoint, request_parameters, source_retrieved_at_utc, response_sha256,
     raw_file_path, importer_version, importer_worktree_dirty, started_at_utc, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
FINISH_SQL = """UPDATE ingestion_runs SET status=%s, finished_at_utc=%s,
    records_processed=%s, error_summary=%s WHERE ingestion_run_id=%s"""


@dataclass
class PreparedImport:
    teams: list
    games: list
    stats: list
    sources: list
    importer_version: str | None
    worktree_dirty: bool | None


def git_version():
    """Fixed read-only commands; include untracked code in the dirty flag."""
    try:
        version = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, check=True, timeout=5,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT,
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        return version, bool(dirty)
    except (OSError, subprocess.SubprocessError):
        return None, None


def prepare(schedule_path, stats_path, *, archive_root=ROOT / "data/raw"):
    """Verify and normalize both sources before any database operation."""
    archive_root = archive_root.resolve()
    sources, records = [], []
    for path, endpoint in (
        (schedule_path, "https://api.collegefootballdata.com/games"),
        (stats_path, "https://api.collegefootballdata.com/games/teams"),
    ):
        path = Path(path).resolve()
        relative = path.relative_to(archive_root)  # Reject files outside the private archive.
        data, metadata = load_verified(path, endpoint, include_metadata=True)
        if len(relative.as_posix()) > 512:
            raise ValueError("Archive path exceeds the schema column limit.")
        sources.append({**metadata, "raw_file_path": relative.as_posix()})
        records.append(data)
    teams, games = normalize_schedule(records[0])
    stats = normalize_stats(records[1], records[0])
    version, dirty = git_version()
    return PreparedImport(teams, games, stats, sources, version, dirty)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ImportFailure(RuntimeError):
    """Sanitized failure; callers must not log underlying connector exceptions."""


def import_prepared(connection, prepared):
    """Use a fresh dedicated Connector/Python-style connection, autocommit=False.

    Owns its transactions but not the connection lifetime. Never pass a shared
    runtime connection. Only call with output from prepare(), not model input.
    """
    if connection.autocommit or connection.in_transaction:
        raise ImportFailure("Requires an idle dedicated connection with autocommit disabled.")
    try:
        cursor = connection.cursor()
    except Exception:
        raise ImportFailure("Could not open import cursor; no import statements sent.") from None
    run_ids = []
    try:
        # Persist attempts first; a crash may leave 'running' rows to reconcile.
        connection.start_transaction()
        for source in prepared.sources:
            retrieved = datetime.fromisoformat(source["retrieved_at_utc"]).astimezone(
                timezone.utc).replace(tzinfo=None)
            cursor.execute(RUN_SQL, (
                source["source"], source["endpoint"], json.dumps(source["parameters"]),
                retrieved, source["sha256"], source["raw_file_path"],
                prepared.importer_version, prepared.worktree_dirty, _now(), "running",
            ))
            run_ids.append(cursor.lastrowid)
        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        _close_cursor(cursor)
        raise ImportFailure("Could not persist import attempts; inspect run state before retrying.") from None

    stage = "writes"
    try:
        connection.start_transaction()
        team_ids, game_ids = {}, {}
        for team in prepared.teams:
            cursor.execute(TEAM_SQL, (team["source_team_id"], team["name"], run_ids[0]))
            cursor.execute("SELECT team_id FROM teams WHERE source_team_id=%s", (team["source_team_id"],))
            team_ids[team["source_team_id"]] = cursor.fetchone()[0]
        for game in prepared.games:
            row = {**game, "home_team_id": team_ids[game["home_source_team_id"]],
                   "away_team_id": team_ids[game["away_source_team_id"]], "ingestion_run_id": run_ids[0]}
            cursor.execute(GAME_SQL, tuple(row[column] for column in GAME_COLUMNS))
            cursor.execute("SELECT game_id FROM games WHERE source_game_id=%s", (game["source_game_id"],))
            game_ids[game["source_game_id"]] = cursor.fetchone()[0]
        for stat in prepared.stats:
            row = {**stat, "game_id": game_ids[stat["source_game_id"]],
                   "team_id": team_ids[stat["source_team_id"]], "ingestion_run_id": run_ids[1]}
            # Values are a separate tuple. Never interpolate source values into SQL.
            cursor.execute(STAT_SQL, tuple(row[column] for column in STAT_COLUMNS))
        for run_id, count in zip(run_ids, (len(prepared.teams) + len(prepared.games), len(prepared.stats))):
            cursor.execute(FINISH_SQL, ("succeeded", _now(), count, None, run_id))
        stage = "commit"
        connection.commit()  # Dataset and success statuses commit together.
    except Exception:
        try:
            connection.rollback()
        except Exception:
            raise ImportFailure("Rollback could not be confirmed; inspect database state before retrying.") from None
        if stage == "commit":
            # A lost connection can hide a successful commit. Do not label it failed.
            raise ImportFailure("Commit outcome is uncertain; reconcile run and dataset state before retrying.") from None
        try:
            connection.start_transaction()
            for run_id in run_ids:
                cursor.execute(FINISH_SQL, ("failed", _now(), 0, "Dataset import failed; changes rolled back.", run_id))
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise ImportFailure("Dataset rolled back; failure status could not be confirmed. Reconcile run state.") from None
        raise ImportFailure("Dataset import failed and rolled back; failure status recorded.") from None
    finally:
        _close_cursor(cursor)
    return {"run_ids": run_ids, "teams": len(prepared.teams), "games": len(prepared.games), "stats": len(prepared.stats)}


def _close_cursor(cursor):
    # Cleanup must not replace a sanitized failure or obscure a committed result.
    # The caller must close the dedicated connection regardless of outcome.
    try:
        cursor.close()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schedule", type=Path)
    parser.add_argument("stats", type=Path)
    args = parser.parse_args()
    try:
        data = prepare(args.schedule, args.stats)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        raise SystemExit("Preparation failed: check saved archives and normalized values.") from None
    print(f"Prepared {len(data.teams)} teams, {len(data.games)} games, {len(data.stats)} statistics rows.")
    print(f"Importer commit: {data.importer_version or 'unknown'}; uncommitted changes: {data.worktree_dirty}")
    print("Dry run only: no database connection, credentials, or writes.")


if __name__ == "__main__":
    main()
