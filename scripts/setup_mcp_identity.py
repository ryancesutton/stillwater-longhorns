"""One-time local administrative setup. Never prints generated credentials."""

import os
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def admin(sql):
    return subprocess.run(["sh", "scripts/db-admin.sh"], cwd=ROOT, input=sql,
                          text=True, capture_output=True, timeout=60)


def main():
    check = admin("SELECT COUNT(*) FROM mysql.user WHERE User IN "
                  "('stillwater_mcp','stillwater_view_owner');")
    if check.returncode or check.stdout.strip().splitlines()[-1:] != ["0"]:
        raise SystemExit("Accounts may already exist or preflight failed. Stop and inspect; no credentials changed.")
    folder = ROOT / "secrets"
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / "mysql-mcp-password"
    password = secrets.token_hex(32)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit("Password file already exists. Stop and reconcile setup; it was not read or changed.") from None
    with os.fdopen(fd, "w") as file:
        file.write(password)
    # Generated hex is restricted to [0-9a-f]; never interpolate user/model input.
    # Password SQL travels on stdin, not command arguments, and is never printed.
    statements = (
        "CREATE USER 'stillwater_view_owner'@'localhost' ACCOUNT LOCK;\n"
        f"CREATE USER 'stillwater_mcp'@'%' IDENTIFIED BY '{password}' "
        "WITH MAX_USER_CONNECTIONS 4;\n"
        + (ROOT / "db/mcp-views.sql").read_text()
    )
    result = admin(statements)
    if result.returncode:
        raise SystemExit("Setup failed or partially completed. Secret file preserved; inspect account/view state before retrying. Raw SQL errors suppressed.")
    print("Created MCP identity, locked view owner, three read-only grants, and private dummy fixture.")
    print("Password saved privately; not displayed. Verify grants before using this identity.")


if __name__ == "__main__":
    main()
