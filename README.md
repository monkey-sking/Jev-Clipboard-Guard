# Jev Clipboard Guard

<!-- badges:start -->
[![Last commit](https://img.shields.io/github/last-commit/monkey-sking/Jev-Clipboard-Guard?style=flat-square)](https://github.com/monkey-sking/Jev-Clipboard-Guard/commits/main) [![Python](https://img.shields.io/github/languages/top/monkey-sking/Jev-Clipboard-Guard?style=flat-square)](https://github.com/monkey-sking/Jev-Clipboard-Guard/search?l=Python) [![views](https://hits.sh/github.com/monkey-sking/Jev-Clipboard-Guard.svg?style=flat-square&label=views&color=0e75b6)](https://github.com/monkey-sking/Jev-Clipboard-Guard)
<!-- badges:end -->

> Made by the team behind [Aion](https://aion.7caifei.com/?utm_source=github&utm_medium=readme&utm_campaign=jev_clipboard_guard) — an AI-powered desktop assistant for everyday workflows.

一个使用 Apple「快捷指令」和 Jev 决策 API 的 iPhone 自动化原型。源文件使用 [Cherri](https://github.com/electrikmilk/cherri) 编写，并通过 GitHub Actions 编译。

> **重要边界：** 这不是 iOS 系统级剪切板权限拦截器。App Is Opened 自动化不能保证在目标 App 读取剪切板之前运行；覆盖剪切板也无法撤回已发生的读取。

## 功能设计

- 确定目标 App：优先用「获取当前 App」识别执行瞬间的前台 App；从「快捷指令」App 里手动
  运行时前台是快捷指令自己，此时会弹列表让你选目标 App；显式传参仍以传入值为准。
- **自动化安全**：整个流程在「识别不到 App」时静默停止，不弹任何对话框、不发「已跳过」通知——
  自动化触发时任何 UI 都会把自动化卡死，而卡死的自动化等于没运行。
- **配置存在系统「储存空间」，首次运行问 3 个问题，之后不用改代码**：
  `Jev API 密钥`、`要检查的 App`、`敏感内容处理`（外加两个进阶开关 `每次弹通知`、`允许发送给 Jev`）。
  键名故意用中文，普通用户看得懂。
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

**首次运行 3 步设置，之后不用再管。** 导入后**手动运行一次**，会依次问你：

| 步骤 | 问题 | 存在哪个键 |
|---|---|---|
| 第 1 步 | 粘贴你的 Jev API Key | `Jev API 密钥` |
| 第 2 步 | 要对哪些 App 做检查（逗号分隔，默认 `阿里巴巴,电话,微信`） | `要检查的 App` |
| 第 3 步 | 命中密码/验证码时怎么办：`1` 只提醒不动 / `2` 用空格覆盖 | `敏感内容处理` |

配置用 Shortcuts 的 `is.workflow.actions.setstoredcontent` 写进系统「储存空间」，之后每次运行自动读取，**不写进快捷指令的动作**，所以分享/导出 `.shortcut` 文件不会带上你的 Key。

两个进阶开关默认给最稳的值（弹通知 + 允许联网判断），需要时手动改储存空间：`每次弹通知`（`是`/`否`）、`允许发送给 Jev`（`否` = 纯本地，绝不联网）。

**改配置**：删掉储存空间里的 `Jev API 密钥`，再运行一次就会重新问。

**改 API 地址**：默认 `https://api.typesafe.ai/v1/systemone`，绝大多数人不用改。自建代理/测试时写储存空间 `API 地址` 覆盖，或改 `Jev_Clipboard_Guard.cherri` 的 `@apiUrl` 默认值再编译。

**不要把真实 API Key 写进源码提交到 GitHub。** 当前方案下 Key 只存在设备的储存空间里；面向公众的产品仍应使用自己控制的服务端代理，避免把 API Key 分发到客户端。

Key 没填就取消时会提示"设置未完成"并停止，**不弹阻塞式对话框**——因为它由「打开 App」自动化触发，弹框会把自动化卡住而不是通知到人。

> **为什么不在导入时问 Key？** 曾尝试用 Shortcuts 的「导入问题」（Import Questions）+ `#question jevApiKey` 在导入时弹框收 Key，实测**在 macOS 27.0.1 与 iPhone 真机上都会静默失败**：带 `WFWorkflowImportQuestions` 的文件点「添加快捷指令」后无任何反应、不落盘、不报错，而同样的文件去掉该字段就能正常导入。换 `ActionIndex` 取值、动作数、手写/编译产物均无效，网上也无公开讨论。完整实验矩阵见 [IMPORT_QUESTIONS_FINDINGS.md](IMPORT_QUESTIONS_FINDINGS.md)。`scripts/patch_import_questions.py` 与对应单测保留在仓库里，待系统修复后可一键恢复。


## GitHub Actions 自动编译

每次推送到 `main`、创建 Pull Request 或手动运行 Actions 时，工作流运行静态检查与分享口令单测、构建固定 commit 的 Cherri 编译器、编译产物并校验动作数量，最后上传**未签名**的 plist。

**工作流只产出未签名产物，这是刻意的**：Shortcuts 不接受未签名文件，而签名只有 Apple 能做——`shortcuts sign` 需要一台登录了维护者 iCloud 的 Mac（托管 Runner 上跑不了），第三方 RoutineHub HubSign 接口现在返回 HTML 重定向而不是 `AEA1` 数据。早先的工作流会尝试这两种自动签名并因此在每次 `main` 推送时失败；现在改为在本机用 [scripts/sign_on_mac.command](scripts/sign_on_mac.command) 签名。

## 本地检查

```bash
python3 scripts/check_source.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 本地编译

```bash
# 1. 编译出未签名产物（文件名取自源码里的 `#define name`）
cherri Jev_Clipboard_Guard.cherri --skip-sign --derive-uuids

# 2. 用 Apple 官方 CLI 签名（需要一台登录了你 iCloud 的 Mac）
zsh scripts/sign_on_mac.command
```

产物：`Jev 剪贴板守卫_unsigned.shortcut`（未签名）→ `Jev 剪贴板守卫.shortcut`（已签名）。

> **文件名就是快捷指令名。** Cherri 的 `#define name` 只用于**产物文件名**，不会写进 plist（编译产物里没有 `WFWorkflowName`）。而 iOS/macOS 导入时用的正是文件名，所以 `Jev 剪贴板守卫.shortcut` 装完就叫「Jev 剪贴板守卫」。想改名就改源码的 `#define name`，并同步 `scripts/sign_on_mac.command` 里的 `NAME`。

> `scripts/patch_import_questions.py` 目前不在编译链路上：它给导入问题补 `ActionIndex`，但带导入问题的文件在当前 macOS/iOS 上根本无法导入（见上文与 [IMPORT_QUESTIONS_FINDINGS.md](IMPORT_QUESTIONS_FINDINGS.md)）。系统修复后把它加回这里即可。

## 安装与自动化

### 已编译的快捷指令（需签名）

1. 从 [GitHub Actions 的编译记录](https://github.com/monkey-sking/Jev-Clipboard-Guard/actions) 下载 `Jev-Clipboard-Guard-unsigned-plist`，解压得到 `Jev_Clipboard_Guard_unsigned.plist`（**未签名，不能直接装**）。
2. 在 **已登录 iCloud 的 Mac** 上，把该文件放到仓库根目录，运行 `zsh scripts/sign_on_mac.command`。脚本会自动找到未签名文件、重试 Apple 时间戳服务的瞬时 500 错误，产出 `Jev 剪贴板守卫.shortcut`。
3. 把 **已签名** 的 `Jev 剪贴板守卫.shortcut` 用 AirDrop 或 iCloud Drive 发到 iPhone，在「文件」里点开 → 「添加快捷指令」。
   > 刚导入后列表里可能还显示「0 个操作」——那是列表没刷新，**退出并重开「快捷指令」App** 就会显示真实动作数。
4. 首次运行一次，依次回答配置问题（Key、目标 App、敏感处理等）；之后配置存在系统「储存空间」，不用再动源码。
5. 触发方式二选一：
   - **手动**：从「快捷指令」App / 主屏 / 小组件运行，首次会弹列表让你选目标 App。
   - **自动化（一条覆盖全部 App）**：在「快捷指令 → 自动化」新建「App 已打开」，把目标 App
     （阿里巴巴、电话、微信…）**一次多选**全加进同一条自动化，动作选 `Jev 剪贴板守卫`，
     并关闭「运行前询问」。**不需要**传参，它自己用「获取当前 App」识别前台 App。
     注意 iOS 的「App 已打开」在**从后台切回**已打开过的 App 时经常不触发，这是 iOS 侧行为，
     与本快捷指令无关；要稳定覆盖这种场景请用轻点背面 / 操作按钮 / 小组件手动触发。
   - **轻点背面**：设置 → 辅助功能 → 触控 → 轻点背面 → 轻点两下/三下 → 选 `Jev 剪贴板守卫`。
     这个触发器没有系统延迟，是"切换 App 后立刻检查"最实际的方案。
6. 先用**不含个人秘密**的测试数据验证分享码和比价 App 场景。

目前尚未完成 iPhone 真机验证。**未签名的 XML plist 即使改扩展名，也不能直接当成已签名的可安装产物**——系统会弹「无法打开快捷指令 / 不支持导入未签名的快捷指令文件」。

### 签名为什么没有自动完成？

- GitHub Actions 的编译已通过，未签名 XML plist 结构合法（`WFWorkflowActions` 数量由工作流断言）。
- RoutineHub HubSign 旧接口现在返回 HTML 重定向，不再返回以 `AEA1` 开头的已签名二进制；服务可用性由第三方控制，因此该路径已从工作流和脚本中移除。
- GitHub 托管的 macOS Runner 运行 Apple CLI 时需要先登录 iCloud，无法使用。
- 所以签名固定由**你已登录 iCloud 的 Mac** 执行。不要在公共仓库上传 Apple ID 或任何 API 密钥。
- `shortcuts sign` 会偶发 `NSURLErrorDomain error 500`——这是 Apple 时间戳服务的瞬时故障，重试即可（脚本已内置 5 次重试）。

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

- **Verified:** GitHub Actions 用 Cherri v2.3.0 编译源码，产出 462 个动作的未签名 XML plist；静态检查与分享口令单测通过。
- **Verified（2026-10-25，macOS 27.0.1 / 26A434）:** `shortcuts sign -m anyone` 产出的 `AEA1` 文件可以正常导入「快捷指令」，导入后动作数为 462（导入后需重启 Shortcuts App 才会刷新列表里的动作计数）。
- **Verified:** 文件名决定导入后的快捷指令名（Cherri 不写 `WFWorkflowName`），`Jev 剪贴板守卫.shortcut` 装完即叫「Jev 剪贴板守卫」。
- **Observed:** HubSign 接口返回 HTML 重定向，无法自动签名；因此工作流只产出未签名产物，签名走本机脚本。
- **Not yet verified:** 在 iPhone 上导入和实际运行、Jev 线上请求与剪切板保护时序、App 已打开自动化的触发时机。
