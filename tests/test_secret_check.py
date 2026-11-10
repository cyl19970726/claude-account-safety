import tempfile
import unittest
from pathlib import Path

from scripts import secret_check


class SecretCheckTests(unittest.TestCase):
    def test_redact_proxy_hides_userinfo(self):
        text = "socks5://user:pass@1.2.3.4:1080"
        redacted = secret_check.redact("proxy-userinfo", text)
        self.assertIn("1.2.3.4:1080", redacted)
        self.assertNotIn("user", redacted)
        self.assertNotIn("pass", redacted)

    def test_placeholders_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.env"
            path.write_text(
                "PROXY_SUBSCRIPTION_URL=op://Private/<provider>/subscription-url\n"
                "PROXY_PURCHASE_URL=env:PROXY_PURCHASE_URL\n",
                encoding="utf-8",
            )
            self.assertEqual(secret_check.scan_file(path), [])

    def test_proxy_url_is_detected_and_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leak.md"
            path.write_text("proxy: socks5://user:pass@1.2.3.4:1080\n", encoding="utf-8")
            findings = secret_check.scan_file(path)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["kind"], "proxy-userinfo")
            self.assertNotIn("user:pass", findings[0]["redacted"])

    def test_api_key_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leak.txt"
            path.write_text("key=sk-ant-abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
            findings = secret_check.scan_file(path)
            self.assertTrue(any(item["kind"] == "api-key" for item in findings))

    def test_ignore_next_line_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(
                "<!-- secret-check: ignore-next-line -->\n"
                "example: socks5://user:pass@1.2.3.4:1080\n",
                encoding="utf-8",
            )
            self.assertEqual(secret_check.scan_file(path), [])


if __name__ == "__main__":
    unittest.main()
