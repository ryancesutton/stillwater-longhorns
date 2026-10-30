"""Local-only runtime connections; no administrator credential access."""

import re
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def connect_import():
    return _connect("stillwater_import", "mysql-import-password")


def connect_mcp():
    return _connect("stillwater_mcp", "mysql-mcp-password")


def _connect(user, filename):
    import mysql.connector

    path = ROOT / "secrets" / filename
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("Credential file must have owner-only permissions.")
    password = path.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", password):
        raise ValueError("Unexpected credential format.")
    connection = mysql.connector.connect(
        host="127.0.0.1", port=3307, database="stillwater",
        user=user, password=password, autocommit=False,
        connection_timeout=10, read_timeout=30, write_timeout=30,
        allow_local_infile=False, use_pure=True, time_zone="+00:00",
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT CURRENT_USER(), VERSION()")
        identity, version = cursor.fetchone()
        cursor.close()
        if identity != user + "@%" or not version.startswith("8.4."):
            raise ValueError("Unexpected identity or server version.")
        connection.rollback()  # Ensure an idle connection before importer ownership.
        return connection
    except Exception:
        connection.close()
        raise
