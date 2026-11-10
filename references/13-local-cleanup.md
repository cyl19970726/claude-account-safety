# 13 本机 Claude 残留：只读审计与可恢复清理

## 先说清楚

清理本机残留**不能解封**，也不能证明“设备不再关联”。如果账号被停用，优先保存证据和走申诉；清理可能删掉申诉需要的日志。

本 Skill 只做：

- 只读审计：列出 Claude 相关目录/文件、大小、数量。
- 可恢复清理计划：先备份/隔离，再由用户确认。

不做：

- 删除 Keychain/凭据。
- 轮换设备 ID、`ant-did`、`machineID` 等“换设备身份”操作。
- 清理浏览器指纹/Cookie 来规避关联。
- 在账号被限制后换号继续使用。

## 审计

```bash
python3 scripts/cleanup_audit.py
python3 scripts/cleanup_audit.py --json --output cleanup-audit.json
```

它只读，不删除、不移动任何文件。

想看 Claude Code 的完整会话记录、prompt 历史和 compact 摘要落在哪，见 `14-claude-code-local-data.md`。`cleanup_audit.py --compaction-stats` 会统计 `projects/**/*.jsonl` 的行数、`compact_boundary` 和 `isCompactSummary`，不打印内容。

## 分类

| 类别 | 典型内容 | 默认 |
|---|---|---|
| `cache` | 缓存、临时渲染数据 | 备份后可清理 |
| `logs` | 日志、崩溃报告 | 先导出证据，再清理 |
| `desktop_data` | 桌面端数据、会话、设置 | 先导出/备份；不要整目录删 |
| `cli_config` | `~/.claude`、`~/.claude.json` | **不要整目录删**；逐项确认 |
| `credentials` | Keychain/凭据 | **永不删除**（退出登录走官方流程） |
| `conversation` | 对话历史 | 用户明确要求才处理；先导出 |

## 推荐顺序

1. 退出 Claude Desktop / Claude Code / 相关后台进程。
2. 导出需要保留的对话、设置、日志、申诉证据。
3. 备份目标目录到本地时间戳目录（不要放公开仓库）。
4. 先清理 `cache`/`logs`；`desktop_data`/`cli_config` 逐项确认。
5. 需要卸载时走官方卸载流程；不要手工删系统组件。
6. 重新安装后重新登录，检查 `Settings > Account > Active sessions`。

注意：`projects/` 和 `history.jsonl` 默认是 **NEVER-DELETE**；它们可能包含申诉证据、token、`.env` 和工具输出。要删除必须先导出/备份并逐项确认。

## 不要做

- 不要为了“换设备”去改 `ant-did`、`machineID`、`userID`。
- 不要删除 Keychain 里的 Claude 凭据来“清除关联”；用官方退出登录。
- 不要清浏览器 Cookie/指纹后马上换号登录。
- 不要在申诉前清空日志；先保存证据。
- 不要把清理脚本放到公开仓库运行；先读源码，再在 VM 里试。

## 和封号申诉的关系

如果账号被停用：

- 先保存警告邮件、request ID、时间线、相关日志。
- 走 Restricted Account 申诉。
- 清理只用于“这台机器不再使用 Claude”或“准备转交/回收设备”，不是解封手段。
