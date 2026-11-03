# Demo Study Script

Compiled from the suggested wording during Ry's rehearsal. Study the sequence and ideas; use the shorter [presenter outline](demo-outline.md) during the demonstration. These paragraphs are suggested phrasing, not a memorization requirement.

## 1. Opening and purpose

“This app generates sourced briefings of Texas Longhorns football games, currently covering the 2023 season. I built it to learn how to orchestrate AI agents with controlled tool access and independent security boundaries, while collaborating with Codex on implementation and review.”

Show Texas–Alabama, then point out the briefing, one or two statistical comparisons, limitations, and evidence panel. If showing the saved sample, identify it as a prior result rather than a fresh generation.

## 2. Browser to application

“The browser resolves the request to a game ID using the game list and reviewed aliases already loaded into the page. Python independently validates that ID and the request, then builds a briefing request for the research agent. The model proposes tool calls, which the application validates before dispatching through MCP.”

“The model API key and database credentials stay server-side. The web interface is restricted to localhost, with origin and request-token checks, bounded requests, and generation limits. That token helps prevent unwanted cross-site browser requests; it is not user authentication.”

## 3. Research, MCP, and database enforcement

“The MCP server invokes the approved retrieval function, such as `get_game_data`, which runs fixed, parameterized queries through approved MySQL views using a SELECT-only database account. The server validates tool inputs, and MySQL independently enforces the account's permissions. There are no arbitrary SQL, file, or shell tools exposed to the model.”

“The model proposes an action; the application controls execution. Our MCP client runs inside the application and communicates with the local MCP subprocess over stdio. Two agent roles do not mean two API calls: the observed workflow used three research responses and one writer response, with local tool calls between research turns.”

## 4. Application handoff to the writer

“The results return to the application, which filters and collects the structured evidence. It then passes that evidence to a separate writer context with no tools. Research and writing use the same model in different roles; MCP does not call the writer directly.”

“The writer uses the supplied result and statistics to generate cited claims and explain material missing data. We preserve missing values as unknown rather than treating them as zero.”

## 5. Output validation and return to the browser

“The application validates the writer's output structure and checks that each claim references evidence retrieved for this briefing. The web wrapper also checks that the returned evidence matches the selected game. These checks do not prove factual correctness; we manually compared generated claims with the underlying records in our sample evaluations.”

“The browser displays the briefing, limitations, evidence, and usage totals. Source and generated text are rendered as text rather than executable HTML.”

## 6. How the data got there

“Data preparation happened before generation. We retrieved CFBD responses and compared the schedule and selected statistics with official records. We preserved the original responses and metadata, designed the MySQL schema, then normalized and imported the selected fields.”

“Unique source identifiers and upserts prevent duplicate records on repeat imports, while ingestion-run history links the data to source files, hashes, and importer version. Dataset writes run in a transaction so a failure rolls back partial changes while failed-attempt history is retained. Hashes check saved-file integrity, not the correctness of every football statistic or transformation.”

## 7. Verification, limitations, and next steps

“We tested allowed and denied database operations separately from model behavior. The current suite includes 41 Python tests and 102 search cases, plus real MCP/database integration and scoped live missing-data and prompt-injection checks. Those results cover the tested cases, not every possible attack. The latest richer writer prompt was checked with a live factual comparison and the existing tests; the earlier live injection cases preceded that prompt revision.”

“MySQL runs in Docker, but our application and MCP processes are not isolated from one another by separate OS identities. Other processes running as the same user, or with sufficient privileges, could still read the secret files. This is a local demonstration, with no user login and sampled rather than automatic claim-level factual verification.”

“After the demo, I want to deploy to the VMs and address the security requirements of that environment, including credential isolation and access control. After that, I want to explore live web-assisted checks for aliases. Those checks are future work; the current alias map is reviewed static configuration. Further features remain deferred.”

VM availability, final topology, and installation permissions beyond the existing authorization must still be confirmed. This roadmap is not permission to begin remote deployment or add runtime web tools now.

## Keep these distinctions precise

| Say | Avoid implying |
| --- | --- |
| The model proposes, the application dispatches, MCP invokes the tool | The model directly executes SQL or MCP directly invokes the writer |
| The MCP account has SELECT-only grants on approved views | Every view is inherently read-only |
| A citation points to retrieved evidence | A valid citation proves the sentence is correct |
| Hashes verify saved bytes against a recorded hash | Hashes establish source truth or correct normalization |
| Same-user programs may access secrets | Every ordinary OS user can read owner-only secret files |
| Two model roles with multiple possible API turns | Exactly two API requests per briefing |

If you lose your place: **Browser → server checks → research/tool loop → MySQL → application evidence handoff → writer → output checks → browser.**

## Quick Glass-to-Metal Flow

**Browser — `app.js` + `game_search.js`:** Resolve the request to a game ID and submit it.\
↓\
**Web server — `web_app.py`:** Validate the request, game ID, token, and usage limits.\
↓\
**Orchestrator — `briefing.py`:** Ask the research model what evidence to retrieve.\
↓\
**Research model:** Propose an approved tool call.\
↓\
**Orchestrator — `briefing.py`:** Validate the proposal and dispatch it through the MCP client.\
↓\
**MCP server — `mcp_server.py`:** Validate inputs and invoke the registered retrieval function.\
↓\
**Retrieval — `game_tools.py`:** Execute fixed, parameterized queries.\
↓\
**MySQL:** Enforce SELECT-only view grants and return records.\
↓\
**MCP server → orchestrator:** Return structured results for filtering and further research turns.\
↓\
**Orchestrator — `briefing.py`:** Hand collected evidence to a separate writer context without tools.\
↓\
**Writer model:** Produce cited claims and limitations from the evidence.\
↓\
**Application — `briefing.py` + `web_app.py`:** Validate output structure, references, and selected-game match.\
↓\
**Browser — `app.js`:** Display the briefing, evidence, limitations, and usage.
