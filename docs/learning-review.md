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
- MCP client exists already for integration tests; the production orchestrator now also contains a client. Live research/writer calls now participate; their access still comes from the application, not the model itself.
- Stdio/TCP/serialization: keep the conceptual distinctions recognizable without requiring wire-format memorization.
- Private file permissions distinguish OS users, not programs sharing the same user.

After the Monday demo, slow down and trace one game end-to-end, then have the learner make and verify a small change. Understanding remains a separate goal from reaching the demo milestone.

## November 1 Review Notes

- Ry correctly identified fixed tool queries and independent view grants as deletion barriers, and explained why missing yards must not become zero.
- Revisit environment minimization versus OS isolation: withholding environment secrets does not block same-user file access.
- A claim is one factual statement with an evidence reference. Our two-claim minimum was a presentation rule, not a security boundary; accepting one supported claim handles sparse data without padding. Empty output and unknown references still fail.
- Ask Ry to distinguish deterministic code checks, live behavior observed in one fixture, and separately tested database enforcement. A passing injection attempt is not proof against all attacks.
- The small Python-served web UI is now implemented on its separate branch; next is abbreviated review and rehearsal near Monday afternoon. Continue one-question-at-a-time reviews.

## UI and Identity Review Topics

- Alias versus identity: BYU and Brigham Young can select the same imported team without changing CFBD names or IDs. A name is not a unique database identifier.
- Context and ambiguity: OSU has one matching opponent in this schedule; UW has two. Ask Ry how the application should behave when coverage expands or a team is played twice.
- Reviewed source configuration versus runtime web access: researching a static map does not give the agent internet tools or write permission.
- Browser checks versus server enforcement: users can bypass JavaScript; Python must still validate IDs, origin/token, request shape and usage limits.
- Client rendering: use textContent for untrusted model/source strings; never treat them as executable HTML.
- Review the UI feedback history in [web-ui.md](web-ui.md). Ry’s visual approval and HTTP integration tests are separate evidence from automated browser testing, which was unavailable.

Nickname review: distinguish a school identity from its nickname and mascot character. Ask why Cowboys/Pokes and Cougars need clarification in the same schedule, why Cougs and Coogs are not automatically interchangeable, and why a reviewed alias source does not prove global uniqueness. Tests include future Washington State/Cougs ambiguity. Browser search is still a convenience layer; Python and database controls remain independent.

## Glass-to-Metal Review Follow-up

- Revisit the exact execution trigger: the external research model returns a structured function-call proposal; the orchestrator validates it and initiates `await tools.call_tool(...)`. Await waits for that initiated request's response; the model does not directly execute Python or call the writer.
- Two agent stages do not mean two API requests. The observed four-request path is list proposal → get-data proposal → research completion → writer output, with local MCP calls and results between model requests.
- Revisit grants versus views, local request token versus authentication, citation linkage versus factual support, and hashing versus correctness. Ry correctly explained rollback, missing versus zero, least privilege, timeout billing risk and excluding secrets from logs; precision at these boundaries remains a review focus.
- Import idempotency uses unique constraints and upserts, not a pre-insert existence check. Dataset identities remain stable while import history/provenance can change.
- Use [glass-to-metal-review.md](glass-to-metal-review.md) to follow one Alabama game and keep ingestion separate from the live request path. Diagrams, code links and the [presenter outline](demo-outline.md) are prepared; full rehearsal remains.

## Latest Review Progress

Completed a step-by-step live-generation walkthrough. Ry correctly explained server-side dataset membership checks, independent tool validation, restricted MCP identity, parameterized-query protection, tool results becoming model input, evidence-only writer context, and citation linkage versus correctness. Revisit the model → orchestrator → MCP trigger and multi-turn API calls in the next abbreviated pass. Runtime token lifecycle and authentication/authorization distinctions were explained with code.

The writer now requests broader use of available statistics; this changes output guidance rather than tool/database access. Ry reported the result was better. Preserve sparse-data behavior and distinguish the latest richer-output sample from earlier live security fixtures when discussing test evidence.
