# 07 验收矩阵

## 状态定义

- `PASS`：有可复现证据，符合预期。
- `FAIL`：有可复现证据，不符合预期。
- `UNKNOWN`：没查、查不到、权限不足，或工具不支持。
- `N/A`：不适用，必须写原因。

不允许把“应该没问题”“教程说可以”“节点名写着住宅”写成 `PASS`。

## 矩阵

| # | 检查 | 怎么查 | PASS 标准 | 证据 |
|---|---|---|---|---|
| 1 | 地区资格 | 用户确认 + 官方支持列表 | 实际所在地在列表内 | 页面截图/日期 |
| 2 | 账号归属 | 用户确认 | 本人账号，不共享/不拼车 | 人工确认 |
| 3 | 支付合规 | 用户确认 | 本人/授权支付，账单真实 | 人工确认（不存卡号） |
| 4 | Claude Code 来源 | `which claude` / `claude --version` | 官方安装，版本可读 | 命令输出 |
| 5 | 官方端点 | 检查 `ANTHROPIC_BASE_URL` | 未指向第三方中转 | 环境变量（脱敏） |
| 6 | 配置隔离 | 检查 `CLAUDE_CONFIG_DIR` | 多账号各自独立 | 路径列表 |
| 7 | 出口一致 | `egress_check.py` | claude.ai 与 cloudflare trace 的 ip/loc 一致 | JSON |
| 7b | 代理层一致 | 对比 env 与系统代理 | host:port 一致 | `machine-profile.json` |
| 8 | DNS | 系统命令 + dnsleaktest | 解析器不在本地 ISP | 截图/命令输出 |
| 9 | WebRTC | browserleaks | 无真实公网 IP | 截图 |
| 10 | IPv6 | 系统命令 | 无意外 IPv6 默认路由 | 命令输出 |
| 11 | QUIC/UDP | 代理规则/浏览器 | UDP 443 不绕过代理 | 规则截图 |
| 12 | 时区/locale | `doctor.py` + 浏览器 | 与真实所在地一致 | JSON/截图 |
| 13 | 账号会话 | Claude Settings | 无陌生设备 | 截图（脱敏） |
| 14 | 2FA | 账号设置 | 已开启 | 人工确认 |
| 15 | 申诉材料 | 仅在被封时 | 事实完整、无敏感信息 | 文档 |

## 不能验收的项

以下无法从客户端证明，必须标 `UNKNOWN`：

- Anthropic 服务端的账号风险分/阈值。
- “这个 IP 一定不会被封”。
- “关掉遥测就不会被检测”。
- “指纹浏览器一定不会关联”。
- “某商家住宅 IP 是官方认可”。

## 验收命令

```bash
python3 scripts/doctor.py --json --output machine-profile.json
python3 scripts/egress_check.py --json --output egress.json
python3 scripts/verify.py --profile machine-profile.json --egress egress.json --region TW
```

`--region` 用 ISO 3166-1 alpha-2 代码（如 `TW`、`US`、`JP`）。脚本只做“是否在本地支持列表”的粗判；最终以官方页面为准。

## 交付模板

```text
Claude 环境验收

已确认：
- ...

未确认：
- ...

不通过：
- ...

已做改动 / 回滚：
- ...

下一步：
- 你：...
- Agent：...
```

不要把“未确认”写成“通过”。不要用总分掩盖单项失败。
