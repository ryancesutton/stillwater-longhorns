# Local Web UI

The demo uses Python's standard-library HTTP server plus plain HTML, CSS, and JavaScript. No React, Node, external assets, or additional dependencies are required. Work is isolated on `feature/local-web-ui`; the terminal workflow is retained.

## Run

From the repository root with the virtual environment active:

```sh
python scripts/web_app.py
```

Open **http://127.0.0.1:8000** (use that exact host). Preview mode lists imported games and displays a clearly labeled saved Alabama sample without any model request. Docker MySQL must be running for the game list, but the saved sample works independently. Its evidence panel is an abbreviated historical snapshot, not a fresh database retrieval.

To enable the paid Generate button, stop the preview process with Ctrl+C and run:

```sh
python scripts/web_app.py --live
```

No model request is sent on page load. Choose a game and click Generate. The Python server creates a bounded request for that imported game, calls the existing research → writer workflow through stdio MCP, checks that returned evidence matches the selected game, and returns the briefing plus evidence. A mismatch is rejected before display. Live retrieval still uses existing approved MCP views and the MCP identity. The game dropdown uses the same bounded `list_games` Python function directly; it does not require a model call or a separate MCP process.

## New boundaries

| Control | Code / purpose |
| --- | --- |
| Local binding | `DemoServer` starts only on `127.0.0.1`; no LAN/tailnet exposure |
| Host and browser-origin checks | Reject unexpected Host headers and foreign/missing POST origins |
| Per-start request token | Same-origin browser obtains a random token; POST requires it; it is not a model/database credential |
| Explicit live opt-in | Default server rejects generation; `--live` enables paid button requests |
| Fixed routes | Only explicitly named static files and API routes; no arbitrary filesystem serving |
| Restricted request shape | JSON, up to 1,024 bytes, exactly one integer source game ID present in imported Texas 2023 games; no free-form prompt/SQL |
| Work and usage limits | One generation at a time, ten-second cooldown, ten attempts per server start, plus existing workflow budgets; not a hard dollar cap |
| Safe rendering | Source/model text is assigned via `textContent`, not interpreted as HTML; restrictive CSP and no third-party scripts/assets |
| Sanitized failures | Generic HTTP errors; no request logging or raw exception bodies; existing metadata-only workflow audits |

The request token is CSRF protection, not user authentication. Other programs running as the same OS user remain trusted by this local-demo setup. No registration, production web server, TLS, or OS-level credential isolation has been added. Do not publish or proxy this service as a public application. Public/VM serving requires a separate deployment and authorization review.

## Verification

The full suite passes 41 tests. Six HTTP tests use real local sockets with fake database/model functions to verify host/origin/token rejection, fixed-file access, sample/disabled-live behavior, input validation and size/type rejection, concurrent and usage limits, and sanitized failures. These do not establish browser rendering or actual model quality.

Live HTTP integration passed: the page was served, 14 games were read from local MySQL, and one selected Alabama game generated a sourced briefing through HTTP → existing orchestrator → real MCP → MySQL → writer. The run used four model requests and 8,246 reported tokens. Codex compared the displayed claim text with the returned result, yardage, and turnover values; they matched. The temporary live verification server was closed afterward.

Automated browser inspection was unavailable because no browser was connected. Ry manually reviewed the page and approved its initial appearance. Responsive layout, keyboard behavior, updated alias interaction, and a user-confirmed live browser generation still need explicit review; HTTP integration is not browser automation. The preview can be reviewed without incurring API usage.

Rehearsal remains scheduled after UI review, closer to Monday afternoon's presentation. VM deployment is unchanged and deferred.

## Search-style game requests

The browser supports bounded phrasing such as `Texas vs Alabama`, `Texas’s third game of 2023`, or `Can you give me a briefing on Texas' 3rd game of the 23 season?`. `web/game_search.js` resolves these against the loaded 2023 games, sorted by kickoff time. Game number means season order, not schedule week. Missing year defaults to the imported 2023 season. Opponent names, numeric ordinals, and first through fourteenth are supported; this is a rule-based selector, not general natural-language understanding.

Only the matched source game ID goes to the existing generation endpoint; the typed request is not sent to the model or used as SQL. Unsupported seasons, no match, multiple matching games, and conflicting game numbers/opponents produce clarification messages before paid calls. The original dropdown remains available and changing it clears the search text. Typing or choosing a game does not scroll or start generation; Generate (or Enter in the search field) initiates the bounded workflow. Generate and saved-sample actions scroll to the results. Scrolling respects reduced-motion settings.

