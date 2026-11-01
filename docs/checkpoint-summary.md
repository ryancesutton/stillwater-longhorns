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

All 35 offline tests now pass; dependency consistency and whitespace checks passed. Live MySQL checks are recorded in [local-database-checks.md](local-database-checks.md). This is not a complete security audit or dependency vulnerability scan. Network-loss recovery remains simulated, and schema constraints were sampled rather than exhaustively tested.

Source accuracy checks cover the schedule and selected box-score fields, not every statistic. Return statistics are excluded after a documented discrepancy. Credentials are private plaintext files accessible to the host user; OS isolation and secret recovery are not implemented/tested. See [credential inventory](credentials.md).

## Next Session

Bounded MCP tools and the sequential research → writer workflow are implemented. A live Texas–Alabama sample passed factual spot checks; live missing-statistics and injected venue-text cases passed after fixing an overly strict two-claim minimum. The writer now accepts 1–6 supported claims; empty briefings and unknown references remain rejected. See [security/failure checks](security-failure-checks.md), [sample briefing](sample-briefing.md), and [model review](model-review.md).

OpenAI `gpt-6-luna` with low reasoning effort is selected and live account access is verified. The November 1 evaluation used 16 requests and 29,567 reported tokens across four runs, including two stopped missing-stat runs. These observations do not prove general factual accuracy or injection resistance.

Next build a basic React UI on a separate branch, retaining the terminal fallback. Estimate 2–4 focused hours for a basic version, subject to findings. Rehearse closer to the Monday afternoon local presentation; VM deployment remains deferred.

Use [learning-review.md](learning-review.md) for periodic whole-project checks. Continue explaining security changes before implementation and pointing to their code. Review both permitted and denied cases, and use short recall questions to check understanding.
