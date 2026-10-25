# Jev Clipboard Guard

> Made by the team behind [Aion](https://aion.7caifei.com/?utm_source=github&utm_medium=readme&utm_campaign=jev_clipboard_guard) — an AI-powered desktop assistant for everyday workflows.

一个使用 Apple「快捷指令」和 Jev 决策 API 的 iPhone 自动化原型。源文件使用 [Cherri](https://github.com/electrikmilk/cherri) 编写，并通过 GitHub Actions 编译。

> **重要边界：** 这不是 iOS 系统级剪切板权限拦截器。App Is Opened 自动化不能保证在目标 App 读取剪切板之前运行；覆盖剪切板也无法撤回已发生的读取。

## 功能设计

- 确定目标 App：优先用「获取当前 App」识别执行瞬间的前台 App；从「快捷指令」App 里手动
  运行时前台是快捷指令自己，此时会弹列表让你选目标 App；显式传参仍以传入值为准。
- **配置存在系统「储存空间」，首次运行问一次，之后不用改代码**：
  `jev.apiKey`（Jev Key）、`jev.targetApps`（目标 App 列表）、`jev.notifyOnResult`（每次结果是否弹通知）、
  `jev.onSensitive`（命中敏感内容时「覆盖剪贴板」或「只提醒不动」）、`jev.sendToJev`（纯本地模式）。
- 需要 iOS/iPadOS 18.2+ 或 macOS 15.2+（「获取当前 App」动作的系统门槛）。
- 在本地先检查明显的密码、验证码、API Key 和私钥模式，命中时按 `@onSensitive` 决定覆盖或只提醒，不发送给 Jev。
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

模型默认使用 `jev-latest`。

**Key 与配置放在「储存空间」里，不用改代码。** 导入后第一次运行（手动运行一次即可）会依次问你：

1. Jev API Key（`jev.apiKey`）
2. 目标 App 列表（`jev.targetApps`，逗号分隔，默认 `阿里巴巴,电话,微信`）
3. 每次结果是否弹通知（`jev.notifyOnResult`，默认「是」）
4. 命中敏感内容时怎么办（`jev.onSensitive`，默认「只提醒不动」，可选「覆盖剪切板」）
5. 是否发送给 Jev（`jev.sendToJev`，默认「是」；选「否」= 纯本地模式，只在设备上做规则检查）

这些值用 Shortcuts 的 `is.workflow.actions.setstoredcontent` 写入系统「储存空间」，之后每次运行都从存储读取，**不会出现在快捷指令的动作里**，所以分享/导出 `.shortcut` 文件不会带上你的 Key。想改配置就重新回答一次问题，或在 `@KEY_*` 常量区直接改默认值后重新编译。

`apiUrl` 仍是源码里的常量（默认 `https://api.typesafe.ai/v1/systemone`），需要改 endpoint 就改 `Jev_Clipboard_Guard.cherri` 的 `@apiUrl` 再编译。

**不要把真实 API Key 写进源码提交到 GitHub。** 当前方案下 Key 只存在设备的储存空间里；面向公众的产品仍应使用自己控制的服务端代理，避免把 API Key 分发到客户端。

Key 没配好时（储存空间为空且用户取消了输入），快捷指令只发一条系统通知然后停止，**不弹阻塞式对话框**——因为它由「打开 App」自动化触发，弹框会把自动化卡住而不是通知到人。

> **为什么不在导入时问 Key？** 曾尝试用 Shortcuts 的「导入问题」（Import Questions）+ `#question jevApiKey` 在导入时弹框收 Key，实测**在 macOS 27.0.1 与 iPhone 真机上都会静默失败**：带 `WFWorkflowImportQuestions` 的文件点「添加快捷指令」后无任何反应、不落盘、不报错，而同样的文件去掉该字段就能正常导入。换 `ActionIndex` 取值、动作数、手写/编译产物均无效，网上也无公开讨论。完整实验矩阵见 [IMPORT_QUESTIONS_FINDINGS.md](IMPORT_QUESTIONS_FINDINGS.md)。`scripts/patch_import_questions.py` 与对应单测保留在仓库里，待系统修复后可一键恢复。


## GitHub Actions 自动编译

每次推送到 `main`、创建 Pull Request 或手动运行 Actions 时，工作流运行静态检查、构建固定 commit 的 Cherri 编译器、编译未签名的验证产物，并尝试通过 RoutineHub HubSign 生成可导入的 `.shortcut`。**2026-10-22 已验证 264 个动作成功编译，未签名产物已上传；远程签名因服务返回 HTML 验证页面而失败。** GitHub 公共 macOS Runner 没有登录你的 iCloud，也无法直接使用 `shortcuts sign`。因此构建是否绿色不应取代对签名产物的检查。

## 本地检查

```bash
python3 scripts/check_source.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 本地编译

```bash
cherri Jev_Clipboard_Guard.cherri --skip-sign
shortcuts sign -m anyone -i "Jev Clipboard Guard_unsigned.shortcut" -o Jev_Clipboard_Guard.shortcut
```

> `scripts/patch_import_questions.py` 目前不在编译链路上：它给导入问题补 `ActionIndex`，但带导入问题的文件在当前 macOS/iOS 上根本无法导入（见上文与 [IMPORT_QUESTIONS_FINDINGS.md](IMPORT_QUESTIONS_FINDINGS.md)）。系统修复后把它加回这里即可。

## 安装与自动化

### 已编译的快捷指令（需签名）

1. 从 [GitHub Actions 的成功编译记录](https://github.com/monkey-sking/Jev-Clipboard-Guard/actions/runs/39856737592) 下载 `Jev-Clipboard-Guard-unsigned-plist`，解压得到 `Jev_Clipboard_Guard_unsigned.plist`，并把扩展名改为 `.shortcut`。
2. 在 **已登录 iCloud 的 Mac** 上，将该未签名文件与 [scripts/sign_on_mac.command](scripts/sign_on_mac.command) 放到同一目录，文件命名为 `Jev_Clipboard_Guard_unsigned.shortcut`，运行 `zsh ./sign_on_mac.command`（也可以手动运行下方命令）。
3. 将生成的 **已签名** `Jev_Clipboard_Guard.shortcut` 用 AirDrop 或 iCloud Drive 发送到 iPhone，在「文件」中打开并添加到快捷指令。
4. 首次运行一次，回答 5 个配置问题（Key、目标 App、通知、敏感处理、是否发送）；
   之后配置存在系统「储存空间」，可在 `Jev_Clipboard_Guard.cherri` 顶部的 `@KEY_*` 默认值里预置。
   并检查顶部用户可配置区的默认值（`@targetApps`、`@notifyOnResult`、`@onSensitive`、`@sendToJev`、`@apiKey`）。
5. 触发方式二选一：
   - **手动**：从「快捷指令」App / 主屏 / 小组件运行，首次会弹列表让你选目标 App。
   - **自动化（一条覆盖全部 App）**：在「快捷指令 → 自动化」新建「App 已打开」，把目标 App
     （阿里巴巴、电话、微信…）**一次多选**全加进同一条自动化，动作选 `Jev Clipboard Guard`，
     并关闭「运行前询问」。**不需要**传参，它自己用「获取当前 App」识别前台 App。
     注意 iOS 的「App 已打开」在**从后台切回**已打开过的 App 时经常不触发，这是 iOS 侧行为，
     与本快捷指令无关；要稳定覆盖这种场景请用轻点背面 / 操作按钮 / 小组件手动触发。
   - **轻点背面**：设置 → 辅助功能 → 触控 → 轻点背面 → 轻点两下/三下 → 选 `Jev Clipboard Guard`。
     这个触发器没有系统延迟，是"切换 App 后立刻检查"最实际的方案。
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
