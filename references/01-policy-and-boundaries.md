# 01 政策、边界与证据口径

## 官方入口

- 支持地区政策：https://www.anthropic.com/legal/supported-regions
- 支持国家/地区：https://www.anthropic.com/supported-countries
- 使用政策：https://www.anthropic.com/legal/aup
- 警告与申诉：https://support.claude.com/en/articles/8241253
- 身份验证：https://support.claude.com/en/articles/14328960
- Claude Code 数据使用：https://docs.anthropic.com/en/docs/claude-code/data-usage

政策会变。每次做地区/账号判断前，重新打开官方页面，不要只信本文件或社区教程。

## 官方列出的封号原因

Anthropic 帮助中心把停用原因归为三类：

1. 反复违反 Usage Policy。
2. 从不支持的地区创建账号。
3. 违反适用的服务条款（包括共享账号、未授权转售/转接访问、欺诈支付等）。

“模型拒绝回答某次请求”不等于账号违规；实时输出拦截和账号级停用是两回事。

## 地区判断（2026-11-10 核对）

- 台湾在支持列表中。
- 中国大陆、香港、澳门不在支持列表中。
- Anthropic 已公布 2026-11-12 生效的新版 Supported Regions Policy；生效后以新页面为准。
- 政策还覆盖“人在不支持地区使用”“注册地/总部在不支持地区”“被不支持地区实体多数控股”等情形，不只看 IP。

因此：

- 人在支持地区：可以做环境一致性、账号卫生和风险体检。
- 人在不支持地区：不要用改时区、住宅 IP、指纹浏览器、代过 KYC、成品号、拼车、第三方中转去“变成合规”。技术手段改变不了“服务未在该地区提供”这一事实。

## 这个 Skill 的边界

会做：

- 只读体检、环境基线、网络/DNS/WebRTC/时区检查。
- Claude Code 官方端点、配置目录、版本、遥测开关审计。
- 账号卫生清单、封号风险体检、申诉材料整理。
- 新机器安装与可重复验收。

不会做：

- 伪装身份、伪造位置、代过 KYC、代充、成品号、拼车、共享账号。
- 用多账号绕过额度/封禁。
- 提供“保证不封”的承诺或虚假概率。
- 把第三方中转/号池描述成官方直连。

## 证据分级

| 级别 | 含义 | 例子 |
|---|---|---|
| E1 | 官方文档/页面 | Anthropic Supported Regions、Usage Policy |
| E2 | 本机可复现证据 | `claude --version`、`scutil --dns`、出口 trace |
| E3 | 客户端逆向/公开研究 | Claude Code 2.1.91–2.1.196 Unicode 隐写报告 |
| E4 | 社区经验/教程 | “固定 IP 更稳”“机场节点容易连坐” |
| E5 | 商家/affiliate 宣称 | “纯净住宅 IP，包过”“100% 防封” |

报告里必须区分 E1–E5。E4/E5 不能写成官方规则；E3 只能说明“客户端可能采集什么”，不能证明服务端一定如何判定。

## 已知的客户端信号（来自本地 REA 研究，E3）

在 Claude Code / Desktop 的公开样本里，能看到这些信号：

- 系统时区、locale、UTC 偏移。
- `apiBaseUrlHost`：当 API 端点不是 `api.anthropic.com` 时，中转域名会进入遥测事件。
- `api_error_origin: first_party`：官方端点错误可能带此标记；走中转时通常缺失。
- `gatewayDetected` / `gatewayHost` / provider 分类（gateway/bedrock/foundry/firstParty/customEndpoint）。
- Desktop 的 `ant-did` 安装级随机 UUID；不是硬件 UUID。
- 旧版 CLI 的 `deviceId` 是随机 64-hex；不是硬件 UUID。

不能从这些信号推出“账号权重公式”或“某个字段单独决定封号”。服务端判定不可见。

## 历史检测机制

- Claude Code 2.1.91（2026-04-02）至约 2.1.196：在自定义 `ANTHROPIC_BASE_URL` 且命中特定时区/域名时，曾用日期分隔符和 Unicode 撇号变体做隐蔽标记。
- 约 2.1.197 移除；本地对 2.1.312 的复核未再找到该机制。
- 这不代表“现在没有检测”，只代表“这个具体隐写通道在当前样本里没找到”。

## 一句话

先把地区和账号合规搞清楚，再谈环境优化。环境优化只能减少异常信号，不能改变服务资格。
