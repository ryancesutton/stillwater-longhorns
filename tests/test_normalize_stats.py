"""Synthetic fixtures only: tests do not require private downloads."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_stats import integer, normalize, normalize_team, pair, possession


class NormalizationTests(unittest.TestCase):
    def test_conversions(self):
        self.assertEqual(pair("24-38"), (24, 38))
        self.assertEqual(possession("32:31"), 1951)
        self.assertEqual(integer("-6", signed=True), -6)
        self.assertEqual(pair("10-5", bounded=False), (10, 5))

    def test_missing_is_not_zero(self):
        row = normalize_team([{"category": "turnovers", "stat": "0"}])
        self.assertEqual(row["turnovers"], 0)
        self.assertIsNone(row["rushing_yards"])
        self.assertEqual(pair(None), (None, None))

    def test_bad_values(self):
        for function, value in ((pair, "39-24"), (pair, "24/38"),
                                (possession, "32:60"), (integer, ""),
                                (integer, "-1"), (integer, "65536")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                function(value)

    def test_inconsistent_totals(self):
        stats = [{"category": k, "stat": v} for k, v in
                 (("totalYards", "100"), ("rushingYards", "50"), ("netPassingYards", "60"))]
        with self.assertRaises(ValueError):
            normalize_team(stats)

    def test_relationships(self):
        schedule = [{"id": 1, "homeId": 10, "homeTeam": "Texas", "homePoints": 7,
                     "awayId": 20, "awayTeam": "Opponent", "awayPoints": 0}]
        games = [{"id": 1, "teams": [
            {"teamId": i, "team": name, "homeAway": side, "points": points,
             "stats": [{"category": "firstDowns", "stat": "1"}]}
            for i, name, side, points in ((10, "Texas", "home", 7), (20, "Opponent", "away", 0))]}]
        self.assertEqual(len(normalize(games, schedule)), 2)
        for kind in ("team", "duplicate", "missing"):
            bad = copy.deepcopy(games)
            if kind == "team": bad[0]["teams"][0]["teamId"] = 99
            if kind == "duplicate": bad.append(copy.deepcopy(bad[0]))
            if kind == "missing": bad = []
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                normalize(bad, schedule)


if __name__ == "__main__":
    unittest.main()
