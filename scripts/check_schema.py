"""Local administrator integration checks; fixtures are rolled back, never committed.

Requires the empty demo database. Auto-increment counters may advance.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sql(statement):
    return subprocess.run(["sh", "scripts/db-admin.sh"], cwd=ROOT,
                          input=statement, text=True, capture_output=True, timeout=30)


COUNTS = """SELECT (SELECT COUNT(*) FROM teams) + (SELECT COUNT(*) FROM games)
    + (SELECT COUNT(*) FROM team_game_stats) + (SELECT COUNT(*) FROM ingestion_runs);"""
FIXTURES = """
START TRANSACTION;
INSERT INTO ingestion_runs
(source, endpoint, request_parameters, source_retrieved_at_utc, response_sha256,
 raw_file_path, started_at_utc, status)
VALUES ('fixture', 'fixture', '{}', UTC_TIMESTAMP(6), REPEAT('a',64),
        'fixture', UTC_TIMESTAMP(6), 'running');
SET @run=LAST_INSERT_ID();
INSERT INTO teams (source_team_id,name,ingestion_run_id) VALUES (900001,'Fixture A',@run);
SET @home=LAST_INSERT_ID();
INSERT INTO teams (source_team_id,name,ingestion_run_id) VALUES (900002,'Fixture B',@run);
SET @away=LAST_INSERT_ID();
INSERT INTO games
(source_game_id,season,season_type,start_time_utc,home_team_id,away_team_id,
 home_points,away_points,neutral_site,ingestion_run_id)
VALUES (900001,2023,'regular','2023-09-02 00:00:00',@home,@away,7,0,0,@run);
SET @game=LAST_INSERT_ID();
"""


def assert_empty():
    result = sql(COUNTS)
    if result.returncode or result.stdout.strip().splitlines()[-1:] != ["0"]:
        raise SystemExit("Requires an empty demo database; no fixture checks started.")


def main():
    assert_empty()
    cases = [
        ("valid rows, missing values, and negative yardage", """INSERT INTO team_game_stats
         (game_id,team_id,ingestion_run_id,rushing_yards)
         VALUES (@game,@home,@run,-6);""", None),
        ("unique source team ID", """INSERT INTO teams (source_team_id,name,ingestion_run_id)
         VALUES (900001,'Duplicate',@run);""", "ERROR 1062"),
        ("foreign key", """INSERT INTO team_game_stats (game_id,team_id,ingestion_run_id)
         VALUES (@game,999999999,@run);""", "ERROR 1452"),
        ("completions cannot exceed attempts", """INSERT INTO team_game_stats
         (game_id,team_id,ingestion_run_id,pass_completions,pass_attempts)
         VALUES (@game,@home,@run,5,4);""", "ERROR 3819"),
        ("game participants must differ", "UPDATE games SET away_team_id=@home WHERE game_id=@game;", "ERROR 3819"),
    ]
    for label, statement, expected_error in cases:
        result = sql(FIXTURES + statement + "\nROLLBACK;")
        if expected_error is None:
            passed = result.returncode == 0
        else:
            passed = result.returncode != 0 and expected_error in result.stderr
        if not passed:
            raise SystemExit(f"FAIL: {label}; inspect the database before proceeding.")
        # SQL error ends the client session; InnoDB rolls its open transaction back.
        assert_empty()
        print(f"PASS: {label}; no fixture rows retained.")


if __name__ == "__main__":
    main()
