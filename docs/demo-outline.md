# Demo Presenter Outline

For suggested full phrasing compiled during rehearsal, see the [study script](demo-study-script.md). Keep this outline as the shorter presentation aid.

Target: a brief product demonstration followed by roughly 3–4 minutes of explanation. These are cues, not a speech. Follow Texas–Alabama throughout. Live generation time varies; do not promise a fixed response time.

## Before presenting

- Have Docker MySQL running and the page open at `http://127.0.0.1:8000`.
- Use `python scripts/web_app.py --live` if live generation is intended; confirm the page says live generation is enabled.
- Close secret-file tabs and avoid showing credentials, raw archives, or unsanitized terminal output during screen sharing.
- Keep the saved sample available as a clearly labeled fallback. Have the [architecture diagrams](glass-to-metal-review.md) ready in Markdown preview.

## 1. Show the result — about 30 seconds, plus generation time

- **Purpose:** historical Texas football briefings grounded in imported records; learning controlled agent orchestration and security boundaries.
- Enter `Texas vs Alabama` and Generate once. While waiting, introduce the two roles: research retrieves evidence, writer summarizes it.
- Point out the result, two statistical comparisons (for example offense and conversions), evidence reference, limitations, and expandable evidence panel. The writer now aims for broader coverage when supported; sparse data can still produce a shorter briefing.
- Scope: Texas 2023, historical postgame summaries. No predictions or live sports feed.
- If using the saved sample, state that it is a prior result and does not demonstrate a new model call.

## 2. Glass: browser and Python server — about 30 seconds

- **Browser:** school names, nicknames, or season order resolve locally to an imported game ID. Ambiguous names ask for clarification.
- **Server:** independently validates that ID and the request before starting work. Browser checks can be bypassed.
- **Guardrails:** localhost-only, origin/request-token checks, limited request shape, explicit paid-generation mode. No API or database credentials in the browser.
- Token is cross-site request protection, not a user login. This is a local demo.

## 3. Research and orchestration — about 45 seconds

- **Orchestrator:** ordinary Python code controls the sequence and calls the model API.
- **Research agent:** the model returns proposed tool calls; it does not execute Python or SQL itself.
- **Application:** validates each proposed tool name, arguments, and budget before dispatch.
- **Guardrails:** two approved tools, bounded calls/results/time/usage, no automatic retries, sanitized metadata logs.
- Two roles do not mean two API requests. Our observed path used four: list proposal, detail proposal, research completion, writer response.

## 4. MCP to metal: retrieval and MySQL — about 40 seconds

- **MCP:** standard client/server interface for discovering and calling tools. Here, the client runs inside the application and talks to a local subprocess over stdio.
- **Tools:** only `list_games` and `get_game_data`; validate inputs and run fixed, parameterized queries.
- **MySQL:** separate read-only MCP identity can SELECT only from approved views. Separate importer and administrator identities do other work.
- **Guardrail to emphasize:** database grants are enforced independently of the model and application. No arbitrary SQL, file, or shell tools.

## 5. Where the records came from — about 25 seconds

- Preparation happened before the briefing: CFBD response files → validation/normalization → MySQL.
- Preserve original files, source metadata, hashes, and import history for traceability.
- Unique source identities plus upserts prevent duplicates on repeated imports; transactions roll back partial dataset writes.
- Source comparisons covered the schedule and selected box-score fields. Hashes check file integrity, not football accuracy.

## 6. Return path: evidence to writer to browser — about 30 seconds

- MCP returns structured data to the **application**; the application filters and collects it.
- The application starts a **separate writer context** with evidence and no tools. Same model, different role and access.
- Validate output structure, evidence references, and selected-game match; browser displays text safely.
- Important limit: a valid citation does not prove the statement is true. We manually compared sampled claims against retrieved evidence.

## 7. Verification, limits, and next steps — about 30 seconds

- **Evidence:** 41 Python tests, 102 search cases, real MCP/database integration, separately tested denied database operations, and scoped live missing-data/injection cases.
- Injection checks observe model behavior; database checks establish tested authorization. Neither guarantees every future attack fails.
- **Current limits:** same-OS-user secret-file access, no user authentication, sampled factual evaluation, local demonstration server. Token budgets are not a hard dollar cap.
- **Next:** VM deployment with its security review and isolation/access decisions, then exploration of live web-assisted alias checks. Further features remain deferred; broader evaluations and factual checks remain hardening work. No runtime web tools are currently enabled.
- Collaboration: Codex assisted planning, implementation, and review; Ry directed scope and reviewed behavior and concepts.

## If something fails

| Situation | Keep the explanation moving |
| --- | --- |
| Generation error or timeout | Do not repeatedly click. Explain fail-closed behavior and possible billing after timeout; switch to the labeled saved sample. |
| Database unavailable | Use the saved sample and diagrams; state that live retrieval is unavailable. |
| Ambiguous nickname | Show the clarification, then use the full school name. This is intentional behavior. |
| Unexpected factual claim | Compare with evidence, identify the mismatch honestly, and explain the present limit of citation validation. |

## Optional deeper questions

- Execution and handoff: `briefing.py` → `run_workflow`.
- Tool registration versus retrieval: `mcp_server.py` and `game_tools.py`.
- Independent DB enforcement: `db/mcp-views.sql` and [permissions](permissions.md).
- Test fixtures and stopped/fixed runs: [security/failure checks](security-failure-checks.md).

Return to this route if you lose your place:

**Browser → server checks → research/tool loop → MySQL → application evidence handoff → writer → output checks → browser.**

Preparation status: intensive and abbreviated live-path reviews plus a guided verbal rehearsal have been completed. Suggested wording is compiled in the study script; a continuous timed/browser rehearsal remains separate. Latest richer-output live check used four model requests and 8,684 reported tokens; it does not replace the earlier separate security evaluations.
