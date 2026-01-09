import os
import unittest
from unittest import mock


class TestHFToken(unittest.TestCase):
    def setUp(self) -> None:
        # Import fresh each time to avoid cross-test cache bleed
        import importlib
        self.hf_token = importlib.import_module("hf_token")
        self.hf_token._cached_token = None

    def tearDown(self) -> None:
        self.hf_token._cached_token = None

    def test_cli_token_wins_and_is_cached(self) -> None:
        token = self.hf_token.get_hf_token("hf_cli")
        self.assertEqual(token, "hf_cli")
        self.assertEqual(self.hf_token.get_hf_token(None), "hf_cli")

    def test_env_token_used_when_no_cli(self) -> None:
        with mock.patch.dict(os.environ, {"HF_TOKEN": "hf_env"}, clear=False):
            self.assertEqual(self.hf_token.get_hf_token(None), "hf_env")

    def test_keychain_used_when_no_cli_or_env(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("hf_token.subprocess.run") as run:
                run.return_value = mock.Mock(stdout="hf_keychain\n")
                token = self.hf_token.get_hf_token(None)
                self.assertEqual(token, "hf_keychain")
                run.assert_called_once()

    def test_keychain_not_called_after_cached(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("hf_token.subprocess.run") as run:
                run.return_value = mock.Mock(stdout="hf_keychain\n")
                self.assertEqual(self.hf_token.get_hf_token(None), "hf_keychain")
                self.assertEqual(self.hf_token.get_hf_token(None), "hf_keychain")
                run.assert_called_once()

    def test_keychain_failure_returns_none(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("hf_token.subprocess.run", side_effect=FileNotFoundError()):
                self.assertIsNone(self.hf_token.get_hf_token(None))


if __name__ == "__main__":
    unittest.main()
