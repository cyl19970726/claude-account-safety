#!/usr/bin/env python3
"""Combine machine profile and egress report into a verification report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

# Coarse local list only. The official page is authoritative and may change.
KNOWN_SUPPORTED = {
    "US", "CA", "GB", "IE", "FR", "DE", "NL", "BE", "LU", "CH", "AT",
    "IT", "ES", "PT", "SE", "NO", "DK", "FI", "IS", "PL", "CZ", "SK",
    "HU", "SI", "HR", "EE", "LV", "LT", "GR", "JP", "KR", "TW", "SG",
    "AU", "NZ", "IN", "IL", "AE", "SA", "ZA", "BR", "MX", "AR", "CL",
    "CO", "PE", "TH", "MY", "PH", "ID", "VN",
}
KNOWN_UNSUPPORTED = {"CN", "HK", "MO", "RU", "IR", "KP", "SY", "CU"}


def add(checks: list[dict[str, str]], check_id: str, status: str, detail: str) -> None:
    checks.append({"id": check_id, "status": status, "detail": detail})


def region_check(region: str | None) -> tuple[str, str]:
    if not region:
        return "UNKNOWN", "no region supplied; confirm with official supported-regions page"
    code = region.upper()
    if code in KNOWN_UNSUPPORTED:
        return "FAIL", f"{code} is in the local unsupported list; official page is authoritative"
    if code in KNOWN_SUPPORTED:
        return "PASS", f"{code} is in the local coarse supported list; confirm official page"
    return "UNKNOWN", f"{code} not in local coarse list; confirm official page"


def profile_value(profile: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = profile
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def host_port(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None
    raw = value if "://" in value else "http://" + value
    try:
        parts = urlsplit(raw)
    except ValueError:
        return None
    if not parts.hostname:
        return None
    return f"{parts.hostname}:{parts.port or ''}".rstrip(":")


def build_report(profile: dict[str, Any], egress: dict[str, Any] | None, region: str | None) -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    status, detail = region_check(region)
    add(checks, "region.supported", status, detail)

    python_ok = profile_value(profile, "host.python_ok")
    add(
        checks,
        "host.python",
        "PASS" if python_ok else "FAIL",
        f"Python {profile_value(profile, 'host.python', 'unknown')} (need >= 3.10)",
    )

    cli = profile_value(profile, "claude.cli_found", False)
    add(
        checks,
        "claude.cli",
        "PASS" if cli else "UNKNOWN",
        profile_value(profile, "claude.cli_path") or "claude not found",
    )

    base_host = profile_value(profile, "claude.base_url_host")
    if base_host and base_host != "api.anthropic.com":
        add(checks, "claude.base_url", "FAIL", f"third-party endpoint host={base_host!r}")
    else:
        add(checks, "claude.base_url", "PASS", "official endpoint or not set")

    http_set = bool(profile_value(profile, "proxy_env.HTTP_PROXY") or profile_value(profile, "proxy_env.http_proxy"))
    https_set = bool(profile_value(profile, "proxy_env.HTTPS_PROXY") or profile_value(profile, "proxy_env.https_proxy"))
    add(
        checks,
        "proxy.env",
        "PASS" if http_set == https_set else "UNKNOWN",
        f"HTTP={http_set} HTTPS={https_set}",
    )

    env_http = profile_value(profile, "proxy_env.HTTP_PROXY_value") or profile_value(profile, "proxy_env.http_proxy_value")
    sys_http = profile_value(profile, "system_proxy.http")
    if env_http and sys_http:
        same = host_port(env_http) == host_port(sys_http)
        add(
            checks,
            "proxy.layers",
            "PASS" if same else "FAIL",
            f"env={host_port(env_http)} system={host_port(sys_http)}",
        )
    else:
        add(checks, "proxy.layers", "UNKNOWN", "system proxy or env proxy endpoint unavailable")

    dns = profile_value(profile, "network.dns_servers", []) or []
    add(
        checks,
        "network.dns",
        "PASS" if dns else "UNKNOWN",
        f"{len(dns)} DNS server(s)" if dns else "no DNS servers detected",
    )

    ipv6_default = profile_value(profile, "network.ipv6_default_route")
    if ipv6_default is True:
        add(checks, "network.ipv6", "UNKNOWN", "IPv6 default route present; verify no bypass")
    elif ipv6_default is False:
        add(checks, "network.ipv6", "PASS", "no IPv6 default route detected")
    else:
        add(checks, "network.ipv6", "UNKNOWN", "IPv6 default route unknown")

    if egress:
        comp = egress.get("comparison", {})
        if comp.get("ip_match") is True and comp.get("loc_match") is True:
            add(checks, "egress.consistency", "PASS", "Claude and Cloudflare traces match")
        elif comp.get("ip_match") is False or comp.get("loc_match") is False:
            add(checks, "egress.consistency", "FAIL", f"split egress: {comp}")
        else:
            add(checks, "egress.consistency", "UNKNOWN", "could not compare traces")

        claude_ep = egress.get("endpoints", {}).get("claude", {})
        add(
            checks,
            "egress.claude",
            "PASS" if claude_ep.get("ok") and claude_ep.get("ip") else "UNKNOWN",
            f"ip={claude_ep.get('ip')} loc={claude_ep.get('loc')} error={claude_ep.get('error')}",
        )
        egress_loc = (claude_ep.get("loc") or "").upper()
        if region and egress_loc:
            add(
                checks,
                "egress.region",
                "PASS" if egress_loc == region.upper() else "UNKNOWN",
                f"declared={region.upper()} egress_loc={egress_loc}; confirm if intentional",
            )
    else:
        add(checks, "egress.consistency", "UNKNOWN", "no egress report; run egress_check.py")
        add(checks, "egress.claude", "UNKNOWN", "no egress report; run egress_check.py")

    add(
        checks,
        "timezone.present",
        "PASS" if profile_value(profile, "locale.timezone") else "UNKNOWN",
        str(profile_value(profile, "locale.timezone", "unknown")),
    )
    add(checks, "browser.webrtc", "UNKNOWN", "manual browser check required")
    add(checks, "browser.dns", "UNKNOWN", "manual browser check required")
    add(checks, "account.ownership", "UNKNOWN", "user must confirm: personal, not shared")
    add(checks, "account.payment", "UNKNOWN", "user must confirm: official, own/authorized payment")
    add(checks, "account.2fa", "UNKNOWN", "user must confirm")

    counts: dict[str, int] = {}
    for check in checks:
        counts[check["status"]] = counts.get(check["status"], 0) + 1

    if counts.get("FAIL", 0):
        overall = "FAIL"
    elif counts.get("UNKNOWN", 0) > 4:
        overall = "ATTENTION"
    else:
        overall = "PASS"

    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "region": region,
        "overall": overall,
        "counts": counts,
        "checks": checks,
        "notes": [
            "PASS only means the check passed; it is not a guarantee against account bans.",
            "UNKNOWN must be resolved manually or explicitly accepted.",
            "Official supported-regions page is authoritative over the local coarse list.",
        ],
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Claude Account Safety · 验收报告",
        "",
        f"- 地区：`{report.get('region') or '未提供'}`",
        f"- 总体：`{report['overall']}`",
        f"- 统计：{', '.join(f'{k}={v}' for k, v in report['counts'].items())}",
        "",
        "| 检查 | 状态 | 说明 |",
        "|---|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| `{check['id']}` | `{check['status']}` | {check['detail']} |")
    lines.append("")
    lines.append("## 说明")
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Claude environment profile and egress")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--egress")
    parser.add_argument("--region", help="declared ISO region, e.g. TW")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--output", help="write report to this path")
    parser.add_argument("--strict", action="store_true", help="exit nonzero when UNKNOWN exists")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"error: profile not found: {profile_path}", file=sys.stderr)
        return 2
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    egress = None
    if args.egress:
        egress_path = Path(args.egress)
        if egress_path.exists():
            egress = json.loads(egress_path.read_text(encoding="utf-8"))
        else:
            print(f"warning: egress report not found: {egress_path}", file=sys.stderr)
    report = build_report(profile, egress, args.region)

    if args.markdown:
        text = to_markdown(report)
    else:
        text = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)

    if report["overall"] == "FAIL":
        return 1
    if args.strict and report["counts"].get("UNKNOWN", 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
