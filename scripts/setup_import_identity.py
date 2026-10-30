"""One-time local importer account setup; generated credentials stay private."""

import os
import secrets

from setup_mcp_identity import ROOT, admin


def main():
    check = admin("SELECT COUNT(*) FROM mysql.user WHERE User='stillwater_import';")
    if check.returncode or check.stdout.strip().splitlines()[-1:] != ["0"]:
        raise SystemExit("Account may already exist or preflight failed. No credentials changed.")
    path = ROOT / "secrets/mysql-import-password"
    password = secrets.token_hex(32)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit("Password file exists; reconcile setup before retrying. File unchanged.") from None
    with os.fdopen(fd, "w") as file:
        file.write(password)
    # Only generated hexadecimal is interpolated; never user or model input.
    result = admin(
        f"CREATE USER 'stillwater_import'@'%' IDENTIFIED BY '{password}' "
        "WITH MAX_USER_CONNECTIONS 2;\n"
        + (ROOT / "db/import-grants.sql").read_text()
    )
    if result.returncode:
        raise SystemExit("Setup failed or partially completed. Secret preserved; inspect grants before retrying. Raw errors suppressed.")
    print("Import identity created; SELECT/INSERT/UPDATE granted on four named tables only.")
    print("Credential saved privately, not displayed.")


if __name__ == "__main__":
    main()
