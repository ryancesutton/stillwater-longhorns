# Checkpoint: Local Data and Database Boundaries

## Working Today

The local workflow can retrieve CFBD data, preserve original responses and metadata, normalize Texas 2023 records, and load MySQL using a restricted import identity. The database contains 15 teams, 14 games, and 28 team-game statistics rows. MySQL 8.4.13 runs in Docker with persistent storage and its host port bound only to `127.0.0.1:3307`.

Repeated imports retained dataset counts and internal IDs. A controlled application exception during a real import rolled back prior dataset changes and recorded failed import attempts. Recorded provenance currently identifies dirty working-tree code; the commit alone does not reproduce those exact runs.

MCP database access is restricted to three views. Its own authenticated queries succeeded, including populated view counts, while private/base-table reads, writes, and schema changes were denied. A separate locked identity supplies the views’ underlying read privileges. The import account's required reads/writes succeeded, while private reads, deletes, and DDL were denied. These are real database enforcement results, not agent behavior tests.

## Major Concepts

| Concept | Application here |
|---|---|
| Authentication vs authorization | Prove account identity separately from checking its permitted operations |
| Least privilege | Separate administrator, importer, MCP reader, and locked view definer |
| Views | Saved queries expose approved columns and provenance without base-table access |
| Parameterized SQL | Source values are passed separately from developer-owned SQL structure |
| Transactions | Dataset changes and success status commit together, or dataset changes roll back |
| Idempotent dataset import | Unique source IDs and upserts prevent duplicate identities; attempts still get new history rows |
| Provenance | Source request, retrieval time, original bytes/hash, and importer version trace records to inputs |
| Missing vs zero | `None`/SQL `NULL` preserves unavailable data instead of inventing a zero |
| Independent controls | Python validation and database constraints/grants enforce different boundaries |
| Secret lifecycle | Cryptographic generation, private storage, restricted consumers, rotation/recovery planning |

## Evidence and Limits

All 41 offline tests now pass; dependency consistency and whitespace checks passed. Live MySQL checks are recorded in [local-database-checks.md](local-database-checks.md). This is not a complete security audit or dependency vulnerability scan. Network-loss recovery remains simulated, and schema constraints were sampled rather than exhaustively tested.

Source accuracy checks cover the schedule and selected box-score fields, not every statistic. Return statistics are excluded after a documented discrepancy. Credentials are private plaintext files accessible to the host user; OS isolation and secret recovery are not implemented/tested. See [credential inventory](credentials.md).

## Next Session

Bounded MCP tools and the sequential research → writer workflow are implemented. A live Texas–Alabama sample passed factual spot checks; live missing-statistics and injected venue-text cases passed after fixing an overly strict two-claim minimum. The writer now accepts 1–6 supported claims; empty briefings and unknown references remain rejected. See [security/failure checks](security-failure-checks.md), [sample briefing](sample-briefing.md), and [model review](model-review.md).

OpenAI `gpt-6-luna` with low reasoning effort is selected and live account access is verified. The November 1 evaluation used 16 requests and 29,567 reported tokens across four runs, including two stopped missing-stat runs. These observations do not prove general factual accuracy or injection resistance.

The initial Python-served web UI is implemented on `feature/local-web-ui`, retaining the terminal fallback. See [web UI](web-ui.md) for startup, boundaries, and remaining browser review. Rehearse closer to the Monday afternoon local presentation; VM deployment remains deferred.

Use [learning-review.md](learning-review.md) for periodic whole-project checks. Continue explaining security changes before implementation and pointing to their code. Review both permitted and denied cases, and use short recall questions to check understanding.

UI follow-up: Ry approved the initial appearance. Longhorns replaced visible Stillwater branding; scrolling now occurs on generation/results or saved-sample actions, not dropdown selection. Bounded query parsing supports season game order and opponent names, now including sourced aliases with ambiguity handling. No new dependencies, database grants, model tools, or runtime web access were added. See [UI review history and security](web-ui.md) and [alias research](team-aliases.md). Ry has since reported testing generated briefings and approved richer output; automated browser and systematic responsive/keyboard verification remain unverified.

The demo search now supports sourced mascot/team-nickname variants, with 102 query checks plus an input-order assertion passing. Cowboys/Pokes/Cougars remain ambiguous in the actual imported season. Cougs and Coogs are distinct reviewed spellings; broader coverage requires collision review. Python suite remains 41 tests. See [UI behavior](web-ui.md) and [alias sources](team-aliases.md).

Ry has approved the current UI feature set as sufficient for the demo. Refresh now starts at the top; selecting a game stays in place. The intensive live-path review is complete; a presenter outline and three Mermaid diagrams are prepared. Next is abbreviated review and rehearsal. Keep feature scope fixed while preparing the presentation. UI work is on `feature/local-web-ui`; main retains the previous terminal checkpoint until an explicit merge.

## Latest Checkpoint

The writer now prefers broader use of supplied statistics across 5–6 claims, without changing the 1–6 validator, tool access, grants, schema or usage budgets. A live Alabama evaluation produced five claims whose figures matched the retrieved evidence, using four requests and 8,684 reported tokens. The 41-test suite passed after the prompt revision. Earlier live injection and missing-stat fixtures were not rerun for this revision. Ry reported the output improved.

The [glass-to-metal review](glass-to-metal-review.md) and [demo outline](demo-outline.md) are prepared. Repeat a short walkthrough, then rehearse near the presentation. Same-user secret-file access, no public/user-authenticated deployment, sampled factual evaluation, and no hard dollar cap remain explicit limits. Main has not been merged with the UI feature branch.

Subsequent abbreviated review and guided verbal rehearsal are complete. The [study script](demo-study-script.md) compiles suggested wording from each segment; a continuous timed/browser rehearsal remains separate. Post-demo priorities clarified by Ry: VM deployment with environment-specific security work, then exploring live web-assisted alias checks. Runtime aliases remain static; no remote actions or new model/web capabilities were implemented. Further features remain deferred.
