# Periodic Knowledge Checks

Use this as a standing learning plan for future project sessions. Start with one short recall question; use 3–5 questions at major checkpoints. Ask one at a time, wait for an answer, and explain corrections using the relevant code. Looking at code/docs is encouraged. Prefer project architecture, implementation and security over unrelated protocol details.

## Topics to Rotate Across the Whole Project

| Topic | Understanding to verify | Code / evidence |
|---|---|---|
| Data ingestion and normalization | Retrieval vs loading; paired strings, UTC dates, missing vs zero | fetch/normalize scripts; source-validation.md |
| Provenance and SHA-256 | Retrieval metadata vs import history; hash integrity vs authenticity; dirty code version limits | metadata files, ingestion_runs, import_data.py |
| Relational modeling | Internal vs CFBD IDs, primary/foreign/composite keys; what each constraint cannot enforce | schema-draft.sql |
| Transactions and upserts | All dataset writes commit together; failure history survives rollback; repeat imports vs repeated attempts | import_prepared, importer-review.md |
| SQL injection | Validation checks acceptable values; bound parameters separate values from SQL syntax | game_tools.py, import_data.py |
| Authentication and authorization | Who connects vs what they may do; successful and denied cases | permissions.md, permission check scripts |
| Views and definers | View definition chooses data; restricted definer supplies underlying reads; MCP still needs view grants | mcp-views.sql |
| Credentials and OS isolation | Cryptographic generation, file locations, rotation vs file replacement; same-user access limits | credentials.md |
| Docker/network boundaries | Persistent volumes, loopback vs all interfaces, host/container ports; grants are separate from network reachability | compose.yaml |
| MCP roles | Host, client, server and model; ordinary lookup functions work without MCP | mcp_server.py, check_mcp_tools.py |
| MCP transport | Stdio launches a subprocess using pipes; no MCP HTTP listener; MySQL separately uses TCP | StdioServerParameters |
| Tool boundaries | Discovery vs dispatch; schema validation, name allowlist, bounded results, query timeouts | game_tools.py, briefing.py |
| Model vs agent vs orchestrator | Same LLM can serve two roles; application owns dispatch and handoff | model_api.py, briefing.py |
| Evidence and generated text | Valid schema/citation ID does not establish factual support; acknowledge missing data | writer schema, model-review.md |
| Budgets and logging | Call/token/input limits, timeouts vs actual billing, sanitized events, provider retention | Budget, Audit, model-review.md |
| Security evidence | Planned vs implemented vs tested; fake-model success vs real behavior; behavioral refusal vs enforced denial | tests and checkpoint reports |

## Areas to Revisit After Today's Discussion

- Transaction boundaries: earlier team upserts also roll back if a later statistics write fails in the same transaction.
- Parameterization: legitimate apostrophes stay intact; values are safe from becoming SQL syntax because they are bound, not because validation declared them valid. JDBC PreparedStatement is the familiar analogy.
- Views: the SQL definition chooses exposed columns/query; the definer’s grants permit the underlying reads. Locking the definer prevents login, not view evaluation.
- MCP client exists already for integration tests; the production orchestrator now also contains a client. No live model has participated yet.
- Stdio/TCP/serialization: keep the conceptual distinctions recognizable without requiring wire-format memorization.
- Private file permissions distinguish OS users, not programs sharing the same user.

After Saturday, slow down and trace one game end-to-end, then have the learner make and verify a small change. Understanding remains a separate goal from reaching the demo milestone.
