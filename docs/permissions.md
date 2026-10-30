# Permission Plan

Status: local MCP database authorization is implemented and tested. `stillwater_mcp` can SELECT three approved views only. The locked `stillwater_view_owner` defines those views. The import identity is also created with its required writes and denied operations tested. The actual MCP service and agent/OS isolation remain pending. See [database checks](local-database-checks.md). Treat the new VM as unavailable until the project owner explicitly reports it ready.

## Identities and Privileges

Authentication establishes which identity is connecting. Authorization determines what that identity may do. Tailscale connectivity, SSH login, and MySQL authentication are separate boundaries.

| Identity | Intended permission | Explicit exclusions |
|---|---|---|
| Project migration identity | Create and alter objects in the project database; define approved views | No use by importer, MCP, or agents; no access to unrelated databases |
| Database grant administrator | Create project database identities and assign reviewed grants | Separate administrative session; credentials unavailable to application runtime; no automatic assumption that migration credentials can grant privileges |
| Import database identity | `SELECT`, `INSERT`, `UPDATE` on `teams`, `games`, `team_game_stats`, and `ingestion_runs` | No `DELETE`, DDL, grant administration, private fixture access, or unrelated database access |
| MCP database identity | `SELECT` on individually named approved views | No base-table grants, ingestion-run metadata, writes, private fixtures, arbitrary SQL tool, or schema administration |
| Research agent | Request bounded `list_games` and `get_game_data` tools through the orchestrator | No SQL/shell tool, database credentials, CFBD key, or migration/import credentials |
| Writer agent | Receive structured research evidence and source references | No retrieval tools or database credentials |

Administrator and migration duties may initially share an administrative identity if required by the environment; document that choice and keep it outside all runtime processes. No global runtime grants or `GRANT OPTION` are planned. Account host matching and authentication configuration must be reviewed for the local Docker connection and again for future VM deployment.

## Approved Read Surface

Implemented local views: `briefing_teams`, `briefing_games`, and `briefing_team_game_stats`, defined in [mcp-views.sql](../db/mcp-views.sql). Explicit column lists expose identities, results, selected core stats, and source references. They exclude raw file paths, error summaries, configuration, and credentials. Include CFBD source IDs plus response hashes and source retrieval timestamps where needed for citations; do not expose the entire `ingestion_runs` table.

Views require a deliberately chosen definer and security mode. If definer privileges are used to avoid giving MCP base-table access, use a restricted view owner with only the necessary underlying reads, not a broadly privileged administrator. Verify that view queries work under the MCP identity and that direct base-table reads fail.

SQL grants enforce database permissions. Tool code separately validates identifiers, bounds result sizes, and uses parameterized queries. Views do not themselves cap row counts. A permitted read can still be expensive; add query timeouts and tool limits.

## Credentials and Host Boundaries

See the [credential inventory and lifecycle plan](credentials.md) for file locations, generation, rotation/recovery planning, and remaining OS-isolation limits.

- CFBD key: retrieval process only; used in the HTTPS authorization header. Offline database loading does not need that key.
- Import database credentials: import process only.
- MCP database credentials: MCP service only, never model inputs.
- Model API key: orchestrator configuration only, never prompts or tool results.
- Administrative credentials: maintenance sessions only.

Keep private configuration outside Git and logs. On the VM, use distinct OS identities or suitably isolated containers where permitted so the agent runtime cannot read import/admin secrets. Merely using separate MySQL accounts does not isolate files owned by a shared OS user. Single-host compromise or privileged host access remains a shared risk.

Current local implementation: MySQL 8.4.13 in Docker publishes only `127.0.0.1:3307` to the Mac, using a separate persistent volume. The old host installation is untouched. The administrator password is a private ignored file mounted as a Compose secret; it is not an encrypted vault. MCP credentials are generated into an owner-only ignored file. Import credentials are stored separately in an owner-only ignored file; OS isolation remains pending.

