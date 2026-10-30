# Model Integration Review

Selected starting configuration: OpenAI `gpt-6-luna`, reasoning effort `low`, via the Responses API. Official [model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna) lists low effort, function calling and structured output. API access for this account and real model behavior are not yet verified. No paid calls have been made by this implementation checkpoint.

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

All 26 offline tests pass, including unknown/invalid calls never dispatching, separate writer context without tools, unknown citations failing, missing evidence stopping before writing, incomplete/over-budget output stopping, timeout behavior, rejected audit fields, fake-secret markers excluded from payloads/logs, and the SDK child's effective environment.

`python scripts/check_briefing_offline.py` also passes fake-model orchestration through the real stdio MCP server and read-only MySQL. Its model is scripted; it does not establish model quality or injection resistance. No real generated briefing, paid usage, model account access, or live injection test is verified yet.

## Next Steps

1. Arrange an OpenAI API project/key privately. Do not put the key in chat. Account billing, model access and spending controls must be checked in that project; no particular account entitlement is assumed.
2. Run `python scripts/store_model_key.py` in an interactive local terminal. Input is hidden; it refuses to overwrite an existing file.
3. Review `RESEARCH`, `WRITER`, `ARGUMENTS`, `Budget`, and `public_evidence` in `briefing.py`.
4. `python scripts/briefing.py` is inert by default. `python scripts/briefing.py --live` explicitly enables the bounded paid run. Logs go under ignored `logs/`. The current terminal output is JSON for inspection, not the final polished UI.
5. Verify model-selected game, factual claims and citations against retrieved evidence. Then test missing data, injected source instructions, and failure cases before declaring the demo ready.

Full OS-level credential isolation and VM deployment remain deferred. Model low effort is not a security boundary.
