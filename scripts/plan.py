#!/usr/bin/env python3
"""Generate a reviewable setup plan from a machine profile (no changes)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


OS_ALIASES = {
    "darwin": "macos",
    "mac": "macos",
    "macos": "macos",
    "windows": "windows",
    "win": "windows",
    "linux": "linux",
}


def detect_os(profile: dict[str, Any], override: str | None) -> str:
    if override:
        return OS_ALIASES.get(override.lower(), override.lower())
    raw = str(profile.get("host", {}).get("os", "")).lower()
    return OS_ALIASES.get(raw, raw or "unknown")


def fact(value: Any, unknown: str = "UNKNOWN") -> str:
    if value is None or value == "":
        return unknown
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def build_plan(profile: dict[str, Any], os_name: str, region: str | None) -> str:
    host = profile.get("host", {})
    loc = profile.get("locale", {})
    net = profile.get("network", {})
    claude = profile.get("claude", {})
    proxy = profile.get("proxy_env", {})
    browsers_found = [k for k, v in profile.get("browsers", {}).items() if v]
    clients_found = [k for k, v in profile.get("proxy_clients", {}).items() if v]

    lines: list[str] = []
    lines.append("# Claude Account Safety · 新机器设置计划")
    lines.append("")
    lines.append(f"- 目标系统：`{os_name}`")
    lines.append(f"- 机器：`{fact(host.get('os'))} {fact(host.get('os_release'))} {fact(host.get('arch'))}`")
    lines.append(f"- Python：`{fact(host.get('python'))}`")
    lines.append(f"- 时区/locale：`{fact(loc.get('timezone'))}` / `{fact(loc.get('locale'))}`")
    lines.append(f"- 地区声明：`{region or '未提供'}`（最终以 Anthropic 官方支持列表为准）")
    lines.append("")
    lines.append("## 0. 政策门禁")
    lines.append("")
    lines.append("- [ ] 打开 https://www.anthropic.com/legal/supported-regions 核对实际所在地")
    lines.append("- [ ] 不在支持地区 → 停止；不提供伪装/代过 KYC/成品号/中转方案")
    lines.append("- [ ] 在支持地区 → 继续；环境与真实所在地一致")
    lines.append("")
    lines.append("## 1. 已盘点事实")
    lines.append("")
    lines.append(f"- 代理环境变量：HTTP={fact(bool(proxy.get('HTTP_PROXY') or proxy.get('http_proxy')))} "
                 f"HTTPS={fact(bool(proxy.get('HTTPS_PROXY') or proxy.get('https_proxy')))} "
                 f"ALL={fact(bool(proxy.get('ALL_PROXY') or proxy.get('all_proxy')))}")
    lines.append(f"- DNS：{', '.join(net.get('dns_servers', [])[:4]) or 'UNKNOWN'}")
    lines.append(f"- IPv6：supported={fact(net.get('ipv6_supported'))} "
                 f"default_route={fact(net.get('ipv6_default_route'))}")
    lines.append(f"- Claude CLI：{fact(claude.get('cli_path'), 'NOT FOUND')} "
                 f"{fact(claude.get('cli_version'), '')}")
    lines.append(f"- ANTHROPIC_BASE_URL：{fact(claude.get('base_url_host'), 'not set')}")
    lines.append(f"- 浏览器：{', '.join(browsers_found) or 'none detected'}")
    lines.append(f"- 代理客户端：{', '.join(clients_found) or 'none detected'}")
    lines.append("")
    lines.append("## 2. A 档（只读，可直接做）")
    lines.append("")
    lines.append("- [ ] 运行 `python3 scripts/doctor.py --json --output machine-profile.json`")
    lines.append("- [ ] 运行 `python3 scripts/egress_check.py --json --output egress.json`")
    lines.append("- [ ] 在真实浏览器打开 trace / WebRTC / DNS 检查页")
    lines.append("- [ ] 记录当前时区、locale、代理变量、DNS、IPv6 状态")
    lines.append("- [ ] 确认账号是否本人、是否共享、支付是否合规")
    lines.append("")
    lines.append("## 3. B 档（可逆，先批准再执行）")
    lines.append("")
    lines.append("- [ ] 新建独立浏览器 profile / 指纹浏览器环境（不导入个人 Cookie）")
    lines.append("- [ ] 只保留一个代理客户端；关闭另一个客户端及其自启")
    lines.append("- [ ] 备份现有代理/Claude 配置（只备份路径和摘要，不复制凭据到公开目录）")
    lines.append("- [ ] 记录当前 `claude --version`，按官方方式升级")
    lines.append("- [ ] 如需多账号，创建独立 `CLAUDE_CONFIG_DIR`")
    lines.append("")
    lines.append("## 4. C 档（必须用户本人确认/操作）")
    lines.append("")
    lines.append("- [ ] 改系统时区/语言（只在真实所在地匹配时）")
    lines.append("- [ ] 开/关 TUN、系统代理、防火墙、IPv6")
    lines.append("- [ ] 切换出口节点/住宅代理")
    lines.append("- [ ] 登录 Claude、付款、KYC、2FA")
    lines.append("- [ ] 删除本地数据/退出登录/清理旧设备")
    lines.append("")
    lines.append("## 5. 本系统命令")
    lines.append("")
    if os_name == "macos":
        lines.extend([
            "```bash",
            "sw_vers",
            "systemsetup -gettimezone 2>/dev/null",
            "defaults read -g AppleLocale 2>/dev/null",
            "scutil --proxy",
            "scutil --dns | sed -n '1,40p'",
            "networksetup -getinfo Wi-Fi 2>/dev/null",
            "```",
        ])
    elif os_name == "windows":
        lines.extend([
            "```powershell",
            "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture",
            "tzutil /g",
            "Get-WinSystemLocale",
            "Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings'",
            "Get-DnsClientServerAddress",
            "Get-NetIPInterface -AddressFamily IPv6",
            "```",
        ])
    else:
        lines.extend([
            "```bash",
            "cat /etc/os-release",
            "timedatectl",
            "locale",
            "resolvectl status 2>/dev/null || cat /etc/resolv.conf",
            "ip -6 addr",
            "ip route",
            "```",
        ])
    lines.append("")
    lines.append("## 6. 验收")
    lines.append("")
    lines.append("- [ ] `verify.py` 无 `FAIL`，所有 `UNKNOWN` 都有原因")
    lines.append("- [ ] 出口 trace 的 `ip`/`loc` 一致")
    lines.append("- [ ] 浏览器 WebRTC/DNS 无泄漏")
    lines.append("- [ ] Claude Code 未指向第三方中转")
    lines.append("- [ ] 账号不共享、支付合规、2FA 开启")
    lines.append("- [ ] 生成 `setup-report.md`，写明已确认/未确认/下一步")
    lines.append("")
    lines.append("## 7. 回滚")
    lines.append("")
    lines.append("- 记录每项改动前的值（时区、DNS、代理开关、TUN、IPv6）。")
    lines.append("- 配置改动前做时间戳备份；不要把备份提交到公开仓库。")
    lines.append("- 失败时先恢复网络，再排查；不要连续换节点/换号。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Claude setup plan from machine-profile.json")
    parser.add_argument("--profile", required=True, help="machine-profile.json from doctor.py")
    parser.add_argument("--os", help="override: macos/windows/linux")
    parser.add_argument("--region", help="declared region, e.g. TW")
    parser.add_argument("--output", help="write Markdown to this path")
    args = parser.parse_args()

    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    os_name = detect_os(profile, args.os)
    plan = build_plan(profile, os_name, args.region)
    if args.output:
        Path(args.output).write_text(plan, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(plan, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