Future VM plan: keep MySQL bound to VM loopback or a private container network without a public database port. Access the terminal application through SSH over Tailscale; MagicDNS resolves the host name and does not grant database privileges. Use local MCP transport initially. No remote configuration is authorized by this document alone.

## Enforcement Checklist

Run against harmless fixtures in the project database, with the actual intended identity. Record results and sanitized errors; do not record passwords or complete connection strings.

| Check | Expected outcome |
|---|---|
| Inspect grants for each runtime DB account | Only reviewed object-level privileges; no inherited broad role or global grants |
| MCP queries approved views | Succeeds |
| MCP reads a base table, `ingestion_runs`, or private dummy table | Denied |
| MCP inserts, updates, or deletes dataset rows | Denied; verify fixture unchanged |
| Import performs required insert/update and repeats a load | Succeeds; dataset identities/counts do not duplicate |
| Import attempts schema changes or private-table access | Denied |
| Invalid tool identifiers / oversized result requests | Rejected or bounded by tool code |
| Note contains an injected request for private data | Observe agent response separately; tool capabilities and database grants remain restricted |
| Runtime attempts to read import/admin secret files | Denied by OS/container isolation once configured |

Also test rollback on failed imports and missing-data responses. Agent refusal is a behavioral result; database denial is enforcement evidence. Neither substitutes for the other. All remote checks remain pending.

## Local MCP Account Details

`stillwater_mcp`@`%` has SELECT only on the three named views, with no inherited roles or grant option. `USAGE ON *.*` means no global data privileges, not permission to read all databases. `%` is a broad MySQL client-host match chosen for Docker NAT and later host-to-container access; it is not a network restriction. Docker’s loopback port binding limits the published host port, while processes/containers able to reach this database network can still attempt authentication. Reassess host matching for VM deployment.

The view owner is `stillwater_view_owner`@`localhost`, locked against login. It has SELECT on teams/games/stats and only five provenance columns of ingestion_runs. The views use SQL SECURITY DEFINER so MCP can query the views without base-table grants. No filesystem paths or error summaries are exposed. This does not limit query cost or tool inputs; those controls remain to be implemented.

Setup: `python scripts/setup_mcp_identity.py` is one-time and refuses existing accounts or password files; account/view DDL is not transactional. Do not blindly rerun it after partial failure. The password is never printed or passed in process arguments. The DB still stores an authentication verifier as normal. Neither the host password file nor local Compose secrets protect against programs running as the host user or Docker administrators.

Verification: `python scripts/check_mcp_permissions.py` connects via TCP inside the container as MCP using a temporary private client configuration. Host Python connector access is now verified for the import identity; MCP host connector integration remains pending. Approved view counts after import were verified as 15 teams, 14 games, and 28 statistics rows. Ten negative tests returned MySQL privilege error 1142, including private-table access and writes. At the initial grant-test checkpoint, dataset counts stayed zero and the harmless private fixture was unchanged. Football data was loaded afterward.

## Local Import Account

`stillwater_import`@`%` is implemented with SELECT, INSERT, UPDATE on exactly four tables: teams, games, team_game_stats, ingestion_runs. SHOW GRANTS confirms no broader grants or roles. The `%` client-host match has the same Docker-network limitation explained above; it is not a firewall rule. The separately generated credential is in `secrets/mysql-import-password`, ignored by Git with owner-only permissions.

`db/import-grants.sql` documents the grants. One-time `scripts/setup_import_identity.py` refuses existing accounts or password files. `scripts/check_import_permissions.py` verified authentication and SELECT/INSERT/UPDATE on all four tables using transaction fixtures, followed by rollback. Private-table reads, DELETE, CREATE TABLE, and ALTER TABLE were denied with error 1142. The four dataset/run tables stayed empty and the private dummy record was unchanged. These checks used container-local TCP, not the host Python connector. Real archive loading and repeated upserts have now passed using the host Python connector. A controlled application failure also confirmed real transaction rollback; see the database-check report.
