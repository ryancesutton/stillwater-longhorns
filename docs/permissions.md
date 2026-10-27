# Permission Plan

Status: proposed, not deployed or enforcement-tested. Treat the new VM as unavailable until the project owner explicitly reports it ready. Local planning and implementation can continue without remote access.

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

Administrator and migration duties may initially share an administrative identity if required by the environment; document that choice and keep it outside all runtime processes. No global runtime grants or `GRANT OPTION` are planned. Final account host matching and authentication configuration must be reviewed on the actual VM.

## Approved Read Surface

Proposed views: `briefing_teams`, `briefing_games`, and `briefing_team_game_stats`. These are not implemented yet. Explicit column lists expose identities, results, selected core stats, and source references. They exclude raw file paths, error summaries, configuration, and credentials. Include CFBD source IDs plus response hashes and source retrieval timestamps where needed for citations; do not expose the entire `ingestion_runs` table.

Views require a deliberately chosen definer and security mode. If definer privileges are used to avoid giving MCP base-table access, use a restricted view owner with only the necessary underlying reads, not a broadly privileged administrator. Verify that view queries work under the MCP identity and that direct base-table reads fail.

SQL grants enforce database permissions. Tool code separately validates identifiers, bounds result sizes, and uses parameterized queries. Views do not themselves cap row counts. A permitted read can still be expensive; add query timeouts and tool limits.

## Credentials and Host Boundaries

- CFBD key: retrieval process only; used in the HTTPS authorization header. Offline database loading does not need that key.
- Import database credentials: import process only.
- MCP database credentials: MCP service only, never model inputs.
- Model API key: orchestrator configuration only, never prompts or tool results.
- Administrative credentials: maintenance sessions only.

Keep private configuration outside Git and logs. On the VM, use distinct OS identities or suitably isolated containers where permitted so the agent runtime cannot read import/admin secrets. Merely using separate MySQL accounts does not isolate files owned by a shared OS user. Single-host compromise or privileged host access remains a shared risk.

Keep MySQL bound to VM loopback or a private container network without a published database port. Access the terminal application through SSH over Tailscale; MagicDNS resolves the host name and does not grant database privileges. Use local MCP transport initially. No remote configuration is authorized by this document alone.

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
