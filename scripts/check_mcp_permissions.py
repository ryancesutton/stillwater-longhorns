"""Real local MySQL authorization checks; never print credential contents."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKER = "/Applications/Docker.app/Contents/Resources/bin/docker"


def mcp_query(statement):
    return account_query("stillwater_mcp", ROOT / "secrets/mysql-mcp-password", statement)


def account_query(user, password_path, statement):
    if user not in ("stillwater_mcp", "stillwater_import"):
        raise ValueError("Unexpected runtime identity.")
    password = password_path.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", password):
        raise SystemExit("Unexpected generated credential format; no request made.")
    config = "[client]\nuser=" + user + "\npassword=" + password + "\nprotocol=tcp\nhost=127.0.0.1\n"
    # Secret goes only through stdin into a temporary private file, not argv/env.
    command = '''umask 077
config=$(mktemp)
trap 'rm -f "$config"' EXIT
cat > "$config"
mysql --defaults-extra-file="$config" --batch --database=stillwater --execute="$1"
'''
    return subprocess.run(
        [DOCKER, "compose", "exec", "-T", "db", "sh", "-eu", "-c", command, "sh", statement],
        cwd=ROOT, input=config, text=True, capture_output=True, timeout=30,
    )


def main():
    identity = mcp_query("SELECT CURRENT_USER();")
    if identity.returncode or "stillwater_mcp@%" not in identity.stdout:
        raise SystemExit("MCP authentication check failed; details suppressed.")
    print("PASS: authenticated as stillwater_mcp@%.")
    for view in ("briefing_teams", "briefing_games", "briefing_team_game_stats"):
        result = mcp_query(f"SELECT * FROM {view} LIMIT 1;")
        if result.returncode:
            raise SystemExit(f"FAIL: authorized read of {view}.")
        print(f"PASS: authorized read of {view} (currently empty).")
    denied = [
        ("base teams", "SELECT * FROM teams LIMIT 1;", "1142"),
        ("base games", "SELECT * FROM games LIMIT 1;", "1142"),
        ("base stats", "SELECT * FROM team_game_stats LIMIT 1;", "1142"),
        ("import metadata", "SELECT * FROM ingestion_runs LIMIT 1;", "1142"),
        ("private fixture", "SELECT * FROM private_security_fixture;", "1142"),
        ("dataset insert", "INSERT INTO teams (source_team_id,name,ingestion_run_id) VALUES (999999,'Denied',0);", "1142"),
        ("dataset update", "UPDATE games SET home_points=0 WHERE game_id=0;", "1142"),
        ("dataset delete", "DELETE FROM team_game_stats WHERE game_id=0;", "1142"),
        ("view write", "UPDATE briefing_teams SET name='Denied' WHERE team_id=0;", "1142"),
        ("schema change", "CREATE TABLE forbidden_mcp_fixture (id INT);", "1142"),
    ]
    for label, statement, code in denied:
        result = mcp_query(statement)
        if not result.returncode or f"ERROR {code}" not in result.stderr:
            raise SystemExit(f"FAIL: expected privilege denial for {label}; inspect state before proceeding.")
        print(f"PASS: {label} denied by MySQL (error {code}).")


if __name__ == "__main__":
    main()
