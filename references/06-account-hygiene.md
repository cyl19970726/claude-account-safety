# 06 账号、支付、会话与申诉

## 账号

- 一人一号；不共享、不拼车、不买成品号。
- 不用多个账号绕过额度或封禁。
- 多个账号使用独立 `CLAUDE_CONFIG_DIR`，不共享 OAuth 凭据。
- 邮箱使用本人长期可访问的地址；不要一次性邮箱。
- 资料按真实情况填写；不伪造姓名、地址、地区、证件。

## 支付

- 使用本人或已获明确授权的支付方式。
- 账单地址与发卡行登记一致；卡片来源国/地区在官方支持范围内。
- 完成发卡行要求的 3DS。
- 不使用黑卡、盗卡、代充、退款套利、虚拟卡批量试错。
- 支付失败时先停，核对账单地址/余额/3DS，不要连续换卡/换 IP/换号重试。

## 会话与安全

- 开启 2FA；保护邮箱和 Google/Apple 账号。
- 定期检查 `Settings > Account > Active sessions`；陌生设备立即终止。
- 不在公共电脑/共享浏览器上登录。
- 不把登录链接、验证码、token 发给他人。

## 使用行为

- 不批量注册、不批量发消息、不爬取、不做平台操纵。
- 不转售 Claude 访问、不把订阅额度包装成 API 卖给第三方。
- 不做模型蒸馏/批量导出，除非有明确授权。
- 长跑 agent/daemon 要有日志、限流、人工确认和停止条件。

## 被封后

1. 先停：不要换号继续、不要重复提交被拒请求。
2. 保存证据：警告邮件、时间、request ID、相关日志、部署变更。
3. 登录被停用账号，打开 Restricted Account 页面提交申诉。
4. 申诉只写事实：账号、时间、使用场景、已做的修复、为什么认为误判。
5. 不提交虚假身份、不隐去关键信息、不反复开新工单。
6. 如果是 API 警告，可通过官方公布的安全邮箱（如 `usersafety@anthropic.com`）联系；以当前帮助中心为准。

## 风险清单

| 风险 | 等级 | 处理 |
|---|---|---|
| 共享/拼车/成品号 | 高 | 停止；换回自己的账号 |
| 第三方中转/号池 | 高 | 换官方端点；审计数据暴露 |
| 虚拟卡/代充/黑卡 | 高 | 停用；换官方支付 |
| 同设备多账号绕额度 | 高 | 停止；只保留合规账号 |
| 频繁换国家/IP | 中高 | 固定真实环境 |
| 公共场所登录 | 中 | 改密码、开 2FA、终止会话 |
| 无 2FA | 中 | 立即开启 |
| 长跑 agent 无审计 | 中 | 加日志、限流、人工确认 |

## 申诉材料模板

```text
Account email:
Account/org ID (if shown):
Suspension date/time (with timezone):
Plan (Free/Pro/Max/Team/Enterprise):
What I was doing:
What changed recently:
Evidence (request IDs, error messages, screenshots):
Why I believe this is a mistake:
What I have already fixed:
```

不要附密码、完整 token、支付卡号、KYC 证件照片。
