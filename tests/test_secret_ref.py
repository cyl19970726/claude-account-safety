import os
import unittest
from unittest.mock import patch

from scripts import secret_ref


class SecretRefTests(unittest.TestCase):
    def test_env_reference(self):
        with patch.dict(os.environ, {"MY_TEST_SECRET": "abc123"}):
            self.assertEqual(secret_ref.resolve("env:MY_TEST_SECRET"), "abc123")
            self.assertEqual(secret_ref.resolve("env://MY_TEST_SECRET"), "abc123")

    def test_missing_env_reference(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(secret_ref.SecretError):
                secret_ref.resolve("env:MISSING_SECRET")

    def test_unsupported_reference(self):
        with self.assertRaises(secret_ref.SecretError):
            secret_ref.resolve("https://example.com/sub?token=abc")


if __name__ == "__main__":
    unittest.main()
