#!/usr/bin/env python3
"""Read-only audit of local Claude data. Never deletes or moves anything."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

NEVER_DELETE = {"cli_config", "config", "credentials", "conversation"}


def candidate_paths(home: Path | None = None) -> list[dict[str, str]]:
    home = home or Path.home()
    system = platform.system()
    items: list[dict[str, str]] = []

    def add(category: str, path: Path, note: str) -> None:
        items.append({"category": category, "path": str(path), "note": note})

    if system == "Darwin":
        add("desktop_data", home / "Library" / "Application Support" / "Claude",
            "desktop data; may include conversations/settings; export before any cleanup")
        add("cache", home / "Library" / "Caches" / "Claude",
            "cache; safe to remove after backup")
        add("cache", home / "Library" / "Caches" / "com.anthropic.claudefordesktop",
            "desktop cache; verify bundle id before removal")
        add("logs", home / "Library" / "Logs" / "Claude",
            "logs; may contain diagnostic evidence")
    elif system == "Windows":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        add("desktop_data", appdata / "Claude",
            "desktop data; may include conversations/settings; export before cleanup")
        add("cache", local / "Claude" / "Cache",
            "cache; safe to remove after backup")
        add("cache", local / "AnthropicClaude",
            "desktop app data/cache; verify contents before removal")
        add("logs", appdata / "Claude" / "logs",
            "logs; may contain diagnostic evidence")
    else:
        config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
        data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
        state = Path(os.environ.get("XDG_STATE_HOME", home / ".local" / "state"))
        add("desktop_data", config / "Claude",
            "desktop data; may include conversations/settings; export before cleanup")
        add("cache", cache / "Claude",
            "cache; safe to remove after backup")
        add("logs", state / "Claude" / "logs",
            "logs; may contain diagnostic evidence")
        add("desktop_data", data / "Claude",
            "desktop data; verify before cleanup")

    claude_root = home / ".claude"
    add("conversation", claude_root / "projects",
        "full session transcripts (JSONL); may contain prompts, tool output and secrets")
    add("conversation", claude_root / "history.jsonl",
        "prompt history; up-arrow / Ctrl+R; may contain sensitive prompts")
    add("config", claude_root / "settings.json", "user settings; audit only")
    add("config", claude_root / "settings.local.json", "local settings; audit only")
    add("config", claude_root / "CLAUDE.md", "user memory; audit only")
    add("config", claude_root / "backups", "config backups; may contain old settings")
    add("config", claude_root / "shell-snapshots", "shell snapshots; may contain env")
    add("config", claude_root / "sessions", "session metadata; audit only")
    add("config", claude_root / "session-env", "session environment; audit only")
    add("config", claude_root / "plugins", "plugins; do not delete as a whole")
    add("config", claude_root / "skills", "skills; do not delete as a whole")
    add("cache", claude_root / "cache", "cache; safe to remove after backup")
    add("logs", claude_root / "logs", "logs; may contain diagnostic evidence")
    add("logs", claude_root / "debug", "debug logs; may contain request details")
    add("cli_config", home / ".claude.json",
        "global config; includes projects/machineID/userID; do not delete")
    return items


def path_stats(path: Path, max_entries: int = 200_000) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return {"exists": False, "size_bytes": 0, "files": 0, "dirs": 0, "symlink": False}
    if path.is_symlink():
        return {"exists": True, "size_bytes": 0, "files": 0, "dirs": 0, "symlink": True}
    size = 0
    files = 0
    dirs = 0
    entries = 0
    if path.is_file():
        try:
            size = path.stat().st_size
        except OSError:
            pass
        return {"exists": True, "size_bytes": size, "files": 1, "dirs": 0, "symlink": False}
    for root, dirnames, filenames in os.walk(path, followlinks=False):
        dirs += len(dirnames)
        for name in filenames:
            entries += 1
            if entries > max_entries:
                return {"exists": True, "size_bytes": size, "files": files, "dirs": dirs,
                        "symlink": False, "truncated": True}
            try:
                size += (Path(root) / name).stat().st_size
                files += 1
            except OSError:
                continue
    return {"exists": True, "size_bytes": size, "files": files, "dirs": dirs, "symlink": False}


def _jsonl_compaction(path: Path, max_lines: int = 200_000) -> dict[str, Any]:
    lines = 0
    compact_boundaries = 0
    compact_summaries = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            lines += 1
            if lines > max_lines:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            kind = str(obj.get("type", ""))
            subtype = str(obj.get("subtype", ""))
            if kind in {"compact_boundary", "summary"} or subtype in {"compact_boundary", "summary"}:
                compact_boundaries += 1
            if obj.get("isCompactSummary") is True:
                compact_summaries += 1
            message = obj.get("message")
            if isinstance(message, dict) and message.get("isCompactSummary") is True:
                compact_summaries += 1
    return {
        "lines": lines,
        "compact_boundaries": compact_boundaries,
        "compact_summaries": compact_summaries,
    }


def compaction_stats(projects: Path, max_files: int = 500) -> dict[str, Any]:
    if not projects.exists():
        return {"exists": False, "files": 0, "lines": 0, "compact_boundaries": 0,
                "compact_summaries": 0, "orphaned_files": 0, "superseded_files": 0,
                "total_bytes": 0, "items": []}
    items: list[dict[str, Any]] = []
    totals = {"files": 0, "lines": 0, "compact_boundaries": 0,
              "compact_summaries": 0, "orphaned_files": 0, "superseded_files": 0,
              "total_bytes": 0}
    for path in sorted(projects.rglob("*.jsonl")):
        if len(items) >= max_files:
            break
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        info = _jsonl_compaction(path)
        name = path.name
        item = {
            "path": str(path),
            "size_bytes": size,
            **info,
            "orphaned": ".orphaned-" in name,
            "superseded": ".superseded-" in name,
        }
        items.append(item)
        totals["files"] += 1
        totals["lines"] += info["lines"]
        totals["compact_boundaries"] += info["compact_boundaries"]
        totals["compact_summaries"] += info["compact_summaries"]
        totals["total_bytes"] += size
        totals["orphaned_files"] += int(item["orphaned"])
        totals["superseded_files"] += int(item["superseded"])
    return {"exists": True, **totals, "items": items, "truncated": len(items) >= max_files}


def audit(home: Path | None = None, include_compaction: bool = False) -> dict[str, Any]:
    home = home or Path.home()
    rows: list[dict[str, Any]] = []
    for item in candidate_paths(home):
        path = Path(item["path"]).expanduser()
        stats = path_stats(path)
        rows.append({
            "category": item["category"],
            "path": str(path),
            "note": item["note"],
            "never_delete": item["category"] in NEVER_DELETE,
            **stats,
        })
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "home": str(home),
        "rows": rows,
        "warnings": [
            "This audit is read-only; it never deletes or moves files.",
            "Claude Code transcripts are plaintext JSONL and may contain prompts, tool output and secrets.",
            "Cleanup does not unban an account and does not prevent device association.",
            "Export data and preserve appeal evidence before deleting anything.",
            "Never delete keychain/credential stores; do not rotate device IDs as an evasion step.",
        ],
    }
    if include_compaction:
        report["compaction"] = compaction_stats(home / ".claude" / "projects")
    return report


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def print_summary(report: dict[str, Any]) -> None:
    print("Claude local data audit (read-only)")
    print(f"home: {report['home']}")
    print()
    for row in report["rows"]:
        if not row["exists"]:
            continue
        flag = " NEVER-DELETE" if row["never_delete"] else ""
        print(f"{row['category']:16} {human_size(row['size_bytes']):>10} "
              f"{row['files']:>7} files  {row['path']}{flag}")
    if "compaction" in report:
        comp = report["compaction"]
        print()
        print("Compaction stats (read-only)")
        if not comp.get("exists"):
            print("  no projects directory")
        else:
            print(f"  files={comp['files']} lines={comp['lines']} "
                  f"boundaries={comp['compact_boundaries']} summaries={comp['compact_summaries']} "
                  f"orphaned={comp['orphaned_files']} superseded={comp['superseded_files']}")
    print()
    for warning in report["warnings"]:
        print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of local Claude data")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", help="write JSON to this path")
    parser.add_argument("--home", help="override home directory (for testing)")
    parser.add_argument("--compaction-stats", action="store_true",
                        help="also count JSONL lines and compact markers (read-only)")
    args = parser.parse_args()

    report = audit(Path(args.home).expanduser() if args.home else None,
                   include_compaction=args.compaction_stats)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    if args.json:
        print(text)
    elif not args.output:
        print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
