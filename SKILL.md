---
name: claude-account-safety
version: 1.0.0
description: "Claude 账号安全与新机器环境基线（用户常称防封/反封/保号）：在新 Mac/Windows/Linux 上完成 Claude 使用环境初始化、网络/DNS/WebRTC/时区一致性检查、Claude Code 配置审计、本机残留只读审计、封号风险体检与申诉材料整理。合规优先；不伪装身份/位置、不绕 KYC/支付、不共享账号、不承诺免封。"
---

# Claude Account Safety

把“新机器上把 Claude 环境配好”做成可重复、可验收的流程，而不是一次性教程。

这个 Skill 负责：

- 新机器初始化：系统、Python、Claude Code、代理客户端、浏览器 profile。
- 环境体检：出口 IP 一致性、DNS/WebRTC/IPv6 泄漏、时区/语言一致性、QUIC、代理链。
- Claude Code 审计：官方端点、配置目录、版本、遥测开关、第三方中转识别。
- 账号卫生：一人一号、支付、会话、2FA、申诉材料。
- 交付证据：`machine-profile.json`、`setup-report.md`、验收清单。

它不负责，也不会做：

- 伪装身份、伪造位置、代过 KYC、代充、成品号、拼车、共享账号。
- 用多个账号绕过额度或封禁。
- 承诺“绝对不封”或给出虚假的风险概率。
- 把第三方中转/号池包装成“官方直连”。

## 先过政策门禁（必须）

在改任何设置之前，先确认用户**实际所在国家/地区**，并对照 Anthropic 当前的支持地区列表：

- https://www.anthropic.com/legal/supported-regions
- https://www.anthropic.com/supported-countries

判断规则：

1. **实际在支持地区**：继续。目标是让环境真实、稳定、一致，不是伪装成另一个地方。
2. **实际不在支持地区，或无法确认**：停止环境配置。说明官方服务在该地区不可用；不要提供改时区、住宅 IP、指纹浏览器、代过 KYC、成品号、拼车、第三方中转等规避方案。可以讨论替代模型、合规云渠道或等待官方支持。
3. **用户要求“伪装/绕过/代过验证”**：拒绝，并转向风险体检、合规整改或申诉材料。

官方列出的封号原因只有三类：反复违反 Usage Policy、从不支持地区创建账号、违反 ToS。技术环境只能降低“环境异常”信号，不能把不合规变成合规。

## 秘密处理（采购链接/订阅 URL）

住宅 IP 的购买链接、订阅 URL、节点 UUID、密码都是 bearer credential。规则：

1. 不写入 Skill、报告、日志、聊天记录、Git。
2. 只存引用：`op://Private/<item>/<field>`、`env:VAR`、`keychain:service/account`。
3. 安装前运行 `scripts/secret_check.py`；发现高置信度 secret 直接拒绝安装。
4. 需要在新机器续费/购买时，由用户从密码管理器取出，在官方页面完成；Agent 不代付、不代登录。
5. 如果用户要求“把链接写进 Skill 方便迁移”，拒绝写入，改为存引用并给一次性读取命令。

详见 `references/12-secrets.md`。

## 工作流

### 0. 确认任务与地区

先问清三件事，能合并成一次问：

- 你实际在哪个国家/地区？是否在官方支持列表？
- 这台机器是日常本机、专用机，还是 VM/VPS？
- 目标是“新机器首次配置”“已有环境排查”，还是“封号后清理/申诉”？

如果用户已经明确回答过，不要重复问。地区不确定时，先让用户打开官方页面确认，不要猜。

### 1. 只读盘点

先跑只读体检，不改任何系统设置：

```bash
python3 scripts/doctor.py --json --output machine-profile.json
python3 scripts/doctor.py --summary
```

`doctor.py` 只收集：

- OS、版本、架构、Python 版本。
- 时区、UTC 偏移、locale、`LANG`/`LC_ALL`。
- 代理环境变量是否存在（值只显示是否设置，不输出完整 URL）。
- IPv6 支持、DNS 服务器、默认路由。
- Claude Code CLI 是否存在、版本、配置目录是否存在。
- 常见浏览器与代理客户端是否存在。

它不读取：密码、token、订阅 URL、节点 UUID、Cookie、聊天记录、Keychain。

### 2. 选运行路线

三条路线并列，不要默认替用户选：

| 路线 | 适合 | 代价 |
|---|---|---|
| 本机 | 只在这台机器用 Claude，环境简单 | 与日常浏览器/其他账号共享风险最高 |
| VM | 想把 Claude 环境与日常环境隔离 | 需要虚拟化软件和额外磁盘 |
| VPS/专用机 | 多设备接入、长期在线、环境可复现 | 成本、延迟、运维；不要把 VPS 当“防封神器” |

