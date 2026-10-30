# MCP Retrieval Checkpoint

Implemented two tools with the official MCP Python SDK 2.3.0. The server runs over local stdio: its parent process exchanges protocol messages over stdin/stdout, without an HTTP listener. No model API is called in this step.

## Code and Guardrails

| File / function | Implemented boundary |
|---|---|
| `scripts/local_db.py`: `connect_mcp` | Reads only the MCP credential, verifies account identity and MySQL version; no import/root key read on this path |
| `scripts/mcp_server.py` | Registers exactly `list_games` and `get_game_data`; strict integer types and range bounds appear in the tool schemas |
| `scripts/game_tools.py`: `_bounded_int` | Rechecks input types/ranges even for direct Python callers; booleans and numeric strings are rejected |
| `list_games` | Texas-only, one season (1869–2100), result limit 1–25; one extra bounded row detects truncation |
| `get_game_data` | One CFBD source game ID; returns at most one Texas game and two team-stat rows; no user-supplied table/column/query text |
| `_query` and SQL constants | MCP connection, read-only transaction, parameter tuples, approved views only, two-second SELECT execution hints, sanitized database-failure response |
| MySQL grants | Independently deny base/private reads, writes, and DDL; previously tested outside MCP |

`get_game_data` returns a stable `cfbd:game:<source-id>` reference, source endpoints, response hashes, retrieval timestamps, result, and selected team statistics. SQL NULL remains JSON null. Missing games return `not_found`; empty seasons return an empty list; database failures return `retrieval_unavailable`. These statuses must be handled separately by the future orchestrator/writer.

The two-second limit is per SELECT, not a strict overall tool deadline. Connections have a ten-second connect timeout and thirty-second read/write timeouts; the integration client uses twenty seconds per request and a ninety-second whole-check timeout. Future orchestration needs its own call-count and total-time budgets.

## Verification

The MCP checkpoint passed 18 offline tests; the full suite now passes 26 after adding model-boundary tests. Real host-to-container retrieval used only the MCP database identity. `python scripts/check_mcp_tools.py` launched an actual subprocess and used MCP discovery/calls over stdio to verify:

- Exactly the two approved tools are exposed.
- Fourteen Texas 2023 games are returned.
- Texas–Alabama returns the 34–24 result, both stat records, and evidence references.
- Missing game and season responses are explicit; a two-row request is truncated correctly.
- Excessive limits, wrong argument types, SQL-like game IDs, and an unregistered arbitrary-SQL tool are rejected.

No API credentials, administrator/import passwords, or raw database exception messages were sent as tool results. The server's database credential exists in its process and remains protected only by the current host-user boundary. A separate OS user/container boundary for the eventual agents is not implemented.

The connection helper shares code with the importer but selects the MCP credential only when `connect_mcp()` is called. Python module/function boundaries are not an OS security boundary. Model-facing tools cannot request another account.

## Dependencies and Reproduction

Direct dependencies are pinned in `requirements.txt`; `requirements-lock.txt` records the installed dependency versions for this checkpoint. On this Intel Mac, use `python -m pip install --only-binary=:all: -r requirements-lock.txt`. The unconstrained source build of cryptography 50.0.2 failed because OpenSSL development dependencies were unavailable; binary-only resolution installed compatible cryptography 48.0.1. This records compatibility, not a completed vulnerability audit.

## Remaining

Orchestrator tool allowlisting, Luna–Low selection, separate research/writer contexts, sanitized audit events and usage budgets are implemented with fake-model tests. Live model behavior, injected-note evaluation and rehearsal remain pending; see [model review](model-review.md). Database-error sanitization and MCP request validation do not substitute for those checks. No accounts, tables, or grants were modified for this milestone.
