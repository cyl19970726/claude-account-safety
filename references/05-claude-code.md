# 05 Claude Code 官方端点、配置与遥测

## 安装

优先使用 Anthropic 官方安装方式（以当前官方文档为准）：

- https://code.claude.com/docs/en/setup
- `claude --version`
- `claude auth login`

不要从来路不明的“防封版”“镜像版”安装包更新 Claude Code。

## 官方端点

- 默认 API：`https://api.anthropic.com`
- 不要设置 `ANTHROPIC_BASE_URL` 指向第三方中转，除非你明确知道自己在做什么，并且接受账号/数据风险。
- 第三方工具应使用 Console API Key 或受支持的云服务，不要复用 Pro/Max 订阅登录令牌。

## 客户端会看到的信号

本地 REA 研究（E3）在公开样本里看到：

- `apiBaseUrlHost`：端点不是官方时会进入遥测事件。
- `api_error_origin: "first_party"`：官方端点错误可能带此标记；中转通常没有。
- `gatewayDetected` / `gatewayHost` / provider 分类。
- 系统时区、locale、UTC 偏移。
- Desktop `ant-did`（安装级随机 UUID，不是硬件 UUID）。

这些是“客户端可能上报的字段”，不是“封号公式”。服务端阈值不可见。

## 多账号配置目录

官方支持一个人使用多个账号，推荐每个账号一个独立配置目录：

```bash
export CLAUDE_CONFIG_DIR="$HOME/.claude-accounts/work"
claude auth login
```

切换账号时用不同目录，不要复制/共享同一个 OAuth 凭据给他人。

## 遥测开关

官方环境变量（以当前文档为准）：

```bash
export DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

关闭遥测不等于“防封”；它只是减少非必要上报。不要把关闭遥测当成绕过检测的手段。

## 版本与更新

- 先记录 `claude --version`。
- 升级走官方安装器/包管理器。
- 不要在多个安装方式之间混用（npm 全局 + 原生安装 + 第三方脚本）。
- 升级后重跑 `doctor.py`，确认路径和版本。

## 已知历史

- 2.1.91–2.1.196：曾被发现用日期分隔符/Unicode 撇号做地区标记；约 2.1.197 移除。
- 2.1.312：本地复核未再找到该机制。
- 这不等于“现在没有任何检测”；只说明该具体通道在当前样本里没找到。

## Claude Code 层验收

| 项 | 通过标准 | 证据 |
|---|---|---|
| CLI 存在 | `which claude` 有路径 | 命令输出 |
| 版本可读 | `claude --version` 正常 | 命令输出 |
| 官方端点 | 未设置第三方 `ANTHROPIC_BASE_URL` | 环境变量检查 |
| 配置目录 | 使用预期目录，未共享 | 路径检查 |
| 登录方式 | 官方 `claude auth login` | 人工确认 |
| 遥测 | 知情选择，不是“防封开关” | 环境变量 |
| 更新来源 | 官方安装器/包管理器 | 人工确认 |
