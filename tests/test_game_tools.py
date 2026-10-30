import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import game_tools


class ToolTests(unittest.TestCase):
    @patch("game_tools.connect_mcp")
    def test_invalid_inputs_never_connect(self, connect):
        for value in (True, "2023", -1, 2101):
            with self.subTest(value=value), self.assertRaises(ValueError):
                game_tools.list_games(value)
        for value in (0, 26, "5", True):
            with self.assertRaises(ValueError):
                game_tools.list_games(limit=value)
        with self.assertRaises(ValueError):
            game_tools.get_game_data("1; DROP TABLE games")
        connect.assert_not_called()

    @patch("game_tools.connect_mcp")
    def test_limit_and_bound_parameters(self, connect):
        cursor = connect.return_value.cursor.return_value
        cursor.fetchall.return_value = [{"source_game_id": i} for i in range(3)]
        result = game_tools.list_games(2023, 2)
        self.assertEqual(len(result["games"]), 2)
        self.assertTrue(result["truncated"])
        sql, params = cursor.execute.call_args.args
        self.assertIn("LIMIT %s", sql)
        self.assertIn("MAX_EXECUTION_TIME(2000)", sql)
        self.assertEqual(params, (2023, "Texas", "Texas", 3))
        connect.return_value.start_transaction.assert_called_once_with(readonly=True)
        connect.return_value.close.assert_called_once()

    @patch("game_tools.connect_mcp")
    def test_missing_game_is_explicit(self, connect):
        connect.return_value.cursor.return_value.fetchall.return_value = []
        self.assertEqual(game_tools.get_game_data(123), {"status": "not_found", "source_game_id": 123})

    @patch("game_tools.connect_mcp", side_effect=RuntimeError("password=private"))
    def test_database_failure_is_sanitized(self, connect):
        self.assertEqual(game_tools.list_games(), {"status": "error", "code": "retrieval_unavailable"})


if __name__ == "__main__":
    unittest.main()
