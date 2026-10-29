import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_games import load_verified, normalize_schedule, utc_datetime


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = {"id": 1, "season": 2023, "completed": True,
                     "seasonType": "regular", "startDate": "2023-09-02T14:30:00-05:00",
                     "homeId": 10, "homeTeam": "Texas", "awayId": 20,
                     "awayTeam": "Opponent", "homePoints": 7, "awayPoints": 0,
                     "neutralSite": False, "venue": None}

    def test_deduplication_and_utc(self):
        second = dict(self.game, id=2)
        teams, games = normalize_schedule([self.game, second])
        self.assertEqual(len(teams), 2)
        self.assertEqual(len(games), 2)
        self.assertEqual(games[0]["start_time_utc"], datetime(2023, 9, 2, 19, 30))
        self.assertIsNone(games[0]["venue"])

    def test_bad_timestamps(self):
        for value in ("not-a-date", "2023-09-02T19:30:00", "2023-02-30T00:00:00Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                utc_datetime(value)

    def test_invalid_records(self):
        for field, value in (("homePoints", -1), ("homeId", True),
                             ("awayId", 10), ("neutralSite", 1), ("completed", False)):
            bad = dict(self.game, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_schedule([bad])
        with self.assertRaises(ValueError):
            normalize_schedule([self.game, self.game])
        with self.assertRaises(ValueError):
            normalize_schedule([self.game, dict(self.game, id=2, awayTeam="Different")])

    def test_integrity_and_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.json"
            body = b'[]'
            path.write_bytes(body)
            metadata = {"sha256": hashlib.sha256(body).hexdigest(), "byte_count": 2,
                        "source": "CollegeFootballData", "endpoint": "sample",
                        "parameters": {"year": 2023, "team": "Texas", "seasonType": "both"},
                        "http_status": 200, "retrieved_at_utc": "2026-10-27T01:56:48+00:00"}
            meta_path = path.with_name("metadata.json")
            meta_path.write_text(json.dumps(metadata))
            self.assertEqual(load_verified(path, "sample"), [])
            with self.assertRaises(ValueError):
                load_verified(path, "other-endpoint")
            path.write_bytes(b'[1]')
            with self.assertRaises(ValueError):
                load_verified(path, "sample")


if __name__ == "__main__":
    unittest.main()
