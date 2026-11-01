# Model Integration Review

Selected starting configuration: OpenAI `gpt-6-luna`, reasoning effort `low`, via the Responses API. Official [model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna) lists low effort, function calling and structured output. API access is verified. A live sample and scoped missing-statistics/injected-text evaluations have passed; see the recorded results below.

## Security Summary

- `scripts/model_api.py` reads only `secrets/openai-api-key`. It uses a fixed HTTPS endpoint, refuses redirects, puts the key only in the authorization header, suppresses response-body errors, caps response size, and does not retry automatically.
- `scripts/briefing.py` launches local MCP with an environment allowlist. A test launches a real child through the SDK and confirms fake model/unrelated secret environment variables are absent. This does not prevent same-user file access.
- Research receives exactly two function-tool definitions. The orchestrator independently checks tool names and strict schemas, rejecting extra fields before MCP dispatch. Parallel calls are disabled and rejected.
- Tool payloads are projected to explicit public fields. Private configuration and file-path extras are excluded. This is an allowlist, not a universal secret detector for arbitrary user text or source-field contents.
- Writer uses a separate model call/context with structured retrieved evidence only, no research prose, original user prompt, or tools. It returns schema-validated claims with references restricted to retrieved evidence. Citation existence is enforced; semantic support and factual accuracy still require evaluation.
- Audit logs contain only approved stage/tool IDs, numeric arguments, timing, aggregate usage and outcomes. Prompt/response bodies, headers, keys and raw exceptions are not logged. Logs are local, ignored, owner-only files, not tamper-proof audit records.

Limits: at most four research model calls, four tool calls, two evidence games, one writer call, 2,500 output tokens per response, 70,000 serialized payload characters, and 30,000 characters per tool response. Reported aggregate usage is checked against 24,000 tokens after each response; it is not a prepaid hard dollar cap. The last in-flight request can cross the usage threshold. A 180-second workflow deadline and request timeouts limit waiting, but a timed-out already-sent request may still complete and be billed. Research and writer both use the same model with different instructions/access.

## Data Leaving the Mac

Live calls send the bounded user request, instructions, tool schemas, selected game evidence and tool-conversation items to OpenAI. No raw archive files, local paths, database passwords or CFBD key are intentionally included. `store=false` disables ordinary Responses application-state storage, not every form of provider retention. OpenAI documents that API data is not used for training by default and that abuse-monitoring logs may retain content for up to 30 days, subject to stated exceptions and account controls. Review [current data controls](https://developers.openai.com/api/docs/guides/your-data) before live use. We have not configured Zero Data Retention.

## Verification So Far

All 35 offline tests pass, including unknown/invalid calls never dispatching, separate writer context without tools, unknown citations failing, missing evidence stopping before writing, incomplete/over-budget output stopping, timeout behavior, rejected audit fields, fake-secret markers excluded from payloads/logs, and the SDK child's effective environment.

`python scripts/check_briefing_offline.py` also passes fake-model orchestration through the real stdio MCP server and read-only MySQL. Its model is scripted; it does not establish model quality or injection resistance. Live model evaluation is recorded separately below; scripted tests do not establish model behavior.

## Next Steps

1. Review the [security/failure results](security-failure-checks.md) and [sample briefing](sample-briefing.md).
2. Keep the API key in the ignored owner-only file; setup is complete. `store_model_key.py` remains available for fresh setups and refuses overwrite.
3. Build the basic React UI on a separate branch; keep API calls server-side and retain the terminal fallback.
4. `python scripts/briefing.py` remains inert by default; `--live` explicitly enables paid calls. `scripts/check_briefing_live.py --live` runs the scoped evaluation fixtures, with optional `--case` selection. Production audit logs remain metadata only.
5. Rehearse closer to the Monday afternoon presentation; broader accuracy/injection evaluation remains future hardening.

Full OS-level credential isolation and VM deployment remain deferred. Model low effort is not a security boundary.

## First Live Run

After the project owner stored a restricted Responses key and confirmed available credit and Luna access, the default Texas–Alabama request completed successfully. Four model requests reported 8,285 aggregate tokens. Research retrieved one game through the real MCP tools, then the writer produced four evidence-referenced claims. Scores, yardage, turnovers/interceptions, third-down values, venue and season matched returned evidence in a manual Codex review. See [sample briefing](sample-briefing.md).

The local audit contained only approved metadata fields and a completed outcome; no prompt/response bodies or key values were logged. This verifies one live path, not all model behavior, injection resistance, or a dollar spending cap. The key remains outside Git. Earlier statements of no paid calls describe the pre-live checkpoint.

## November 1 Security Evaluation

Live missing-statistics and injected venue-text checks passed in scoped runs. A diagnostic run found that requiring two claims rejected a valid one-claim result briefing. Writer instructions and validation now permit 1–6 claims; a regression test also verifies zero claims remain rejected. The complete suite passes 35 tests. See [security/failure checks](security-failure-checks.md) for fixtures, stopped runs, manual review, usage and limitations. No database records or raw imports were changed.
