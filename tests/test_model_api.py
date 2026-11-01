"""Simulate provider failures without reading real credentials or sending requests."""
import io
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from model_api import ModelError, NoRedirects, ResponsesModel


class ModelFailureTests(unittest.TestCase):
    def setUp(self):
        # Bypass credential-file loading; this sentinel is deliberately fake.
        self.model = ResponsesModel.__new__(ResponsesModel)
        self.model._key = "FAKE_KEY_FOR_TEST_ONLY"

    @patch("model_api.build_opener")
    def test_http_errors_suppress_body_and_do_not_retry(self, opener):
        for code in (401, 429, 500):
            with self.subTest(code=code):
                opener.reset_mock()
                opener.return_value.open.side_effect = HTTPError(
                    "https://api.openai.com/v1/responses", code, "private detail", {},
                    io.BytesIO(b"FAKE_PRIVATE_RESPONSE"))
                with self.assertRaises(ModelError) as caught:
                    self.model._send({"input": "test"})
                self.assertIn(str(code), str(caught.exception))
                self.assertNotIn("PRIVATE", str(caught.exception))
                self.assertNotIn("private detail", str(caught.exception))
                opener.return_value.open.assert_called_once()

    @patch("model_api.build_opener")
    def test_network_timeout_is_sanitized_without_retry(self, opener):
        opener.return_value.open.side_effect = TimeoutError("FAKE_PRIVATE_DETAIL")
        with self.assertRaisesRegex(ModelError, "details suppressed") as caught:
            self.model._send({"input": "test"})
        self.assertNotIn("PRIVATE", str(caught.exception))
        opener.return_value.open.assert_called_once()
        self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 30)

    def test_redirect_is_refused(self):
        self.assertIsNone(NoRedirects().redirect_request(
            None, None, 302, "redirect", {}, "https://example.invalid"))


if __name__ == "__main__":
    unittest.main()
