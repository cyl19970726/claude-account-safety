#!/usr/bin/env python3
"""Resolve a secret reference without printing the secret.

Supported references:
  op://vault/item/field
  keychain://service/account
  env:NAME
  env://NAME
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


class SecretError(RuntimeError):
    pass


def resolve(ref: str) -> str:
    if ref.startswith("op://"):
        if not shutil.which("op"):
            raise SecretError("1Password CLI 'op' not found")
        proc = subprocess.run(
            ["op", "read", ref],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise SecretError(f"op read failed: {proc.stderr.strip()[:200]}")
        return proc.stdout.rstrip("\n")

    if ref.startswith("keychain://"):
        if platform.system() != "Darwin":
            raise SecretError("keychain:// is only supported on macOS")
        parts = urlsplit(ref)
        service = parts.netloc
        account = parts.path.lstrip("/") or os.environ.get("USER", "")
        if not service:
            raise SecretError("keychain reference must include a service")
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise SecretError(f"keychain lookup failed for service={service!r}")
        return proc.stdout.rstrip("\n")

    if ref.startswith("env:") or ref.startswith("env://"):
        name = ref.split("://", 1)[1] if ref.startswith("env://") else ref.split(":", 1)[1]
        value = os.environ.get(name)
        if value is None:
            raise SecretError(f"environment variable not set: {name}")
        return value

    raise SecretError("unsupported reference; use op://, keychain://, env: or env://")


def copy_to_clipboard(value: str) -> None:
    system = platform.system()
    if system == "Darwin":
        cmd = ["pbcopy"]
    elif system == "Windows":
        cmd = ["clip"]
    else:
        if shutil.which("wl-copy"):
            cmd = ["wl-copy"]
        elif shutil.which("xclip"):
            cmd = ["xclip", "-selection", "clipboard"]
        else:
            raise SecretError("no clipboard tool found (wl-copy/xclip)")
    proc = subprocess.run(cmd, input=value, text=True, check=False)
    if proc.returncode != 0:
        raise SecretError("clipboard copy failed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a secret reference without printing it")
    parser.add_argument("ref", help="op:// / keychain:// / env: reference")
    parser.add_argument("--check", action="store_true", help="only verify the reference resolves")
    parser.add_argument("--copy", action="store_true", help="copy to clipboard without printing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        value = resolve(args.ref)
    except (SecretError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        payload = {"ref": args.ref, "resolved": True, "length": len(value)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"resolved ref={args.ref} length={len(value)}")
        return 0

    if args.copy:
        try:
            copy_to_clipboard(value)
        except (SecretError, OSError, subprocess.SubprocessError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"copied to clipboard ref={args.ref} length={len(value)}")
        return 0

    print("refusing to print secret; use --check or --copy", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
