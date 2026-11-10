# 03 网络出口、DNS、WebRTC、IPv6

## 目标

让目标机器的公网出口**单一、稳定、可解释**，并让 DNS/WebRTC/IPv6 不绕过这条出口。

这不是“越隐蔽越好”。一个昨天在东京、今天在洛杉矶、明天又换机房的账号，在任何风控系统里都不像正常用户。稳定性和一致性通常比“IP 分数”更重要，但这是经验判断，不是官方规则。

## 三种接管层

| 层 | 覆盖谁 | 常见问题 |
|---|---|---|
| 环境变量 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` | 守规矩的 CLI | Go/Rust/部分 SDK 不读 |
| 系统代理 | 守规矩的 GUI/浏览器 | 不认系统代理的应用、UDP 绕过 |
| TUN 虚拟网卡 | IP 层兜底 | 需要 root/服务；双客户端会打架 |

优先保证“目标应用实际走同一条路”，而不是只看某个开关。

## 推荐基线

1. 只保留一个代理客户端在跑（Clash Verge Rev / Mihomo / FlClash / sing-box 之一）。
2. 默认 `rule` 模式；`global` 只做临时诊断，用完切回。
3. TUN 可选；如果开 TUN，确认没有第二个客户端同时开 TUN。
4. 目标域名走固定出口：
   - `claude.ai`
   - `claude.com`
   - `anthropic.com`
   - `claudeusercontent.com`
   - `statsig.com`（Claude 相关）
5. 禁用 QUIC/UDP 443 作为兜底，避免浏览器 QUIC 粘滞旧出口。
6. DNS 走代理/加密上游；不要让系统 DNS 泄漏到本地 ISP。
7. 除非确有需要，关闭目标机器的 IPv6 默认路由；IPv6 很容易绕过 IPv4 代理规则。

这些是“减少泄漏”的工程基线，不是官方免封配方。

## 验收端点

在目标机器上，用**同一个浏览器/终端**访问：

- `https://claude.ai/cdn-cgi/trace`
- `https://www.cloudflare.com/cdn-cgi/trace`
- `https://ippure.com/claude.html`（第三方检测页）
- `https://browserleaks.com/webrtc`
- `https://dnsleaktest.com/`

看：

- `ip=` 是否一致。
- `loc=` 是否一致。
- `colo=` 是否合理。
- WebRTC 是否暴露本地/中国大陆 IP。
- DNS 解析器是否在代理出口附近。

自动化脚本只比较前两个 trace 的 `ip`/`loc`；浏览器项必须人工看。

## 分流出问题怎么查

按顺序：

1. **谁在跑**：是否两个代理客户端同时接管。
2. **实际出口**：`curl` 走代理 vs 不走代理，分别看 trace。
3. **DNS**：`scutil --dns` / `resolvectl` 看解析器；浏览器再做 DNS leak test。
4. **IPv6**：`networksetup -getinfo Wi-Fi` / `ip -6 addr` / `Get-NetIPInterface`。
5. **规则**：Clash/Mihomo 的控制面 `/rules`、`/proxies` 看目标域名命中了哪条。
6. **应用**：Claude Code 是否设了 `ANTHROPIC_BASE_URL`；浏览器是否用了另一个 profile/扩展。

一次只改一个变量，否则无法归因。

## Clash 片段模板

`templates/clash-snippet.yaml` 只有占位符，不含凭据。使用时替换 `CLAUDE_EXIT` 为你自己的策略组/节点名，不要把真实订阅 URL、UUID、密码提交到仓库。

## 不要做

- 不要把公共机场节点当成“稳定住宅出口”；共享出口的账号连坐风险更高。
- 不要今天美国、明天日本地切换登录。
- 不要在登录/付款时换出口。
- 不要把节点名里的“住宅”“原生”“纯净”当成事实；用 trace 和第三方检测核验，但仍不能证明 Anthropic 认可。
- 不要为了“看起来像美国”而改系统时区/语言，除非那确实是你真实所在地；否则这是伪装，违反政策边界。
