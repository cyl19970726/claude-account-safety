import unittest

from scripts import plan, verify


def minimal_profile():
    return {
        "host": {
            "os": "Darwin",
            "os_release": "25.0.0",
            "arch": "arm64",
            "python": "3.12.0",
            "python_ok": True,
        },
        "locale": {"timezone": "Asia/Taipei", "utc_offset": "+08:00", "locale": "zh_TW"},
        "proxy_env": {"HTTP_PROXY": True, "HTTPS_PROXY": True},
        "network": {
            "ipv6_supported": True,
            "ipv6_default_route": False,
            "dns_servers": ["1.1.1.1"],
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


def matching_egress():
    return {
        "comparison": {"ip_match": True, "loc_match": True},
        "endpoints": {"claude": {"ok": True, "ip": "1.2.3.4", "loc": "TW"}},
    }


class PlanTests(unittest.TestCase):
    def test_detect_os(self):
        self.assertEqual(plan.detect_os(minimal_profile(), None), "macos")
        self.assertEqual(plan.detect_os({"host": {"os": "Windows"}}, None), "windows")

    def test_plan_contains_policy_gate_and_commands(self):
        text = plan.build_plan(minimal_profile(), "macos", "TW")
        self.assertIn("政策门禁", text)
        self.assertIn("scutil --proxy", text)
        self.assertIn("verify.py", text)


class VerifyTests(unittest.TestCase):
    def test_unsupported_region_fails(self):
        report = verify.build_report(minimal_profile(), matching_egress(), "CN")
        self.assertEqual(report["overall"], "FAIL")
        self.assertEqual(
            next(c for c in report["checks"] if c["id"] == "region.supported")["status"],
            "FAIL",
        )

    def test_supported_region_with_match_has_no_fail(self):
        report = verify.build_report(minimal_profile(), matching_egress(), "TW")
        self.assertNotEqual(report["overall"], "FAIL")
        self.assertFalse(any(c["status"] == "FAIL" for c in report["checks"]))

    def test_split_egress_fails(self):
        egress = matching_egress()
        egress["comparison"] = {"ip_match": False, "loc_match": False}
        report = verify.build_report(minimal_profile(), egress, "TW")
        self.assertEqual(
            next(c for c in report["checks"] if c["id"] == "egress.consistency")["status"],
            "FAIL",
        )

    def test_proxy_layer_mismatch_fails(self):
        profile = minimal_profile()
        profile["proxy_env"]["HTTP_PROXY_value"] = "http://127.0.0.1:7897"
        profile["system_proxy"] = {"http": "127.0.0.1:7898"}
        report = verify.build_report(profile, matching_egress(), "TW")
        self.assertEqual(
            next(c for c in report["checks"] if c["id"] == "proxy.layers")["status"],
            "FAIL",
        )


if __name__ == "__main__":
    unittest.main()
