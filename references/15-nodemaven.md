# 15 NodeMaven 美国静态 ISP（推荐候选）

这份说明只写公开购买/配置信息，不含任何人的账号、密码、订阅 URL 或具体出口 IP。

## 为什么推荐

截至 2026-11-10，在“Claude + 美国静态 IP + 不绕 VPS”这个组合里，NodeMaven 是比较合适的一个候选：

- 官方有 Claude proxy 页面：https://nodemaven.com/websites/claude-proxy/
- 静态 ISP 按 IP 计费、无限流量，不按 GB 烧流量。
- 官方网关：`gate.nodemaven.com:8080`；静态 ISP 订单会在 dashboard 给出独立 host/port。
- 支持 HTTP(S) 和 SOCKS5；Claude/Claude Code 用 HTTP 就够。
- 不需要 ProxyEmpire，也不需要额外 VPS（前提是商家没有额外要求住宅源 IP；买前确认）。

对比注意：

- ProxyEmpire 面板明确屏蔽 Claude/ChatGPT（所有类型，含 ISP），不要用它跑 Claude。
- MarsProxies 美国 ISP 可能售罄；超住宅是 rotating。
- IPRoyal 的“机房/数据中心”产品不是真住宅；要买它的静态住宅/ISP 产品。

## Protocol

优先 **HTTP**：

- Clash: `type: http`
- `udp: false`
- Claude/Claude Code 走 HTTPS CONNECT，HTTP 代理足够。

SOCKS5 适合需要 UDP/DNS over SOCKS 的场景；Claude 不需要。新订单如果可选，选 HTTP 兼容性最好。

## 购买/续费

1. 打开 `https://dashboard.nodemaven.com/isp-proxies`
2. `Buy new`：选美国、静态 ISP、30 天、HTTP。
3. 注意最小 IP 数量/单价会变；以 dashboard 当前价格为准。
4. 如果已有 Active 订单：用 `Order details` → `Extend` 续期，不要重复买新订单。
5. IP 被标记/不可用时，先用订单里的 `Swap IPs`（如果有免费次数）。
6. 付款/KYC 由使用者本人完成；本项目不代付、不代登录。

## 配置与验收

Clash 最小结构：

```yaml
proxies:
  - name: NODEMAVEN-US
    type: http
    server: <dashboard 给出的 host>
    port: <dashboard 给出的 port>
    username: <USER>
    password: <PASS>
    udp: false

proxy-groups:
  - name: CLAUDE
    type: select
    proxies: [NODEMAVEN-US, DIRECT]
```

Claude 域名规则指向 `CLAUDE`，其余 `MATCH,DIRECT`。

验收：

```bash
curl -x http://<host>:<port> --proxy-user 'USER:PASS' https://claude.ai/cdn-cgi/trace
curl -x http://<host>:<port> --proxy-user 'USER:PASS' https://www.cloudflare.com/cdn-cgi/trace
```

期望两个 `ip` 一致、`loc=US`，再用 whois/ASN 确认不是明显机房段。

## 安全与边界

- 不要把填好的 YAML、用户名/密码、订阅 URL 提交到 Git/公开仓库。
- 只在 Anthropic 支持地区使用；买美国 IP 不会让不支持地区变合规。
- 不承诺“不封”；NodeMaven 只是当前测试通过的候选。
- 价格、库存、协议、是否允许 Claude 以官方页面为准；本文没有 affiliate 链接。
