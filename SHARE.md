# 给别人的一页说明

这个包是“Claude 环境基线 Skill”，不是免封器。收到后按下面做：

## 1. 先确认地区

打开 https://www.anthropic.com/legal/supported-regions ，确认你**实际所在地区**在列表内。

不在列表内：停止。买美国住宅 IP、改时区、换指纹浏览器都不会让账号合规，仍然违反 Anthropic 的支持地区政策。

## 2. 安装

macOS / Linux：

```bash
./install.sh --target "$HOME/.agents/skills"
```

Windows PowerShell：

```powershell
.\install.ps1 -Target "$HOME\.agents\skills"
```

## 3. 只读体检

```bash
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json
```

## 4. 让 Agent 接手

在新会话里发：

```text
$claude-account-safety 帮我在新机器上初始化 Claude 环境。先做只读体检，不要改系统设置。
```

Agent 会先问地区、机器用途和现有出口，然后给 A/B/C 分级计划。

## 5. 重要边界

- 不要把自己的 Claude 账号借给别人，也不要拼车。
- 不要用第三方中转/号池冒充官方端点。
- 采购链接/订阅 URL 只放自己的密码管理器；不要发到群里或提交到仓库。
- 出口选型只按 `references/11-egress-options.md` 的评估维度；本仓库不提供商家采购页。
- 不要相信“100% 防封”“包过 KYC”“成品号”。

## 6. 分享时不要带

- `secrets.env`
- `machine-profile.json`
- `egress.json`
- `setup-report.md`
- `clash/profile.yaml`
- 任何订阅 URL、节点 UUID、账号、密码

`package.sh` 默认会排除这些文件。

分享前跑一遍：

```bash
python3 scripts/secret_check.py --root .
./package.sh
```

只发 `dist/claude-account-safety-1.0.0.tar.gz` 和对应的 `.sha256`，不要发整个工作目录。
