# Claude Account Safety Skill

一个可移植的 Claude 账号安全与新机器环境基线 Skill（用户常称防封/反封/保号）。目标是把“换一台机器重新配 Claude”变成一条可重复、可验收的流程。

## 它是什么

- 一个 Agent Skill：`SKILL.md` 定义工作流、门禁和交付格式。
- 一套跨平台只读体检脚本：macOS / Windows / Linux。
- 本机 Claude 残留只读审计：缓存、日志、桌面数据、CLI 配置分类；默认不删除。
- 一套新机器安装器：把 Skill 复制到 Codex / Claude / 通用 Agent 的 skills 目录。
- 一套验收清单：网络出口、DNS、WebRTC、IPv6、时区/语言、Claude Code、账号卫生。

## 它不是什么

- 不是“免封器”，不承诺不封号。
- 不提供伪装身份/位置、代过 KYC、代充、成品号、拼车、共享账号、第三方中转。
- 不替代 Anthropic 官方政策、支持地区列表和申诉流程。

## 快速开始

### 1. 在这台机器上使用

```bash
cd claude-account-safety
python3 scripts/doctor.py --summary
python3 scripts/doctor.py --json --output machine-profile.json
python3 scripts/plan.py --profile machine-profile.json --os macos
```

然后在 Codex / Claude 里调用：

```text
$claude-account-safety 帮我在新机器上初始化 Claude 环境，先做只读体检，不要改系统设置。
```

### 2. 安装到 Agent 的 skills 目录

macOS / Linux：

```bash
./install.sh --target "$HOME/.agents/skills"
```

Windows PowerShell：

```powershell
.\install.ps1 -Target "$HOME\.agents\skills"
```

也支持安装到项目内（推荐先这样试）：

```bash
./install.sh --project .
# 结果：./.agents/skills/claude-account-safety/
```

安装器不会覆盖已有目录；目标存在时会先备份再退出，让你决定是否替换。

### 3. 在新机器上

把整个 `claude-account-safety/` 目录带到新机器（U 盘、私有仓库、scp 都行），然后：

```bash
./install.sh --target "$HOME/.agents/skills"
python3 scripts/doctor.py --summary
```

具体步骤见 `references/09-new-machine.md`。

## 分享给别人

```bash
./package.sh
# dist/claude-account-safety-1.0.0.tar.gz
# dist/claude-account-safety-1.0.0.tar.gz.sha256
```

对方解压后运行 `./install.sh --target "$HOME/.agents/skills"`，再按 `SHARE.md` 操作。打包会自动跑 secret 扫描，并排除 `secrets.env`、`machine-profile.json`、`egress.json`、`setup-report.md`、`clash/profile.yaml`。

## 目录

```text
claude-account-safety/
├── SKILL.md                     # Agent 入口
├── README.md
├── SHARE.md                     # 给别人的一页说明
├── install.sh                   # macOS/Linux 安装器
├── install.ps1                  # Windows 安装器
├── package.sh                   # 打 tar.gz + sha256（排除秘密/报告）
├── references/                  # 按主题读取的参考文档
├── scripts/
│   ├── doctor.py                # 只读体检
│   ├── egress_check.py          # 出口一致性检查（可选网络）
│   ├── plan.py                  # 生成分级计划
│   ├── verify.py                # 验收
│   ├── secret_check.py          # 安装前 secret 扫描
│   ├── secret_ref.py            # 不打印明文的 secret 引用解析
│   ├── cleanup_audit.py         # 本机 Claude 残留只读审计 + compact 统计
│   └── selftest.py              # 自测
├── templates/
│   ├── new-machine-prompt.md    # 新机器开场提示词
│   ├── clash-snippet.yaml       # 无凭据的 Clash 片段模板
│   ├── egress-provider.md       # 不含秘密的出口供应商卡片
│   └── setup-report.md          # 验收报告模板
└── tests/
```

## 安全边界

- 默认只读；不会自动改时区、DNS、TUN、防火墙、IPv6。
- 不读取/输出密码、token、订阅 URL、节点 UUID、Cookie、聊天记录、Keychain。
- 不复制任何人的 `clash/profile.yaml`；里面通常含凭据。
- 所有 B/C 档改动都要先有计划、备份和回滚方式。

## 采购链接与秘密

住宅 IP 的购买链接/订阅 URL 不写进 Skill。它们是 bearer credential，泄露后别人可以直接用你的出口。

- 只存引用：`op://Private/<item>/<field>`、`env:VAR`、`keychain:service/account`。
- 明文放在 1Password / Keychain / Secret Service / age 加密文件里，密钥不要和密文放同一仓库。
<!-- secret-check: ignore-next-line -->
- 安装前自动跑 `scripts/secret_check.py`；发现 `ss://`、`vmess://`、`socks5://user:pass@`、订阅 token、API key 等直接拒绝安装。
- 新机器续费/购买由你本人在官方页面完成；Agent 不代付、不代登录。

细节见 `references/12-secrets.md`。

## 支持范围

- macOS 13+（优先）
- Windows 10/11（PowerShell 5.1+）
- Linux（systemd 发行版优先）
- Python 3.10+；只用标准库

## 开发

```bash
python3 -m unittest discover -s tests -v
python3 scripts/selftest.py
python3 -m py_compile scripts/*.py
```

## 许可与安全

- License: MIT（见 `LICENSE`）。
- 安全问题请走私密渠道：`SECURITY.md` / GitHub Security Advisories。
- CI：`.github/workflows/ci.yml` 跑单元测试、secret 扫描、语法检查、体检脚本和打包。
- 仓库只应出现 `op://` / `env:` / `keychain://` 引用；不要把真实订阅 URL、token、账号提交进来。

## 政策

使用前先确认你实际所在地区在 Anthropic 支持列表内：

- https://www.anthropic.com/legal/supported-regions
- https://www.anthropic.com/supported-countries

不在支持地区时，这个 Skill 会停止环境配置，不提供规避方案。
