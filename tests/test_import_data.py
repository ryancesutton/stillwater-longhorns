"""Transaction simulation: does not establish MySQL syntax or enforcement."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_data import (
    GAME_COLUMNS, STAT_COLUMNS, ImportFailure, PreparedImport, import_prepared,
)


class FakeConnection:
    def __init__(self):
        self.autocommit = False
        self.in_transaction = False
        self.state = {name: {} for name in ("teams", "games", "team_game_stats", "ingestion_runs")}
        self.calls = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_table = None
        self.uncertain_commit = False
        self.closed_cursor = False

    def cursor(self):
        return FakeCursor(self)

    def start_transaction(self):
        assert not self.in_transaction
        self.snapshot = copy.deepcopy(self.state)
        self.in_transaction = True

    def commit(self):
        self.commits += 1
        self.in_transaction = False
        if self.uncertain_commit and self.commits == 2:
            # Simulate server committing, then client losing the acknowledgement.
            raise RuntimeError("private connector details")

    def rollback(self):
        if self.in_transaction:
            self.state = self.snapshot
        self.in_transaction = False
        self.rollbacks += 1


class FakeCursor:
    def __init__(self, connection):
        self.db = connection
        self.lastrowid = None
        self.result = None

    def execute(self, sql, parameters):
        self.db.calls.append((sql, parameters))
        if sql.startswith("INSERT INTO"):
            table = sql.split()[2]
            if table == self.db.fail_table:
                raise RuntimeError("password=should-not-appear-in-error")
            columns = {
                "teams": ("source_team_id", "name", "ingestion_run_id"),
                "games": GAME_COLUMNS, "team_game_stats": STAT_COLUMNS,
                "ingestion_runs": ("source", "endpoint", "parameters", "retrieved", "hash",
                                   "path", "version", "dirty", "started", "status"),
            }[table]
            row = dict(zip(columns, parameters))
            rows = self.db.state[table]
            if table == "ingestion_runs":
                key = len(rows) + 1
            elif table == "team_game_stats":
                key = (row["game_id"], row["team_id"])
            else:
                key = row["source_team_id" if table == "teams" else "source_game_id"]
            internal_id = rows[key]["internal_id"] if key in rows else len(rows) + 100
            rows[key] = {**row, "internal_id": internal_id}
            self.lastrowid = key if table == "ingestion_runs" else internal_id
        elif sql.startswith("SELECT"):
            table = "teams" if "FROM teams" in sql else "games"
            self.result = (self.db.state[table][parameters[0]]["internal_id"],)
        elif sql.startswith("UPDATE ingestion_runs"):
            status, finished, count, error, key = parameters
            self.db.state["ingestion_runs"][key].update(
                status=status, finished=finished, count=count, error=error)
        else:
            raise AssertionError("Unexpected SQL operation")

    def fetchone(self):
        return self.result

    def close(self):
        self.db.closed_cursor = True


def prepared():
    source = {"source": "CollegeFootballData", "endpoint": "sample", "parameters": {},
              "retrieved_at_utc": "2026-10-27T01:00:00+00:00", "sha256": "a" * 64,
              "raw_file_path": "sample/response.json"}
    game = dict.fromkeys(GAME_COLUMNS)
    game.update(source_game_id=99, home_source_team_id=10, away_source_team_id=20)
    stats = []
    for team in (10, 20):
        row = dict.fromkeys(STAT_COLUMNS)
        row.update(source_game_id=99, source_team_id=team, turnovers=0)
        stats.append(row)
    return PreparedImport(
        [{"source_team_id": 10, "name": "Texas"}, {"source_team_id": 20, "name": "Opponent"}],
        [game], stats, [source, dict(source, endpoint="stats")], "a" * 40, False,
    )


class ImportTests(unittest.TestCase):
    def test_repeat_import_and_mapping(self):
        db = FakeConnection()
        import_prepared(db, prepared())
        ids = {key: row["internal_id"] for key, row in db.state["teams"].items()}
        import_prepared(db, prepared())
        self.assertEqual([len(db.state[t]) for t in db.state], [2, 1, 2, 4])
        self.assertEqual(ids, {key: row["internal_id"] for key, row in db.state["teams"].items()})
        game = db.state["games"][99]
        self.assertEqual((game["home_team_id"], game["away_team_id"]), (ids[10], ids[20]))
        for row in db.state["team_game_stats"].values():
            self.assertEqual(row["game_id"], game["internal_id"])
            self.assertIsNone(row["rushing_yards"])
            self.assertEqual(row["turnovers"], 0)
        self.assertTrue(all(r["status"] == "succeeded" for r in db.state["ingestion_runs"].values()))

    def test_values_are_bound_separately(self):
        db, data = FakeConnection(), prepared()
        malicious = "Opponent'); DROP TABLE games; --"
        data.teams[1]["name"] = malicious
        import_prepared(db, data)
        self.assertTrue(any(malicious in params for _, params in db.calls))
        self.assertTrue(all(malicious not in sql for sql, _ in db.calls))

    def test_failure_restores_existing_dataset(self):
        for table in ("games", "team_game_stats"):
            with self.subTest(table=table):
                db = FakeConnection()
                import_prepared(db, prepared())
                original = copy.deepcopy({key: db.state[key] for key in ("teams", "games", "team_game_stats")})
                db.fail_table = table
                data = prepared()
                data.teams[0]["name"] = "Changed"
                with self.assertRaises(ImportFailure) as error:
                    import_prepared(db, data)
                self.assertNotIn("password", str(error.exception))
                self.assertEqual(original, {key: db.state[key] for key in original})
                self.assertEqual([db.state["ingestion_runs"][i]["status"] for i in (3, 4)], ["failed", "failed"])

    def test_ambiguous_commit_is_not_marked_failed(self):
        db = FakeConnection()
        db.uncertain_commit = True
        with self.assertRaisesRegex(ImportFailure, "uncertain"):
            import_prepared(db, prepared())
        self.assertTrue(all(row["status"] == "succeeded" for row in db.state["ingestion_runs"].values()))

    def test_unsafe_connection_rejected_before_work(self):
        for attribute in ("autocommit", "in_transaction"):
            db = FakeConnection()
            setattr(db, attribute, True)
            with self.assertRaises(ImportFailure):
                import_prepared(db, prepared())
            self.assertEqual(db.calls, [])


if __name__ == "__main__":
    unittest.main()
