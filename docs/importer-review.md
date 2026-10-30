# Offline Importer Review

Status: prepared for review, not connected to MySQL. The CLI only prepares records and prints a summary; it cannot create a connection or execute writes. No connector dependency or credential configuration has been added.

## Walk Through the Code

Open [import_data.py](../scripts/import_data.py) alongside the [schema draft](../db/schema-draft.sql).

1. `prepare()` verifies each response against adjacent metadata and checks the expected CFBD request scope. It normalizes both responses before any database work. Paths must resolve inside the private archive. It retains the same metadata used during verification, avoiding a second read of metadata after validation.
2. `_upsert()` builds SQL from developer-owned table/column constants. All downloaded values are supplied separately as parameter tuples to `cursor.execute(sql, parameters)`. This is the parameterization boundary; regex validation is not the SQL-injection defense. No identifiers come from an agent or source record.
3. `import_prepared()` requires a dedicated idle connection with autocommit disabled. It persists two `running` import attempts: one for the schedule response and one for the statistics response.
4. In a new transaction it upserts teams, looks up their internal IDs, upserts games using those IDs, and looks up internal game IDs. It then upserts statistics using the internal game/team IDs. Schedule-derived teams/games reference the schedule run; stats reference the stats run.
5. Dataset changes and both `succeeded` statuses commit together. If a write fails and rollback succeeds, a separate transaction marks both attempts failed. Error summaries are fixed messages; source values and connector exception details are not logged.

An upsert means insert if the unique key is new, otherwise update the existing row. Database unique keys—not this Python function alone—must prevent duplicate source identities. `records_processed` counts attempted normalized rows on success, not a distinction between new/changed/unchanged rows. Schedule count includes teams plus games; a rolled-back run records zero persisted dataset rows.

## Failure Boundaries

- Failure before `prepare()` completes produces no database calls.
- Failure saving initial attempts produces no dataset writes. A lost commit acknowledgement can still leave run rows; reconcile state.
- Failed dataset writes trigger rollback before failure-status writes.
- A failed commit acknowledgement may hide a successful server commit. The importer reports an uncertain outcome without falsely overwriting statuses as failed. Do not automatically retry; inspect the run and dataset state.
- If rollback or recording failure status cannot be confirmed, the importer reports that uncertainty. Crashes can leave `running` attempts; these need reconciliation, not an automatic assumption of failure.
- The connection owner must always close the dedicated connection. No concurrent-import or recovery automation is included in this first version.

`importer_version` records the current Git commit and `importer_worktree_dirty` includes untracked files. Dirty code is not exactly reproducible from its commit. The same two source files can be reimported with a new pair of run IDs while retaining dataset identities.

## What Has Been Tested

The offline suite uses synthetic fixtures and a transactional simulation to check:

- Repeated loads retain dataset identities and create fresh run records.
- Source IDs map to internal foreign-key values.
- Missing statistics remain `None` while explicit zero remains zero.
- SQL-like text stays in bound parameters, not statement text.
- Failures during game/stat writes restore the existing simulated dataset and record failed attempts.
- A commit that succeeds server-side but loses its acknowledgement is reported as uncertain.
- Autocommit-enabled or already-active connections are rejected before import statements.

The simulation does not parse SQL or emulate MySQL privilege/constraint enforcement. MySQL 8.4 syntax, connector behavior, real rollback and repeat-import results, and denied-access checks remain unverified until integration testing. This layer does not enforce MCP access or OS secret isolation.

## Commands for Review

```bash
python -m unittest discover -s tests -v
python scripts/import_data.py \
  data/raw/cfbd-games-20261027T015648114714Z/response.json \
  data/raw/cfbd-team-stats-20261027T020832174803Z/response.json
```

The second command has no write mode. Database configuration, verified server version, connector selection, reviewed account grants, and explicit integration checks come next.

## Official References

- [Connector/Python execute parameters](https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html)
- [MySQL 8.4 insert-or-update row aliases](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)
- [Connector/Python transaction example](https://dev.mysql.com/doc/connector-python/en/connector-python-example-cursor-transaction.html)
