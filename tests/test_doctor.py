import tempfile
import unittest
from pathlib import Path

from scripts import doctor


def minimal_profile():
    return {
        "host": {
            "os": "Darwin",
            "os_release": "25.0.0",
            "arch": "arm64",
            "python": "3.12.0",
            "python_ok": True,
        },
        "locale": {"timezone": "Asia/Taipei", "utc_offset": "+08:00"},
        "proxy_env": {
            "HTTP_PROXY": True,
            "HTTPS_PROXY": True,
            "http_proxy": False,
            "https_proxy": False,
        },
        "network": {
            "ipv6_supported": True,
            "ipv6_default_route": False,
            "dns_servers": ["1.1.1.1"],
            "default_route": "utun8",
        },
        "claude": {
            "cli_found": True,
            "cli_path": "/usr/local/bin/claude",
            "cli_version": "2.1.312",
            "base_url_set": False,
            "base_url_host": None,
        },
        "browsers": {"chrome": True},
        "proxy_clients": {"clash": True},
    }


class DoctorTests(unittest.TestCase):
    def test_scrub_proxy_removes_userinfo_and_query(self):
        value = "socks5://user:pass@1.2.3.4:1080/path?token=abc"
        self.assertEqual(doctor._scrub_proxy(value), "socks5://1.2.3.4:1080")

    def test_scrub_proxy_accepts_bare_host_port(self):
        self.assertEqual(doctor._scrub_proxy("1.2.3.4:8080"), "http://1.2.3.4:8080")

    def test_parse_scutil_proxy(self):
        text = """
<dictionary> {
  HTTPEnable : 1
  HTTPPort : 7897
  HTTPProxy : 127.0.0.1
  HTTPSEnable : 1
  HTTPSPort : 7897
  HTTPSProxy : 127.0.0.1
  SOCKSEnable : 0
}
"""
        parsed = doctor._parse_scutil_proxy(text)
        self.assertTrue(parsed["http_enabled"])
        self.assertTrue(parsed["https_enabled"])
        self.assertFalse(parsed["socks_enabled"])
        self.assertEqual(parsed["http"], "127.0.0.1:7897")

    def test_build_checks_flags_third_party_base_url(self):
        profile = minimal_profile()
        profile["claude"]["base_url_set"] = True
        profile["claude"]["base_url_host"] = "relay.example.com"
        checks = doctor.build_checks(profile)
        by_id = {item["id"]: item for item in checks}
        self.assertEqual(by_id["claude.base_url"]["status"], "FAIL")

    def test_build_checks_partial_proxy_is_unknown(self):
        profile = minimal_profile()
        profile["proxy_env"]["HTTPS_PROXY"] = False
        checks = doctor.build_checks(profile)
        by_id = {item["id"]: item for item in checks}
        self.assertEqual(by_id["proxy.env"]["status"], "UNKNOWN")

    def test_locale_info_has_expected_keys(self):
        info = doctor.locale_info()
        for key in ("timezone", "utc_offset", "locale", "lang_env", "lc_all"):
            self.assertIn(key, info)

    def test_build_profile_is_json_serializable(self):
        profile = doctor.build_profile()
        self.assertIn("checks", profile)
        self.assertIn("host", profile)
        self.assertIn("claude", profile)


if __name__ == "__main__":
    unittest.main()
