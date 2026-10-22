# Jev Clipboard Guard

> Made by the team behind [Aion](https://aion.7caifei.com/?utm_source=github&utm_medium=readme&utm_campaign=jev_clipboard_guard) — an AI-powered desktop assistant for everyday workflows.

一个使用 Apple「快捷指令」和 Jev 决策 API 的 iPhone 自动化原型。源文件使用 [Cherri](https://github.com/electrikmilk/cherri) 编写，并通过 GitHub Actions 编译。

> **重要边界：** 这不是 iOS 系统级剪切板权限拦截器。App Is Opened 自动化不能保证在目标 App 读取剪切板之前运行；覆盖剪切板也无法撤回已发生的读取。

## 功能设计

- 将目标 App 名称作为快捷指令输入；为不同 App 配置独立的个人自动化。
- 在本地先检查明显的密码、验证码、API Key 和私钥模式，命中时用单个空格覆盖剪切板，不发送给 Jev。
- 本地识别淘宝/天猫、拼多多、抖音、小红书、快手、京东、美团/大众点评、B 站等常见分享链接或口令。
- 已识别且目标 App 匹配的分享内容会被保留，不发送原始分享内容给模型。
- 淘宝/天猫、拼多多、京东商品分享内容可以通过本地购物/比价工具白名单跨 App 保留；默认示例为“慢慢买、什么值得买、惠惠购物助手、比价狗”。请按快捷指令传入的实际 App 名称修改规则。
- 微信/支付宝相关内容、未知分享口令或无法匹配的分享内容会要求用户选择保留或覆盖。
- 其他普通文本发送给 Jev，返回 ALLOW、DENY 或不确定时让用户确认。
- Jev API 地址可编辑，默认使用 TypeSafe 官方 API：`https://api.typesafe.ai/v1/systemone`。

## Jev API 配置

官方 API 文档：

- [TypeSafe API 文档](https://api.typesafe.ai/docs)
- [TypeSafe 官方网站](https://typesafe.ai/)

默认 endpoint：

```text
https://api.typesafe.ai/v1/systemone
```

模型默认使用 `jev-latest`。将 `.cherri` 编译并导入「快捷指令」后，在对应的 `apiUrl` 文本/变量动作中修改 endpoint，并在 `apiKey` 动作中填写自己的 API Key。**不要把真实 API Key 提交到 GitHub，也不要分享已经填入密钥的快捷指令。** API Key 会保存在个人快捷指令中；这适合个人原型，不适合作为面向公众分发的生产方案。面向公众的产品应使用自己控制的服务端代理，避免把 API Key 分发到客户端。

## GitHub Actions 自动编译

每次推送到 `main`、创建 Pull Request 或手动运行 Actions 时，工作流会运行静态检查、构建固定 commit 的 Cherri 编译器、编译未签名的验证产物，并尝试通过 RoutineHub HubSign 生成可导入的 `.shortcut`。签名服务不可用时仍保留未签名编译产物；未签名 plist 仅用于验证编译，不应误当成可直接安装的快捷指令。

## 本地检查

```bash
python3 scripts/check_source.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 安装与自动化

1. 从 Actions 下载 `Jev-Clipboard-Guard-shortcut` artifact（仅在签名成功时出现）。
2. 在 iPhone「文件」中打开签名后的 `.shortcut` 并导入快捷指令。
3. 填入自己的 API Key；必要时修改 `apiUrl`。
4. 为每个目标 App 创建“打开 App”个人自动化，将 App 名称作为文本输入传给 `Jev Clipboard Guard`。
5. 先用无敏感信息的测试文本和示例分享链接测试，确认不会误清空重要剪切板内容后再考虑日常使用。

## 现有限制与风险

- iOS 不向普通第三方 App 开放通用接口来拦截其他 App 的每次剪切板读取请求。
- “打开 App”自动化可能在目标 App 读取剪切板之后才执行，无法提供真正的授权前置拦截。
- 本地正则识别只能尽力而为，分享格式变化后需要更新；未识别或误识别都可能发生。
- 覆盖剪切板会破坏原内容，且无法撤销目标 App 已经读取的数据。
- 普通文本会被发送到所配置的 Jev endpoint；请勿在不接受数据外发的情况下使用。
- 自动化未完成真机测试前，不应把它作为安全边界使用。

## More from us

**[Aion — AI-powered desktop assistant](https://aion.7caifei.com/?utm_source=github&utm_medium=readme&utm_campaign=jev_clipboard_guard)** · Explore Aion and our other work on the [official website](https://aion.7caifei.com/?utm_source=github&utm_medium=readme&utm_campaign=jev_clipboard_guard).

## Project status

- **Prepared:** Cherri source, README, static checks, GitHub Actions workflow.
- **Observed:** source contract checks and share-rule unit tests pass locally.
- **Not yet verified:** Cherri compilation in CI, HubSign signing, importing/running on a real iPhone.
