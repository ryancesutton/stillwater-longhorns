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

Pending: real importer integration and repeat imports, MCP tools, and agent behavior. Administrator success does not establish restricted-account authorization; the MCP checks below use its own identity.

## MCP Authorization Checkpoint

Created `stillwater_mcp`@`%` and locked `stillwater_view_owner`@`localhost`. The owner defines three explicit-column SQL SECURITY DEFINER views; MCP has only SELECT on those named views. Actual SHOW GRANTS output and view definers/security modes were inspected. No roles or broad data grants were present.

`python scripts/check_mcp_permissions.py` authenticated as MCP over container-local TCP and successfully queried all three empty views. Ten denied operations returned privilege error 1142: reads of teams, games, team_game_stats, ingestion_runs and private_security_fixture; dataset insert/update/delete; view update; and CREATE TABLE. Post-check administrator reads confirmed the four dataset/run tables remained empty and the single harmless private fixture was unchanged.

The added `private_security_fixture` table is only a harmless security-test fixture, not a new application feature. No import account was created in this step. At this checkpoint those runtime and integration checks remained pending; subsequent host import and populated view checks are recorded below. OS isolation, MCP tool validation, and agent behavior still remain pending.

## Import Authorization Checkpoint

Created `stillwater_import`@`%` with SELECT, INSERT, UPDATE on the four dataset/run tables only. Inspected SHOW GRANTS. Container-local TCP authentication succeeded. Real SELECT/INSERT/UPDATE fixtures passed on all four tables, then rolled back. Private-fixture reads, DELETE, CREATE TABLE, and ALTER TABLE each returned privilege error 1142. Dataset/run tables remained empty and the private fixture was unchanged. No real football data had been loaded at this checkpoint; subsequent imports are recorded below.

## Real Importer Integration

Installed pinned MySQL Connector/Python 26.10.0 in `.venv`. Host Python authenticated as `stillwater_import` over `127.0.0.1:3307` and verified MySQL 8.4.x before writes. Loaded the verified CFBD archives: 15 teams, 14 games, 28 statistics rows, with successful schedule/stat run IDs 7 and 8. A second load created successful run IDs 9 and 10; dataset counts and internal team/game/stat identities stayed stable. Auto-increment gaps from earlier fixture tests are expected.

A controlled exception before the first statistics upsert, after earlier team/game updates, exercised rollback in the real MySQL transaction. Full dataset snapshots before and after were equal, including the temporary team-name change being undone. Two new attempt rows were marked failed with zero persisted records. This tests application-triggered failure with a live connection; actual network loss and ambiguous server-commit outcomes remain simulated only.

The MCP account then read 15 teams, 14 games and 28 stats through the approved views. Its private-fixture read remained denied (1142). Import-run records indicate dirty working-tree code, so the recorded Git commit alone does not reproduce these exact executions. All 14 offline tests passed and pip reported no broken requirements; this is not a dependency vulnerability audit.

Real loading command (omit `--write` for a dry run):

```bash
python scripts/import_data.py \
  data/raw/cfbd-games-20261027T015648114714Z/response.json \
  data/raw/cfbd-team-stats-20261027T020832174803Z/response.json --write
```

Earlier empty-table results describe their checkpoints; the four tables now contain imported data and run history. Empty-database schema/import grant fixture scripts must not be rerun on this populated database. Runtime OS isolation, MCP tools, agent behavior, and remote deployment remain pending.
