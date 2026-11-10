# 出口供应商卡片（不含秘密）

这张卡可以提交/同步；不要写购买链接、订阅 URL、账号、密码、节点 UUID。

```text
Alias:
Type:            self-hosted VPS / residential proxy / home broadband
Exit region:
ASN type:        residential / datacenter / mobile / enterprise
Shared or dedicated:
Static or rotating:
IPv4/IPv6:
Protocol:        HTTP(S) / SOCKS5 / other
Renewal date:
Secret reference: op://Private/<item>/subscription-url
Validation:      claude.ai trace loc=..., cloudflare trace loc=..., date
Notes:
```

新机器上需要续费/更换时，按 `Secret reference` 从密码管理器取，不把明文写进这张卡。
