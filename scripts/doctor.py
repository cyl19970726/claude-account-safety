#!/usr/bin/env python3
"""Read-only Claude environment inventory.

Collects host, locale, proxy, network, Claude Code, browser and proxy-client
facts without reading credentials, cookies, chat history or subscription URLs.
"""

from __future__ import annotations

import argparse
import json
import locale as locale_mod
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = 1
MIN_PYTHON = (3, 10)


def run(cmd: list[str], timeout: int = 5) -> str | None:
    """Run a read-only command and return stdout, or None on failure."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def host_info() -> dict[str, Any]:
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "python_ok": sys.version_info >= MIN_PYTHON,
        "hostname_present": bool(socket.gethostname()),
    }


def _tz_from_localtime() -> str | None:
    try:
        target = Path("/etc/localtime").resolve()
        parts = target.parts
        if "zoneinfo" in parts:
            idx = parts.index("zoneinfo")
            return "/".join(parts[idx + 1 :])
    except (OSError, ValueError):
        return None
    return None


def timezone_name() -> str | None:
    tz = os.environ.get("TZ")
    if tz:
        return tz
    if platform.system() == "Darwin":
        out = run(["systemsetup", "-gettimezone"])
        if out and ":" in out:
            return out.split(":", 1)[1].strip()
    if platform.system() == "Linux":
        out = run(["timedatectl", "show", "-p", "Timezone", "--value"])
        if out:
            return out.strip()
    if platform.system() == "Windows":
        out = run(["tzutil", "/g"])
        if out:
            return out.strip()
    return _tz_from_localtime()


def locale_info() -> dict[str, Any]:
    now = datetime.now().astimezone()
    offset = now.utcoffset()
    offset_text = None
    if offset is not None:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        offset_text = f"{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    try:
        lang, encoding = locale_mod.getlocale()
    except ValueError:
        lang, encoding = None, None
    if not lang:
        if platform.system() == "Darwin":
            lang = run(["defaults", "read", "-g", "AppleLocale"])
        elif platform.system() == "Windows":
            lang = run(["powershell", "-NoProfile", "-Command", "Get-Culture | Select-Object -ExpandProperty Name"])
        else:
            env_locale = os.environ.get("LC_ALL") or os.environ.get("LANG")
            if env_locale:
                lang = env_locale.split(".", 1)[0]
    return {
        "timezone": timezone_name(),
        "utc_offset": offset_text,
        "locale": lang,
        "locale_encoding": encoding,
        "lang_env": os.environ.get("LANG"),
        "lc_all": os.environ.get("LC_ALL"),
    }


def _scrub_proxy(value: str) -> str:
    """Return host:port only; never userinfo, path, query or fragment."""
    raw = value.strip()
    if "://" not in raw:
        raw = "http://" + raw
    try:
        parts = urlsplit(raw)
    except ValueError:
        return "[set]"
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    scheme = parts.scheme or "http"
    return urlunsplit((scheme, host + port, "", "", ""))


def proxy_env() -> dict[str, Any]:
    names = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
             "http_proxy", "https_proxy", "all_proxy", "no_proxy"]
    out: dict[str, Any] = {}
    for name in names:
        value = os.environ.get(name)
        if name.lower().endswith("_proxy"):
            out[name] = bool(value)
            if value and name.upper() != "NO_PROXY":
                out[name + "_value"] = _scrub_proxy(value)
        else:
            out[name] = bool(value)
    return out


def _parse_scutil_proxy(text: str) -> dict[str, Any]:
    def enabled(key: str) -> bool:
        match = re.search(rf"{re.escape(key)}\s*:\s*(\d)", text)
        return bool(match and match.group(1) == "1")

    def endpoint(prefix: str) -> str | None:
        host = re.search(rf"{prefix}Proxy\s*:\s*(\S+)", text)
        port = re.search(rf"{prefix}Port\s*:\s*(\d+)", text)
        if host and port:
            return f"{host.group(1)}:{port.group(1)}"
        return None

    return {
        "http_enabled": enabled("HTTPEnable"),
        "https_enabled": enabled("HTTPSEnable"),
        "socks_enabled": enabled("SOCKSEnable"),
        "http": endpoint("HTTP"),
        "https": endpoint("HTTPS"),
        "socks": endpoint("SOCKS"),
    }


def system_proxy() -> dict[str, Any]:
    system = platform.system()
    if system == "Darwin":
        out = run(["scutil", "--proxy"])
        return _parse_scutil_proxy(out) if out else {"known": False}
    if system == "Windows":
        out = run(["reg", "query",
                   r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"])
        if not out:
            return {"known": False}
        enabled = re.search(r"ProxyEnable\s+REG_DWORD\s+0x(\d+)", out)
        server = re.search(r"ProxyServer\s+REG_SZ\s+(.+)", out)
        return {
            "known": True,
            "http_enabled": bool(enabled and int(enabled.group(1), 16) == 1),
            "server": server.group(1).strip() if server else None,
        }
    return {"known": False}


def _dns_macos() -> list[str]:
    out = run(["scutil", "--dns"])
    if not out:
        return []
    servers = re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", out)
    return sorted(set(servers))


def _dns_linux() -> list[str]:
    servers: list[str] = []
    try:
        for line in Path("/etc/resolv.conf").read_text(errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("nameserver "):
                servers.append(line.split(None, 1)[1].strip())
    except OSError:
        return []
    return sorted(set(servers))


def _dns_windows() -> list[str]:
    out = run(["ipconfig", "/all"])
    if not out:
        return []
    servers: list[str] = []
    for line in out.splitlines():
        if "DNS Servers" in line and ":" in line:
            candidate = line.split(":", 1)[1].strip()
            if candidate:
                servers.append(candidate)
        elif servers and re.match(r"^\s+\d{1,3}(?:\.\d{1,3}){3}\s*$", line):
            servers.append(line.strip())
    return sorted(set(servers))


def dns_servers() -> list[str]:
    system = platform.system()
    if system == "Darwin":
        return _dns_macos()
    if system == "Windows":
        return _dns_windows()
    return _dns_linux()


def default_route() -> str | None:
    system = platform.system()
    if system == "Darwin":
        out = run(["route", "-n", "get", "default"])
        if not out:
            return None
        match = re.search(r"interface:\s*(\S+)", out)
        return match.group(1) if match else None
    if system == "Linux":
        out = run(["ip", "route", "show", "default"])
        if out:
            return out.splitlines()[0].strip()
    if system == "Windows":
        out = run(["route", "print", "0.0.0.0"])
        if out:
            return "default route present"
    return None


def ipv6_default() -> bool | None:
    system = platform.system()
    if system == "Darwin":
        out = run(["netstat", "-rn", "-f", "inet6"])
        return bool(out and re.search(r"^default\s", out, re.MULTILINE))
    if system == "Linux":
        out = run(["ip", "-6", "route", "show", "default"])
        return bool(out and out.strip())
    if system == "Windows":
        out = run(["route", "print", "-6"])
        return bool(out and "::/0" in out)
    return None


def _safe_host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parts = urlsplit(url if "://" in url else "https://" + url)
    except ValueError:
        return None
    return parts.hostname


def claude_info() -> dict[str, Any]:
    cli = shutil.which("claude")
    version = run([cli, "--version"], timeout=8) if cli else None
    home = Path.home()
    config_candidates = [
        home / ".claude",
        home / ".claude.json",
        home / ".config" / "claude",
        home / ".claude-accounts",
    ]
    env_config = os.environ.get("CLAUDE_CONFIG_DIR")
    if env_config:
        config_candidates.append(Path(env_config).expanduser())
    config_exists = {str(path): path.exists() for path in config_candidates}
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    telemetry = {
        name: bool(os.environ.get(name))
        for name in (
            "DISABLE_TELEMETRY",
            "DO_NOT_TRACK",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
        )
    }
    desktop = False
    system = platform.system()
    if system == "Darwin":
        desktop = Path("/Applications/Claude.app").exists()
    elif system == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        desktop = (local / "AnthropicClaude").exists() or (local / "Programs" / "Claude").exists()
    else:
        desktop = (home / ".config" / "Claude").exists()
    return {
        "cli_found": bool(cli),
        "cli_path": cli,
        "cli_version": version,
        "config_dir_exists": config_exists,
        "config_dir_env": env_config,
        "desktop_found": desktop,
        "base_url_set": bool(base_url),
        "base_url_host": _safe_host(base_url),
        "telemetry_env": telemetry,
    }


def browsers() -> dict[str, bool]:
    system = platform.system()
    if system == "Darwin":
        paths = {
            "chrome": Path("/Applications/Google Chrome.app"),
            "edge": Path("/Applications/Microsoft Edge.app"),
            "firefox": Path("/Applications/Firefox.app"),
            "safari": Path("/Applications/Safari.app"),
            "arc": Path("/Applications/Arc.app"),
        }
        return {name: path.exists() for name, path in paths.items()}
    if system == "Windows":
        base = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        base86 = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        return {
            "chrome": (base / "Google" / "Chrome" / "Application" / "chrome.exe").exists()
            or (base86 / "Google" / "Chrome" / "Application" / "chrome.exe").exists(),
            "edge": (base86 / "Microsoft" / "Edge" / "Application" / "msedge.exe").exists()
            or (base / "Microsoft" / "Edge" / "Application" / "msedge.exe").exists(),
            "firefox": (base / "Mozilla Firefox" / "firefox.exe").exists(),
        }
    return {
        "chrome": bool(shutil.which("google-chrome") or shutil.which("chromium")),
        "edge": bool(shutil.which("microsoft-edge")),
        "firefox": bool(shutil.which("firefox")),
    }


def proxy_clients() -> dict[str, bool]:
    names = ["clash", "mihomo", "clash-verge", "verge-mihomo", "flclash", "sing-box"]
    found = {name: bool(shutil.which(name)) for name in names}
    system = platform.system()
    if system == "Darwin":
        found["clash_verge_app"] = Path("/Applications/Clash Verge.app").exists()
        found["clashx_app"] = Path("/Applications/ClashX.app").exists()
    elif system == "Windows":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        found["clash_verge_app"] = (local / "Programs" / "Clash Verge").exists()
    return found


def build_checks(profile: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(check_id: str, status: str, detail: str) -> None:
        checks.append({"id": check_id, "status": status, "detail": detail})

    host = profile["host"]
    add(
        "host.python",
        "PASS" if host.get("python_ok") else "FAIL",
        f"Python {host.get('python')} (need >= 3.10)",
    )

    claude = profile["claude"]
    add(
        "claude.cli",
        "PASS" if claude.get("cli_found") else "UNKNOWN",
        claude.get("cli_path") or "claude not found in PATH",
    )
    if claude.get("base_url_set"):
        host_name = claude.get("base_url_host")
        status = "PASS" if host_name == "api.anthropic.com" else "FAIL"
        add("claude.base_url", status, f"ANTHROPIC_BASE_URL host={host_name!r}")
    else:
        add("claude.base_url", "PASS", "ANTHROPIC_BASE_URL not set")

    proxy = profile["proxy_env"]
    http_set = bool(proxy.get("HTTP_PROXY") or proxy.get("http_proxy"))
    https_set = bool(proxy.get("HTTPS_PROXY") or proxy.get("https_proxy"))
    if http_set == https_set:
        add("proxy.env", "PASS", f"HTTP={http_set} HTTPS={https_set}")
    else:
        add("proxy.env", "UNKNOWN", f"partial proxy env: HTTP={http_set} HTTPS={https_set}")

    ipv6 = profile["network"].get("ipv6_default_route")
    if ipv6 is True:
        add("network.ipv6", "UNKNOWN", "IPv6 default route present; verify it does not bypass proxy")
    elif ipv6 is False:
        add("network.ipv6", "PASS", "no IPv6 default route detected")
    else:
        add("network.ipv6", "UNKNOWN", "could not determine IPv6 default route")

    dns = profile["network"].get("dns_servers") or []
    add("network.dns", "PASS" if dns else "UNKNOWN",
        f"{len(dns)} DNS server(s) detected" if dns else "DNS servers not detected")

    if any(profile["browsers"].values()):
        add("browser.present", "PASS", "at least one supported browser found")
    else:
        add("browser.present", "UNKNOWN", "no supported browser found")

    return checks


def build_profile() -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": host_info(),
        "locale": locale_info(),
        "proxy_env": proxy_env(),
        "system_proxy": system_proxy(),
        "network": {
            "ipv6_supported": socket.has_ipv6,
            "ipv6_default_route": ipv6_default(),
            "dns_servers": dns_servers(),
            "default_route": default_route(),
        },
        "claude": claude_info(),
        "browsers": browsers(),
        "proxy_clients": proxy_clients(),
    }
    profile["checks"] = build_checks(profile)
    return profile


def summarize(profile: dict[str, Any]) -> str:
    host = profile["host"]
    loc = profile["locale"]
    net = profile["network"]
    claude = profile["claude"]
    proxy = profile["proxy_env"]
    counts: dict[str, int] = {}
    for check in profile["checks"]:
        counts[check["status"]] = counts.get(check["status"], 0) + 1
    lines = [
        "Claude Account Safety · 只读体检",
        f"Host: {host['os']} {host['os_release']} {host['arch']} / Python {host['python']}",
        f"Timezone: {loc['timezone'] or 'UNKNOWN'} ({loc['utc_offset'] or '?'}) / locale: {loc['locale'] or 'UNKNOWN'}",
        f"Proxy env: HTTP={bool(proxy.get('HTTP_PROXY') or proxy.get('http_proxy'))} "
        f"HTTPS={bool(proxy.get('HTTPS_PROXY') or proxy.get('https_proxy'))} "
        f"ALL={bool(proxy.get('ALL_PROXY') or proxy.get('all_proxy'))}",
        f"DNS: {', '.join(net['dns_servers'][:4]) or 'UNKNOWN'}",
        f"IPv6: supported={net['ipv6_supported']} default_route={net['ipv6_default_route']}",
        f"Claude CLI: {claude['cli_path'] or 'NOT FOUND'} {claude['cli_version'] or ''}".rstrip(),
        f"Claude Desktop: {'found' if claude.get('desktop_found') else 'not found'}",
        f"ANTHROPIC_BASE_URL: {claude['base_url_host'] or 'not set'}",
        f"Browsers: {', '.join(k for k, v in profile['browsers'].items() if v) or 'none detected'}",
        f"Proxy clients: {', '.join(k for k, v in profile['proxy_clients'].items() if v) or 'none detected'}",
        f"Checks: {counts.get('PASS', 0)} PASS, {counts.get('FAIL', 0)} FAIL, "
        f"{counts.get('UNKNOWN', 0)} UNKNOWN",
        "",
        "Next: read references/09-new-machine.md, then run plan.py.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Claude environment inventory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--summary", action="store_true", help="emit a short human summary")
    parser.add_argument("--output", help="write JSON to this path")
    args = parser.parse_args()

    profile = build_profile()
    text = json.dumps(profile, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    if args.json:
        print(text)
    elif not args.output:
        print(summarize(profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
