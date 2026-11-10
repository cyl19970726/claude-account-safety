#!/usr/bin/env python3
"""Scan a skill directory for accidental secrets and print redacted findings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", "tests"}
SKIP_FILES = {
    "secret_check.py",
    "12-secrets.md",
    "secrets.example.env",
}
MAX_BYTES = 1_000_000

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("subscription-uri", re.compile(
        r"\b(?:ss|vmess|vless|trojan|hysteria2?|hy2|tuic)://[^\s\"'<>]+", re.I)),
    ("proxy-userinfo", re.compile(
        r"\b(?:socks5h?|https?)://[^/\s:@]+:[^/\s@]+@[^\s\"'<>]+", re.I)),
    ("api-key", re.compile(
        r"\b(?:sk-ant-[A-Za-z0-9_-]{16,}|sk-proj-[A-Za-z0-9_-]{16,}"
        r"|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
        r"|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16})\b")),
    ("private-key", re.compile(
        r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----")),
    ("token-query", re.compile(
        r"[?&](?:token|key|sub|subscription|access_token|api_key)=([A-Za-z0-9._~-]{12,})",
        re.I)),
    ("env-secret", re.compile(
        r"(?i)\b(?:ANTHROPIC_API_KEY|OPENAI_API_KEY|PROXY_SUBSCRIPTION_URL|PROXY_PURCHASE_URL)"
        r"\s*=\s*([^\s#]+)")),
]


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return (
        lowered.startswith(("op://", "env:", "keychain:", "<", "$"))
        or "your_" in lowered
        or "example" in lowered
        or "placeholder" in lowered
        or lowered in {"", "none", "null", "redacted", "changeme"}
    )


def redact(kind: str, text: str) -> str:
    if kind == "proxy-userinfo":
        try:
            parts = urlsplit(text)
            host = parts.hostname or "host"
            port = f":{parts.port}" if parts.port else ""
            return f"{parts.scheme}://{host}{port} [redacted]"
        except ValueError:
            return "[redacted proxy URL]"
    if kind == "subscription-uri":
        scheme = text.split("://", 1)[0]
        return f"{scheme}://[redacted]"
    if kind in {"api-key", "env-secret"}:
        if len(text) <= 8:
            return "[redacted]"
        return f"{text[:4]}... [redacted, len={len(text)}]"
    if kind == "private-key":
        return "[private-key]"
    if kind == "token-query":
        return "[redacted query token]"
    return "[redacted]"


def scan_file(path: Path) -> list[dict[str, Any]]:
    try:
        if path.stat().st_size > MAX_BYTES:
            return []
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings: list[dict[str, Any]] = []
    ignore_next = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "secret-check: ignore-next-line" in line:
            ignore_next = True
            continue
        if ignore_next:
            ignore_next = False
            continue
        for kind, pattern in PATTERNS:
            for match in pattern.finditer(line):
                raw = match.group(1) if match.lastindex else match.group(0)
                if is_placeholder(raw):
                    continue
                findings.append({
                    "file": str(path),
                    "line": line_no,
                    "kind": kind,
                    "redacted": redact(kind, raw),
                })
    return findings


def scan_root(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        findings.extend(scan_file(path))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan for accidental secrets")
    parser.add_argument("--root", default=".", help="directory to scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings = scan_root(root)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "count": len(findings),
            "findings": findings,
        }, ensure_ascii=False, indent=2))
    elif findings:
        if not args.quiet:
            print(f"secret-check: {len(findings)} finding(s)")
            for item in findings:
                print(f"  {item['file']}:{item['line']}  {item['kind']}  {item['redacted']}")
    else:
        if not args.quiet:
            print("secret-check: no high-confidence secrets found")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
