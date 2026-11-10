# 12 采购链接、订阅 URL 与凭据保护

> 本文件因包含示例 URL，被 `secret_check.py` 排除扫描。**不要把真实链接贴进这里**；真实值只放密码管理器或 Skill 目录之外的 `secrets.env`。

## 先说结论

住宅 IP 的购买链接、订阅 URL、节点 UUID、密码，都是 **bearer credential**：

- 谁拿到，谁就能用你的出口、消耗你的流量。
- 很多订阅 URL 还会暴露账号、节点列表、到期时间。
- 放进 Skill、Git、报告、聊天记录，等于把钥匙复制到每个副本里。

所以本 Skill **不保存明文**，只保存“引用”。真正的新机器配置由你从密码管理器取出，或由本机 secret provider 在内存中提供。

## 推荐存储

### 1Password（跨平台首选）

把购买链接/订阅 URL 放在 1Password 的 item 里，Skill 只写引用：

```text
op://Private/<provider>/purchase-url
op://Private/<provider>/subscription-url
op://Private/<provider>/account
```

读取：

```bash
op read "op://Private/<provider>/subscription-url"
```

不要把 `op read` 的输出重定向到文件、日志或聊天。

本 Skill 带一个不打印明文的解析器：

```bash
# 只验证引用能解析，不输出值
python3 scripts/secret_ref.py check "op://Private/<provider>/subscription-url"

# 解析后直接放进剪贴板（不打印）
python3 scripts/secret_ref.py --copy "op://Private/<provider>/subscription-url"

# 环境变量引用
python3 scripts/secret_ref.py check "env:PROXY_SUBSCRIPTION_URL"
```

### macOS Keychain

```bash
# 存入（URL 作为 password；不要出现在 shell history 里）
security add-generic-password -a "$USER" -s "claude-account-safety/proxy-purchase" -w

# 读取到剪贴板（不打印）
security find-generic-password -a "$USER" -s "claude-account-safety/proxy-purchase" -w | pbcopy

# 或用本 Skill 的解析器
python3 scripts/secret_ref.py --copy "keychain://claude-account-safety/proxy-purchase"
```

### Windows Credential Manager / DPAPI

- 用 `cmdkey` 或 PowerShell `CredentialManager` 模块存为 generic credential。
- 不要把 `Export-Clixml` 的 DPAPI 密文当成跨机器可移植方案；它绑定用户/机器。
- 新机器重新从密码管理器取，不要复制旧机器的密文。

### Linux Secret Service

```bash
secret-tool store --label="claude-account-safety proxy" service claude-account-safety key proxy-purchase
secret-tool lookup service claude-account-safety key proxy-purchase
```

### 纯本地加密文件（备选）

如果一定要落盘，用 `age` 或 `gpg` 加密，并把私钥/口令放在密码管理器：

```bash
age -p -o proxy.secret.age proxy.secret.txt
age -d proxy.secret.age
```

不要：

- 把 `age` 私钥和密文放在同一个仓库。
- 用仓库里的 `.env` 当“加密”。
- 把解密结果写进 `machine-profile.json`、`setup-report.md` 或 shell history。

## 本 Skill 的规则

1. 不把购买链接/订阅 URL/节点凭据写入 `SKILL.md`、`references/`、`templates/`、`scripts/`。
2. 不在报告里输出完整 URL；最多写 `host:port` 或 `provider: <alias>`。
3. 安装前运行 `scripts/secret_check.py`；发现高置信度 secret 直接拒绝安装。
4. 需要在新机器上续费/购买时，由用户从密码管理器取出，在官方页面完成；Agent 不代付、不代登录。
5. 如果用户要求“把链接写进 Skill 方便迁移”，回答：不写入；改为存引用，并给一次性读取命令。

## 采购链接的脱敏写法

报告/笔记里可以这样记：

```text
Provider: <alias>
Purpose: residential egress (US)
Renewal: 2026-11-xx
Reference: op://Private/<item>/subscription-url
Exit check: claude.ai trace ip=<redacted> loc=US
```

也可以用 `templates/egress-provider.md` 这张“出口供应商卡片”：只记 alias、地区、续费日、secret reference，不记明文链接。卡片可以同步/提交；`secrets.env` 不要放在 Skill 目录里，放到 `~/.config/claude-account-safety/` 并设 `chmod 600`。

不要记：

```text
https://provider.example/sub?token=...
socks5://user:pass@1.2.3.4:1080
```
