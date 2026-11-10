# 新机器开场提示词

把下面这段发到新机器上的 Codex / Claude：

```text
请使用 $claude-account-safety 帮我初始化这台新机器上的 Claude 环境。

先做只读体检，不要改任何系统设置：
1. 确认我实际所在地区是否在 Anthropic 支持列表内；
2. 运行 python3 scripts/doctor.py --summary；
3. 告诉我缺什么、哪些项无法自动确认；
4. 给我一张按 A/B/C 分级的计划，A 档只读，B 档可逆，C 档必须我本人确认；
5. 不要询问或输出密码、token、订阅 URL、节点 UUID、Cookie。

这台机器的用途是：<本机 / 专用机 / VM / VPS>。
我已经有的出口是：<已有代理 / VPS / 住宅代理 / 暂无>。
```

如果 Agent 不在 Skill 目录里，先运行：

```bash
./install.sh --target "$HOME/.agents/skills"
```

然后把 `$claude-account-safety` 换成对应 Agent 的 Skill 调用方式。
