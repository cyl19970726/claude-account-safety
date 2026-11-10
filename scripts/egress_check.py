#!/usr/bin/env python3
"""Compare Claude/Cloudflare egress traces.

Read-only network check. It does not authenticate, does not send cookies, and
does not print proxy credentials.
"""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

CLAUDE_TRACE = "https://claude.ai/cdn-cgi/trace"
CF_TRACE = "https://www.cloudflare.com/cdn-cgi/trace"
ANTHROPIC_ROOT = "https://api.anthropic.com/"


def fetch(url: str, timeout: int = 12, direct: bool = False) -> dict[str, Any]:
    handlers: list[Any] = [urllib.request.HTTPSHandler(context=ssl.create_default_context())]
    if direct:
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "claude-account-safety/1.0 (read-only environment check)",
            "Accept": "text/plain,*/*",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(32768).decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": response.status,
                "url": url,
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(8192).decode("utf-8", errors="replace")
        except OSError:
            pass
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "error": f"HTTP {exc.code}",
            "body": body,
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "error": str(exc),
            "body": "",
        }


def parse_trace(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in body.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key and len(key) < 64:
                out[key] = value.strip()[:256]
    return out


def summarize_endpoint(result: dict[str, Any], trace: bool = True) -> dict[str, Any]:
    out = {
        "ok": result.get("ok", False),
        "status": result.get("status"),
        "error": result.get("error"),
    }
    if trace:
        parsed = parse_trace(result.get("body", ""))
        for key in ("ip", "loc", "colo", "http", "tls", "warp", "gateway"):
            if key in parsed:
                out[key] = parsed[key]
    return out


def build_report(timeout: int = 12, direct: bool = False) -> dict[str, Any]:
    claude_raw = fetch(CLAUDE_TRACE, timeout=timeout, direct=direct)
    cf_raw = fetch(CF_TRACE, timeout=timeout, direct=direct)
    anthropic_raw = fetch(ANTHROPIC_ROOT, timeout=timeout, direct=direct)

    claude = summarize_endpoint(claude_raw, trace=True)
    cf = summarize_endpoint(cf_raw, trace=True)
    anthropic = summarize_endpoint(anthropic_raw, trace=False)

    checks: list[dict[str, str]] = []

    def add(check_id: str, status: str, detail: str) -> None:
        checks.append({"id": check_id, "status": status, "detail": detail})

    if claude.get("ok") and claude.get("ip"):
        add("egress.claude", "PASS", f"ip={claude.get('ip')} loc={claude.get('loc')}")
    else:
        add("egress.claude", "UNKNOWN", claude.get("error") or "claude.ai trace unavailable")

    if cf.get("ok") and cf.get("ip"):
        add("egress.cloudflare", "PASS", f"ip={cf.get('ip')} loc={cf.get('loc')}")
    else:
        add("egress.cloudflare", "UNKNOWN", cf.get("error") or "cloudflare trace unavailable")

    ip_match = None
    loc_match = None
    if claude.get("ip") and cf.get("ip"):
        ip_match = claude["ip"] == cf["ip"]
        loc_match = claude.get("loc") == cf.get("loc")
        add(
            "egress.consistency",
            "PASS" if (ip_match and loc_match) else "FAIL",
            f"ip_match={ip_match} loc_match={loc_match}",
        )
    else:
        add("egress.consistency", "UNKNOWN", "need both traces to compare")

    add(
        "anthropic.reachable",
        "PASS" if anthropic.get("status") in (200, 401, 403, 404) else "UNKNOWN",
        f"status={anthropic.get('status')} error={anthropic.get('error')}",
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "direct": direct,
        "endpoints": {
            "claude": claude,
            "cloudflare": cf,
            "anthropic": anthropic,
        },
        "comparison": {
            "ip_match": ip_match,
            "loc_match": loc_match,
            "split_egress": (ip_match is False or loc_match is False),
        },
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Claude and Cloudflare egress traces")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--output", help="write JSON to this path")
    parser.add_argument("--timeout", type=int, default=12, help="per-request timeout seconds")
    parser.add_argument("--direct", action="store_true", help="ignore proxy env for this check")
    args = parser.parse_args()

    report = build_report(timeout=args.timeout, direct=args.direct)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    if args.json:
        print(text)
    else:
        for check in report["checks"]:
            print(f"{check['status']:7} {check['id']}: {check['detail']}")
        if args.output:
            print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
