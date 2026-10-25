# 「获取当前 App」动作：实测报告与采用理由

> 结论先行：`获取当前 App`（`is.workflow.actions.getcurrentapp`）返回**执行瞬间的前台 App**，
> 名字是**本地化显示名**（如「访达」「计算器」）。本项目用它替代原来唯一依赖的
> `ShortcutInput`，因为「打开 App」自动化**通常不传任何快捷指令输入**。

## 1. 为什么改

旧实现（v18 及以前）：

```cherri
#define noinput stopwith "请从“打开 App”自动化运行，并传入目标 App 名称。"
@currentApp = ShortcutInput
```

问题在两处叠加：

1. 个人自动化「App 已打开」触发时，快捷指令**默认没有输入**，`ShortcutInput` 是空的。
2. `#define noinput stopwith ...` 会在没有输入时直接中止，于是自动化一跑就停，
   用户看到的只是「什么都没发生」。

用户在 iPhone 上配置的自动化（截图证据）是「阿里巴巴 或 电话 已打开 时」运行本快捷指令，
快捷指令里没有任何显式传参 —— 这正是上述组合必然失败的场景。

## 2. 动作存在性证据（本机 macOS 27.0.1 / 26A434）

| 证据 | 内容 |
| --- | --- |
| `WorkflowKit` 本地化表 | `/System/Library/PrivateFrameworks/WorkflowKit.framework/Versions/A/Resources/Localizable.loctable` 含 `"Current App" => "当前 App"` 等各语言条目 |
| dyld 共享缓存 | `dyld_shared_cache_arm64e.71` 偏移 85112164 附近含 `is.workflow.actions.getcurrentapp`、类名 `WFGetCurrentAppAction`、描述 `Gets the current visible app.` |
| 参数 | `WFVisibleAppScope`，取值 `Current`（单数）与 `Visible`（复数，iPad/Mac 多窗口用） |
| 官方说明 | [What's new in Shortcuts for iOS 18](https://support.apple.com/en-us/121131)：新增「Get Current App」动作，可按「which app is being used」改变快捷指令行为；随 iOS/iPadOS 18.2、macOS 15.2 发布 |

## 3. 本机实测（可复现）

探针：`is.workflow.actions.getcurrentapp`（`WFVisibleAppScope = Current`）→ `getitemname` → `is.workflow.actions.output`，
用 `shortcuts run <名字> -o /tmp/out.txt` 取结果。

| 运行前的前台 App | `-o` 文件内容 |
| --- | --- |
| Finder | `访达` |
| 计算器 | `计算器` |

结论：

- 返回的是**单个 App 的本地化显示名**，可以直接和自动化里配置的 App 名（`阿里巴巴`、`电话`）做文本匹配。
- 它取的是**执行那一刻**的前台 App，而不是「触发自动化的 App」。对「打开 App」自动化，
  这两者通常相同（App 打开后即成为前台）；但存在极窄的竞态窗口。
- 因此本项目采用**动作优先 + `ShortcutInput` 兜底**：手动运行并显式传入 App 名时仍按传入值走。

一个附带发现（影响选型）：`Visible` 复数档没有用于本项目的必要；且实测时未安装的探针
（`ShowVis`）调用 `shortcuts run` 会报 `找不到快捷指令`，与本动作无关。

## 4. 现在的实现

```cherri
// 顶部用户可配置区（导入后改这里，不动逻辑）
@targetApps = ["阿里巴巴", "电话", "微信", "支付宝", "淘宝", "京东"]
@notifyOnResult = "是"
@onSensitive = "覆盖剪切板"
@sendToJev = "是"

const detectedAppRaw = getCurrentApp("Current")
const detectedApp = getName(detectedAppRaw)
const detectedAppText = "{detectedApp}"
const isSelfApp = matchText('(?i)^(快捷指令|Shortcuts|Shortcut)$', detectedAppText)
const isSelfAppText = "{isSelfApp}"
const inputAppText = "{ShortcutInput}"
@currentApp = detectedAppText
if detectedAppText == "" || isSelfAppText != "" {
    // 手动运行并显式传参时以传入值为准；否则弹列表让用户选目标 App。
    @currentApp = inputAppText
}
const afterInputText = "{@currentApp}"
if afterInputText == "" || afterInputText == "快捷指令" || afterInputText == "Shortcuts" {
    const pickedApp = chooseFromList(@targetApps, "选择本次要检查的目标 App")
    @currentApp = "{pickedApp}"
}
const resolvedAppText = "{@currentApp}"
if resolvedAppText == "" || resolvedAppText == "快捷指令" || resolvedAppText == "Shortcuts" {
    if @notifyOnResult == "是" {
        showNotification("没有确定要检查的 App，本次跳过。", "Jev Clipboard Guard", false)
    }
    stop()
}
```

要点：

- **手动触发也能用**：从「快捷指令」App 里点运行时，`getCurrentApp` 返回「快捷指令」自己，
  代码识别到前台是快捷指令后会让用户从 `@targetApps` 里选，不再拿错 App。
- `ShortcutInput` 仍是兜底：显式传参时以传入值为准。
- 去掉了 `#define noinput stopwith`，自动化不再被输入校验直接中止。
- 空值判断先用 `"{...}"` 取出文本再比较，而不是直接比较变量：
  Cherri 里 `@变量` 的类型是 `variable`，直接写 `if @currentApp == ""` 会报
  `Invalid type 'variable' for conditional '=='`；先取文本再比较即可。
- 所有 `showNotification` 都包在 `if @notifyOnResult == "是"` 里，关掉后自动/手动都静默。
- 命中敏感内容走 `@onSensitive`（「覆盖剪切板」或「只提醒不动」）；`@sendToJev != "是"` 时纯本地，不联网。

## 5. 已知局限

- **竞态**：若 App 启动后、快捷指令执行前用户已切走，取到的会是切走后的前台 App。
  这是该动作的固有语义，不是实现缺陷。
- **本地化名**：返回的是显示名，中文系统下是「阿里巴巴」而非 `com.taobao.taobao4iphone`。
  匹配规则用的就是中文名，因此一致；若系统语言不是中文，需要相应调整规则里的名称。
- **最低系统**：iOS/iPadOS 18.2、macOS 15.2 起才有此动作。更早的系统上编译产物能导入，
  但该动作会被忽略（取不到值 → 走 `ShortcutInput` 兜底 → 空 → 弹「无法识别当前 App」）。
