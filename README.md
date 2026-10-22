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

每次推送到 `main`、创建 Pull Request 或手动运行 Actions 时，工作流运行静态检查、构建固定 commit 的 Cherri 编译器、编译未签名的验证产物，并尝试通过 RoutineHub HubSign 生成可导入的 `.shortcut`。**2026-10-22 已验证 264 个动作成功编译，未签名产物已上传；远程签名因服务返回 HTML 验证页面而失败。** GitHub 公共 macOS Runner 没有登录你的 iCloud，也无法直接使用 `shortcuts sign`。因此构建是否绿色不应取代对签名产物的检查。

## 本地检查

```bash
python3 scripts/check_source.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 安装与自动化

### 已编译的快捷指令（需签名）

1. 从 [GitHub Actions 的成功编译记录](https://github.com/monkey-sking/Jev-Clipboard-Guard/actions/runs/39856737592) 下载 `Jev-Clipboard-Guard-unsigned-plist`，解压得到 `Jev_Clipboard_Guard_unsigned.plist`，并把扩展名改为 `.shortcut`。
2. 在 **已登录 iCloud 的 Mac** 上，将该未签名文件与 [scripts/sign_on_mac.command](scripts/sign_on_mac.command) 放到同一目录，文件命名为 `Jev_Clipboard_Guard_unsigned.shortcut`，运行 `zsh ./sign_on_mac.command`（也可以手动运行下方命令）。
3. 将生成的 **已签名** `Jev_Clipboard_Guard.shortcut` 用 AirDrop 或 iCloud Drive 发送到 iPhone，在「文件」中打开并添加到快捷指令。
4. 编辑导入后的快捷指令，填入自己的 Jev API Key，必要时修改 `apiUrl`。
5. 为每个目标 App 创建「打开 App」个人自动化，把该 App 的实际名称作为文本传给此快捷指令。
6. 先用**不含个人秘密**的测试数据验证分享码和比价 App 场景。

```bash
shortcuts sign -i Jev_Clipboard_Guard_unsigned.shortcut -o Jev_Clipboard_Guard.shortcut -m anyone
```

目前尚未完成 iPhone 真机验证。**未签名的 XML plist 即使改扩展名，也不能直接当成已签名的可安装产物。**

### 签名为什么没有自动完成？

- 2026-10-22 的 GitHub Actions 编译已经通过，原始未签名 XML plist 结构合法。
- RoutineHub HubSign 旧接口返回了 HTML 验证页面，而非以 `AEA1` 开头的已签名二进制；服务可用性由第三方控制。
- GitHub 托管 macOS Runner 运行 Apple CLI 时提示需要先登录 iCloud。
- 自动签名的后续方案是由你**已登录 iCloud 的 Mac** 执行本地签名，或配置有权限的远程签名服务。不要在公共仓库上传 Apple ID 或任何 API 密钥。

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

- **Verified:** GitHub Actions 已完成 Cherri v2.3.0 源码编译，生成 264 个动作的未签名 XML plist；静态检查和分享口令测试通过。
- **Observed:** HubSign 旧接口返回 HTML 验证页面，GitHub macOS Runner 缺少 iCloud 登录，无法完成签名。
- **Not yet verified:** 使用个人 Mac 进行苹果签名、在 iPhone 导入和实际运行、Jev 线上请求与剪切板保护时序。
