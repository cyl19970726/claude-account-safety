#!/usr/bin/env python3
"""Run packaging, unit-test, inventory and secret checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(label: str, cmd: list[str], cwd: Path = ROOT) -> bool:
    print(f"\n== {label} ==")
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, text=True, check=False)
    ok = proc.returncode == 0
    print("OK" if ok else f"FAILED (exit {proc.returncode})")
    return ok


def main() -> int:
    required = [
        "SKILL.md",
        "README.md",
        "SHARE.md",
        "install.sh",
        "install.ps1",
        "package.sh",
        "references/01-policy-and-boundaries.md",
        "references/09-new-machine.md",
        "references/11-egress-options.md",
        "references/12-secrets.md",
        "references/13-local-cleanup.md",
        "references/14-claude-code-local-data.md",
        "references/15-nodemaven.md",
        "scripts/doctor.py",
        "scripts/egress_check.py",
        "scripts/plan.py",
        "scripts/verify.py",
        "scripts/secret_check.py",
        "scripts/secret_ref.py",
        "scripts/cleanup_audit.py",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    print("== package files ==")
    if missing:
        print("missing:", ", ".join(missing))
        return 1
    print(f"OK ({len(required)} required files)")

    ok = True
    ok &= run("unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    ok &= run("doctor summary", [sys.executable, "scripts/doctor.py", "--summary"])
    ok &= run("secret scan", [sys.executable, "scripts/secret_check.py", "--root", str(ROOT)])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
