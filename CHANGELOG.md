# Changelog

## 1.0.0 — 2026-11-10

- 首个可移植版本：`SKILL.md` + 跨平台只读体检 + 验收 + 安装器。
- 增加政策门禁：支持地区判断，不做伪装/代过 KYC/共享账号/中转。
- 增加 `doctor.py`、`egress_check.py`、`plan.py`、`verify.py`。
- 增加 `secret_check.py`：安装前扫描订阅 URL、代理 userinfo、API key、私钥。
- 增加 secrets 引用规范（1Password/Keychain/Secret Service/age）。
- 增加 macOS/Windows/Linux 新机器步骤与模板。
- 增加出口选型评估维度（不含商家列表、affiliate 或个人订阅）。
- 增加本机 Claude 残留只读审计（不删除、不轮换设备 ID）。
