# Local Schema Checkpoint

The reviewed four-table schema was applied to the previously empty `stillwater` database on local Docker MySQL 8.4.13. The authenticated setup session used `root@localhost`. No changes were made to the older host MySQL installation.

Verified tables: `ingestion_runs`, `teams`, `games`, and `team_game_stats`, all InnoDB. Primary keys, unique keys, foreign keys, and CHECK constraints were inspected in `information_schema`.

`python scripts/check_schema.py` performed these real database checks:

| Check | Result |
|---|---|
| Valid related rows, nullable stats, negative rushing yards | Accepted |
| Duplicate source team ID | Rejected, error 1062 |
| Nonexistent team foreign key in stats | Rejected, error 1452 |
| Pass completions greater than attempts | Rejected, error 3819 |
| Same team as both game participants | Rejected, error 3819 |

Every case used a transaction, with no commit. After each case, counts across all four tables were verified as zero. Failed SQL ended the client session and rolled back its open transaction. Auto-increment counters can advance despite rollback; gaps are expected and are not missing records.

These are representative checks, not exhaustive verification of every constraint. The schema script is not idempotent; do not rerun it against these existing tables.

The administrator helper `scripts/db-admin.sh` reads the mounted password inside the container using a temporary owner-only client configuration, removes that configuration on exit, and does not print the password. It is for local setup only, not agent runtime. The password is still accessible to the host user and Docker administrators; the Compose secret file is not an encrypted vault.

Pending: import/MCP identities, approved views, denied-access checks, real importer integration and repeat imports, MCP tools, and agent behavior. Administrator success does not establish restricted-account authorization.