The optional developer check `node tests/test_game_search.js` passed six matching and nine rejection/clarification cases plus a no-mutation assertion. It uses the existing Node executable for testing only; running the app requires no Node install or packages. Python HTTP/database security checks remain separate. The visible page is branded Longhorns; Stillwater remains the internal project name.

## Changes during UI review

| Feedback / check | Change or observation |
| --- | --- |
| Initial burnt-orange styling approved by Ry | Retained the simple local layout and styling |
| Stillwater is an internal project name | Removed it from the page title, header, and footer; visible branding is Longhorns |
| Asked for results to come into view | Added smooth scrolling with reduced-motion support |
| Dropdown scrolled unexpectedly while choosing a game | Removed selection-triggered scrolling; Generate/results and saved-sample actions still scroll |
| Refresh restored the prior scroll position | Disabled browser scroll restoration and reset to the top on page show; results actions still scroll |
| Wanted natural ways to identify a game | Added a search-style field, retained dropdown fallback, and matched opponent names or season ordinals against loaded records |
| Wanted BYU/full-name and OSU-style inputs | Added a reviewed local alias catalog with primary-source references and ambiguity checks; no runtime web access |
| Requested preparation for browser live generation | Server was switched to explicit live mode; startup/config/game-list checks made no paid calls. A user-confirmed browser generation has not been reported |

Aliases are loaded from `/api/team-aliases`; only the selected source game ID is sent to the generation endpoint. See [alias research and maintenance](team-aliases.md). All 14 imported opponents have reviewed name variants; the catalog also records Ohio/Oregon State as OSU ambiguity candidates without importing their data. The search checks periods, case, spacing, full-name context, overlapping names, and collisions. Bare UW is ambiguous in the current dataset and asks for a full name or game number. No model calls are needed for alias resolution.

## Future UI work and security maintenance

Before rehearsal, review search/alias matching and errors in the browser, including UW ambiguity, unavailable data, small screens, keyboard focus, and the selected game shown during generation. Keep the terminal and saved-sample fallbacks available. Rehearse nearer Monday afternoon.

Later options include explicit candidate-choice buttons, a match-confirmation step before paid generation, supported-alias examples, and broader season coverage. Typo tolerance and web-assisted discovery remain deferred. Predictions, registration, and public deployment require separate backend/data/security work; they are not enabled by the UI.

For every UI change, preserve server-side ID validation and generation budgets: client checks are usability features, not an authorization boundary. Keep keys/database access out of browser code, retain fixed routes, origin/token checks, safe text rendering, CSP, sanitized errors, and metadata-only audit logs. Recheck denial cases when routes, payloads, or rendering change. Review aliases as configuration, including collisions and out-of-dataset candidates; never let source text grant tools or write access. Keep raw user search text out of prompts/logs under the current design. New browser functionality must not silently enable live calls, automatic retries, broader model tools, or external scripts. The standard-library server and same-user secret access remain local-demo limitations.

## Team-nickname demo extension

Version 2 of the alias catalog includes reviewed team nicknames for all 14 imported opponents, including Cowpokes, Pokes, Cougs, Coogs, Horned Frogs and Red Raiders. Try `Texas vs Cougs`, `Texas vs Cowpokes`, or `Texas vs Wyoming Pokes`. Bare Cowboys/Pokes/Cougars are ambiguous within this season and show a clarification message before any generation. `Texas vs BYU Cougars` uses the explicit school name to disambiguate. See the [full nickname list and sources](team-aliases.md).

Nickname handling uses the same local resolver and server-validated game-ID endpoint. No change to paid-call opt-in, database grants, MCP tools, logging, or rendering permissions was needed. Search checks now pass 102 query cases plus the input-order assertion; Python suite remains 41 tests. Future review should include nickname ambiguity in the browser; broader nickname coverage and explicit candidate-selection buttons remain future work. A browser refresh loads the updated static catalog; it does not call the model.

## Demo feature checkpoint

Ry considers this feature set sufficient for the demo. Pause feature additions. Next session: intensive architecture/code/security review, a step-by-step demo script with fallback paths, and a few readable Mermaid diagrams for the mentor. The demonstration remains local; rehearsal should be close to the Monday afternoon presentation. No final rehearsal or user-confirmed live browser-generation result is implied by visual approval.
