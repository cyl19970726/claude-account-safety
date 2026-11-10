# 09 新机器配置步骤

## 通用前置

1. 确认实际所在地区在 Anthropic 支持列表内。
2. 准备 Python 3.10+：
   - macOS：`python3 --version`；低于 3.10 时用 python.org 安装包或 `brew install python@3.12`。
   - Windows：python.org 安装包或 Microsoft Store；用 `py -3 --version` 验证。
   - Linux：发行版的 `python3` 包；用 `python3 --version` 验证。
3. Claude Code 走官方安装页面：https://code.claude.com/docs/en/setup
4. 准备自己的代理出口（已有 VPS/住宅代理/家庭宽带），不要从 Skill 里买。
5. 准备官方 Claude 账号和官方支付方式。
6. 准备密码管理器（1Password/Bitwarden/Keychain）存放采购链接和订阅 URL。
7. 不要把旧机器的 `clash/profile.yaml`、订阅 URL、token 直接拷到新机器；先确认是否需要重新授权。

Agent 不应自动安装系统软件。缺 Python/Claude Code/代理客户端时，先给官方安装步骤，等用户执行完再继续。

## macOS

### 1. 安装 Skill

```bash
./install.sh --target "$HOME/.agents/skills"
```

### 2. 只读体检

```bash
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json
```

### 3. 系统基线

- 系统设置 → 通用 → 日期与时间：自动设置；时区与真实所在地一致。
- 语言与地区：与真实所在地一致；不要为了“像美国”而改。
- 检查 `scutil --proxy`、`scutil --dns`、`networksetup -getinfo Wi-Fi`。

### 4. 网络

- 安装/打开 Clash Verge Rev 或现有客户端。
- 只保留一个客户端；TUN 可选，rule 模式。
- 目标域名走固定出口；DNS 走代理；关闭不必要的 IPv6。
- 用 `egress_check.py` 和浏览器 trace 验证。

### 5. 浏览器

- 新建独立 profile 或指纹浏览器环境。
- WebRTC 禁用/替换；DNS 泄漏测试；不导入日常 Cookie。
- 登录前先跑 browserleaks/dnsleaktest。

### 6. Claude Code

```bash
claude --version
claude auth login
```

- 不设置第三方 `ANTHROPIC_BASE_URL`。
- 多账号用独立 `CLAUDE_CONFIG_DIR`。

### 7. 验收

```bash
python3 scripts/egress_check.py --json --output egress.json
python3 scripts/verify.py --profile machine-profile.json --egress egress.json --region TW
```

## Windows

### 1. 安装 Skill

```powershell
.\install.ps1 -Target "$HOME\.agents\skills"
```

### 2. 只读体检

```powershell
python scripts\doctor.py --summary
python scripts\doctor.py --json --output machine-profile.json
```

### 3. 系统基线

- 设置 → 时间和语言：自动时间；时区与真实所在地一致。
- 语言/地区与真实所在地一致。
- `Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'`
- `Get-DnsClientServerAddress`
- `Get-NetIPInterface -AddressFamily IPv6`

### 4. 网络

- 只保留一个代理客户端。
- TUN/系统代理二选一或按客户端文档组合。
- 检查 Windows 防火墙没有把目标应用放行到直连。
- 用 `egress_check.py` 和浏览器 trace 验证。

### 5. 浏览器

- 新建 Edge/Chrome profile，或独立指纹浏览器环境。
- 关闭 WebRTC（设置/扩展/策略），检查 DNS 泄漏。
- 不导入日常 Cookie。

### 6. Claude Code

```powershell
claude --version
claude auth login
```

- 不设置第三方 `ANTHROPIC_BASE_URL`。
- 多账号用独立 `CLAUDE_CONFIG_DIR`。

### 7. 验收

```powershell
python scripts\egress_check.py --json --output egress.json
python scripts\verify.py --profile machine-profile.json --egress egress.json --region TW
```

## Linux

### 1. 安装 Skill

```bash
./install.sh --target "$HOME/.agents/skills"
```

### 2. 只读体检

```bash
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json
```

### 3. 系统基线

```bash
timedatectl
locale
resolvectl status
ip -6 addr
ip route
```

- 时区/locale 与真实所在地一致。
- DNS 走代理/加密解析；检查 `/etc/resolv.conf` 是否被覆盖。
- IPv6 无意外默认路由。

### 4. 网络

- 只保留一个代理客户端（Mihomo/sing-box/Clash）。
- TUN 可选；确认 nftables/iptables 没有绕过规则。
- 用 `egress_check.py` 和浏览器 trace 验证。

### 5. 浏览器

- 独立 profile；WebRTC 关闭；DNS 泄漏测试。
- 服务器无 GUI 时，浏览器检查在本地机器做，不要用 curl 代替。

### 6. Claude Code

```bash
claude --version
claude auth login
```

### 7. 验收

```bash
python3 scripts/egress_check.py --json --output egress.json
python3 scripts/verify.py --profile machine-profile.json --egress egress.json --region TW
```

## 新机器检查清单

- [ ] 地区在支持列表内（截图/日期）
- [ ] Python 3.10+
- [ ] Claude Code 官方安装
- [ ] 无第三方 `ANTHROPIC_BASE_URL`
- [ ] 多账号配置目录隔离
- [ ] 单一代理客户端
- [ ] 目标域名固定出口
- [ ] DNS 不泄漏
- [ ] WebRTC 不泄漏
- [ ] IPv6 不绕过
- [ ] 时区/locale 与真实所在地一致
- [ ] 账号不共享、支付合规、2FA 开启
- [ ] `machine-profile.json` / `setup-report.md` 已保存
