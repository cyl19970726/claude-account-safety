# 14 Claude Code 本机记录与压缩

## 记录在哪

默认根目录：`~/.claude`（Windows：`%USERPROFILE%\.claude`）。设置 `CLAUDE_CONFIG_DIR` 会把整棵树移到别处。

| 路径 | 内容 | 敏感度 |
|---|---|---|
| `projects/<encoded-cwd>/<session-uuid>.jsonl` | 完整会话记录：消息、工具调用/结果、系统提示、工具定义、请求参数 | 高：可能含 `.env`、token、命令输出 |
| `projects/<project>/<session>.orphaned-<timestamp>-<suffix>.jsonl` | 被放到一边的旧 transcript | 高 |
| `projects/<project>/<session>.jsonl.superseded-<timestamp>` | 被替换的旧 transcript | 高 |
| `projects/<project>/<session-uuid>/subagents/` | 子代理 transcript（较新版本） | 高 |
| `history.jsonl` | 输入过的 prompt 历史（含项目路径、session ID、时间） | 高 |
| `sessions/`、`session-env/` | 会话元数据/环境 | 中 |
| `shell-snapshots/` | shell 快照，可能含环境变量 | 高 |
| `backups/` | 配置损坏时的备份 | 中高 |
| `cache/`、`debug/`、`logs/` | 缓存、调试日志、日志 | 中 |
| `plugins/`、`skills/` | 插件/Skill 代码与配置 | 中 |
| `settings.json`、`settings.local.json`、`CLAUDE.md` | 用户设置/记忆 | 中 |
| `~/.claude.json` | 全局配置：`projects`、`machineID`、`userID`、`oauthAccount`、`autoCompactWindowsCache` 等 | 高 |

项目目录名是 cwd 的绝对路径，把非字母数字字符替换成 `-`。例如 `/Users/you/dev/webapp` → `-Users-you-dev-webapp`。

## 压缩是什么

Claude Code 的 `/compact`（和 auto-compact）会把之前的历史替换成一段结构化摘要，让模型继续在更小的上下文里工作。

- 摘要不是单独的 `.gz` 文件；它写进**同一个 session JSONL**。
- 压缩时 transcript 里会出现 `compact_boundary` 记录；紧随其后的用户消息通常带 `isCompactSummary: true`。
- transcript 基本是 append-only：原始轮次可能仍留在文件里；模型只是不再加载被摘要替换的部分。
- `CLAUDE_CODE_TRANSCRIPT_LOCAL_GC=1` 时，较长的 `-p` / Agent SDK 会话可能在 transcript 超过 5 MB 后丢弃压缩前的历史。
- transcript 会按 `cleanupPeriodDays` 保留（默认 30 天）；到期后本地记录可能被清理。
- 想再看摘要：用 `PostCompact` hook 的 `compact_summary`，或解析 JSONL 里的 `isCompactSummary`；TUI 不会直接重放摘要。

相关设置/环境变量：

- `autoCompactWindow`（`~/.claude/settings.json`）
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW`（环境变量，优先级更高）
- `autoCompactWindowsCache`（`~/.claude.json` 的按模型缓存）

## 只读审计

```bash
# 目录/大小/文件数，不解析内容
python3 scripts/cleanup_audit.py

# 额外统计 JSONL 的行数、compact boundary、compact summary
python3 scripts/cleanup_audit.py --compaction-stats

# JSON 输出
python3 scripts/cleanup_audit.py --json --output cleanup-audit.json
```

审计不会删除、移动或上传任何记录。它不会打印 prompt/工具输出内容，只输出路径、大小、行数和计数。

## 清理原则

- 先导出/备份，再清理；`projects/` 和 `history.jsonl` 默认 **NEVER-DELETE**。
- 不要为了“换设备”去改 `machineID`、`userID`、`ant-did`；这不属于清理。
- 不要在申诉前清空日志/transcript；它们是证据。
- 不要把 transcript 提交到公开仓库；它可能包含 token、`.env`、内部路径。
- 需要彻底删除时，由用户明确选择具体文件/目录；先隔离到时间戳目录，再确认删除。

## 证据边界

- E1：Claude Code 官方 `claude-directory`、`settings`、`context-window`、`sessions` 文档。
- E2：本机 `~/.claude/projects/*.jsonl` 的实际结构（键名/类型）可只读核验。
- E4：社区对 JSONL/compact summary 的解析文章；不同版本字段可能变化。

官方文档优先；如果版本升级后路径或字段变了，以本机实际结构和官方文档为准。

## 参考

- https://code.claude.com/docs/en/claude-directory
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/context-window
- https://code.claude.com/docs/en/sessions
- https://code.claude.com/docs/en/data-usage
- https://turnlog.dev/claude-code-jsonl/（E4）
- https://github.com/xoonjaeho/claude-skill-compact-summary（E4）
- https://harnessnotes.com/context-compaction（E4）
