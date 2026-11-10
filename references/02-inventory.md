# 02 只读体检与证据口径

## 目标

在不改系统、不碰凭据的前提下，回答：

- 这台机器是什么环境？
- Claude Code / 浏览器 / 代理客户端是否就位？
- 时区、locale、代理变量、DNS、IPv6 是否一致？
- 哪些项能自动查，哪些必须人工确认？

## 命令

```bash
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json
```

`--summary` 给人看；`--json` 给后续 `plan.py` / `verify.py` 用。

## 采集项

| 类别 | 字段 | 说明 |
|---|---|---|
| Host | os / os_version / arch / python | 平台与运行时 |
| Locale | timezone / utc_offset / locale / lang_env | 时区、语言、环境变量 |
| Proxy | http_proxy_set / https_proxy_set / all_proxy_set / no_proxy_count | 只记录是否设置，不输出完整值 |
| System proxy | http / https / socks 端点 | 只记录 host:port，不输出凭据 |
| Network | ipv6_supported / dns_servers / default_route | 只读系统状态 |
| Claude | cli_found / cli_path / cli_version / config_dir_exists / desktop_found | 不读配置内容 |
| Browser | chrome / edge / firefox / safari | 是否存在 |
| Proxy client | clash / mihomo / clash_verge / flclash | 是否存在/可执行 |

## 不采集

- 密码、token、API key、Cookie、Keychain。
- 订阅 URL、节点 UUID、完整代理 URL、完整配置全文。
- 聊天记录、项目源码、浏览器历史。

代理变量只输出 `set: true/false`；如果必须显示 host，使用 `host:port` 并去掉 userinfo/path/query。

## 跨平台只读命令

### macOS

```bash
sw_vers
uname -m
systemsetup -gettimezone 2>/dev/null
defaults read -g AppleLocale 2>/dev/null
scutil --proxy
scutil --dns | sed -n '1,40p'
networksetup -getinfo Wi-Fi 2>/dev/null
```

### Windows PowerShell

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture
tzutil /g
Get-WinSystemLocale
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
Get-DnsClientServerAddress
Get-NetIPInterface -AddressFamily IPv6
```

### Linux

```bash
cat /etc/os-release
uname -m
timedatectl
locale
resolvectl status 2>/dev/null || cat /etc/resolv.conf
ip -6 addr
ip route
```

## 结果怎么读

- `cli_found: false`：Claude Code 未安装，或不在 PATH。先确认路径，不要直接重装。
- `config_dir_exists: false`：可能从未登录，或使用了自定义 `CLAUDE_CONFIG_DIR`。先问，不要创建。
- `http_proxy_set: true` 但 `https_proxy_set: false`：可能只代理 HTTP，Claude Code 仍可能直连；需要进一步查。
- 环境变量代理与系统代理的 host:port 不一致：说明两层没有接同一条路，浏览器/CLI 可能分流；`verify.py` 会标 `FAIL`。
- `ipv6_supported: true`：不代表一定泄漏；要看是否有 IPv6 默认路由、浏览器是否走 IPv6。
- `dns_servers` 含本地 ISP DNS：在 TUN/代理场景下可能是泄漏信号，也可能只是未接管；要结合 `scutil --dns` / `resolvectl` 和浏览器测试判断。
- `cli_version` 很低：先按官方方式升级，不要从第三方脚本装“防封版”。

## 证据保存

`machine-profile.json` 可以提交到私有仓库，但先检查：

- 没有完整代理 URL。
- 没有用户名/密码。
- 没有内部 IP/主机名（如果敏感）。
- 没有 `ANTHROPIC_API_KEY` 等环境变量值。

报告默认写到当前目录；路径由用户指定。