路线确定后，再读对应的 `references/09-new-machine.md` 章节。路线变了，之前的检查结论作废，重新跑。

### 3. 生成计划

```bash
python3 scripts/plan.py --profile machine-profile.json --os macos
```

输出一张按风险分级的清单：

- A 档：只读检查、报告、方案、预演。
- B 档：可逆的本地配置（新建浏览器 profile、写报告、安装 CLI 包装器）。
- C 档：必须用户当场确认（改时区/语言、切 TUN/防火墙、改出口、登录/付款/KYC、删数据）。

计划里每一步都要有：目标、命令/路径、预期结果、回滚方式。不能只写“优化一下”。

### 4. 执行

默认只做 A 档。B/C 档必须满足：

- 用户看过具体计划并明确同意。
- 改动前有备份或可回滚方案。
- 不覆盖用户已有配置；不复制别人的节点名、端口、订阅、域名白名单。
- 不把凭据写进仓库、报告、日志或聊天记录。

系统级设置（时区、语言、DNS、TUN、防火墙、IPv6）优先让用户自己在 GUI/系统设置里完成；Agent 给精确步骤和验收命令，不代点。

### 5. 验收

```bash
python3 scripts/egress_check.py --json --output egress.json
python3 scripts/verify.py --profile machine-profile.json --egress egress.json --region TW
```

验收结果只允许四种状态：

- `PASS`：有证据，且符合预期。
- `FAIL`：有证据，且不符合预期。
- `UNKNOWN`：没查到，或工具/权限不足。
- `N/A`：不适用，必须写原因。

单次 `curl` 成功、节点名带“住宅”、网页能打开，都不算整机验收通过。浏览器 WebRTC/DNS 泄漏必须在真实浏览器里看，不能用 CLI 结果代替。

### 6. 交付

生成 `setup-report.md`，至少包含：

- 已确认的事实（附命令/页面证据）。
- 未确认/无法验证的项。
- 已做的改动与回滚方式。
- 账号卫生清单。
- 下一步（谁做什么）。

报告里不出现：完整代理 URL、订阅链接、节点 UUID、密码、token、Cookie、KYC 资料。

## 常用入口

```bash
# 只读体检
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json

# 出口一致性（可选，需要网络）
python3 scripts/egress_check.py --json --output egress.json

# 生成计划（不执行）
python3 scripts/plan.py --profile machine-profile.json --os macos

# 验收
python3 scripts/verify.py --profile machine-profile.json --egress egress.json --region TW

# 验证采购/订阅链接的引用（不打印明文）
python3 scripts/secret_ref.py check "op://Private/<provider>/subscription-url"
python3 scripts/secret_ref.py --copy "keychain://claude-account-safety/proxy-subscription"

# 本机 Claude 残留只读审计（不删除）
python3 scripts/cleanup_audit.py
python3 scripts/cleanup_audit.py --compaction-stats

# 自测（开发用）
python3 -m unittest discover -s tests -v
```

## 参考文档

按需读取，不要一次加载全部：

| 主题 | 文件 |
|---|---|
| 官方政策、支持地区、封号原因、申诉 | `references/01-policy-and-boundaries.md` |
| 体检项与证据口径 | `references/02-inventory.md` |
| 网络出口、DNS、WebRTC、IPv6、QUIC | `references/03-network.md` |
| 浏览器 profile 与指纹一致性 | `references/04-browser.md` |
| Claude Code 官方端点、配置、遥测 | `references/05-claude-code.md` |
| 账号、支付、会话、拼车风险 | `references/06-account-hygiene.md` |
| 验收矩阵与命令 | `references/07-verification.md` |
| 403/429/529、登录循环、泄漏排查 | `references/08-troubleshooting.md` |
| 新机器 macOS/Windows/Linux 步骤 | `references/09-new-machine.md` |
| 设计说明与证据边界 | `references/10-legacy-notes.md` |
| 出口选型（BYO，不带商家） | `references/11-egress-options.md` |
| 采购链接/订阅 URL/凭据保护 | `references/12-secrets.md` |
| 本机 Claude 残留审计与可恢复清理 | `references/13-local-cleanup.md` |
| Claude Code 本机记录与 compact 摘要 | `references/14-claude-code-local-data.md` |

## 交付语气

- 先说结论，再说证据；不要用“可能”“据说”代替检查结果。
- 没查到的写 `UNKNOWN`，不要编。
- 用户要越过政策边界时，只拒绝一次并给替代路径，不反复说教。
- 不把“节点叫住宅”“IPPure 分数低”“某教程说稳”当成官方认可或免封证明。
