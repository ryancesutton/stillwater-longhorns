"""Exercise importer grants with rollback-only fixtures on the empty demo DB."""

from check_mcp_permissions import ROOT, account_query
from check_schema import FIXTURES, assert_empty


def query(statement):
    return account_query("stillwater_import", ROOT / "secrets/mysql-import-password", statement)


def main():
    assert_empty()
    result = query("SELECT CURRENT_USER();")
    if result.returncode or "stillwater_import@%" not in result.stdout:
        raise SystemExit("Import authentication failed; details suppressed.")
    print("PASS: authenticated as stillwater_import@%.")
    result = query(FIXTURES + """
INSERT INTO team_game_stats (game_id,team_id,ingestion_run_id,rushing_yards)
VALUES (@game,@home,@run,10);
UPDATE teams SET name='Fixture updated' WHERE team_id=@home;
UPDATE games SET home_points=14 WHERE game_id=@game;
UPDATE team_game_stats SET rushing_yards=11 WHERE game_id=@game AND team_id=@home;
UPDATE ingestion_runs SET status='succeeded',finished_at_utc=UTC_TIMESTAMP(6),
 records_processed=4 WHERE ingestion_run_id=@run;
SELECT COUNT(*) FROM teams;
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM team_game_stats;
SELECT COUNT(*) FROM ingestion_runs;
ROLLBACK;
""")
    if result.returncode:
        raise SystemExit("FAIL: required importer operations; raw database error suppressed.")
    if result.stdout.strip().splitlines()[-8::2] != ['COUNT(*)'] * 4:
        raise SystemExit("Unexpected fixture query output; inspect before proceeding.")
    if result.stdout.strip().splitlines()[-7::2] != ['2', '1', '1', '1']:
        raise SystemExit("Unexpected fixture counts; inspect before proceeding.")
    assert_empty()
    print("PASS: SELECT/INSERT/UPDATE on all four tables; fixture rows rolled back.")
    for label, statement in (
        ("private-table read", "SELECT * FROM private_security_fixture;"),
        ("dataset delete", "DELETE FROM teams WHERE team_id=0;"),
        ("schema creation", "CREATE TABLE forbidden_import_fixture (id INT);"),
        ("schema alteration", "ALTER TABLE teams ADD COLUMN forbidden_test INT;"),
    ):
        result = query(statement)
        if not result.returncode or "ERROR 1142" not in result.stderr:
            raise SystemExit(f"FAIL: expected privilege denial for {label}; inspect database.")
        print(f"PASS: {label} denied by MySQL (error 1142).")
    assert_empty()


if __name__ == "__main__":
    main()
