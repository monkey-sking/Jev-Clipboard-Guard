# Jev-Clipboard-Guard 导入问题（Import Questions）验证报告

日期：2026-10-24
环境：macOS 27.0.1 (26A434)，快捷指令 10.0（macOS），iPhone 真机（iOS 未记录版本号）

## 结论（TL;DR）

**带「导入问题」的快捷指令在 macOS 27.0.1 上导入时会静默失败**：
预览窗能打开、按钮能点、但点「添加快捷指令」后什么都不会发生——没有报错、没有落盘、
导入流程不会继续。人工点击与自动化点击（AXPress / CGEvent）结果一致，排除自动化能力问题。

**iPhone 真机同样失败**（用户实测：「我点了没有效果，点了闪一下，还是有这个」）。

因此 **`ActionIndex` 补丁无法解决**：问题不在字段值（0/1/2 都试过），而是带
`WFWorkflowImportQuestions` 数组的文件本身在这个系统的导入管线上被静默拒绝。

网上查不到任何相同问题的公开讨论（DuckDuckGo、Reddit、GitHub Code Search 均无命中），
可能是 macOS 27 / iOS 26 引入的未记录回归。

## 实验矩阵

| 文件 | ActionIndex | 动作数 | 来源 | 结果 |
|---|---|---|---|---|
| tiny_noq（无问题） | — | 1 | 手写 | ✅ 导入成功（shortcuts list 21→22） |
| tiny_q | 0 | 1 | 手写 | ❌ 按钮闪一下，无反应 |
| tiny_q2 / tinyqa / tinyurl | 0/1/未填 | 1-2 | 手写 | ❌ 全部失败 |
| Jev_Clipboard_Guard（无问题） | — | 266 | cherri | ✅ 导入成功 |
| Jev_Clipboard_Guard（有问题） | 0/1/2 | 266 | cherri+补丁 | ❌ 失败 |
| q1（ActionIndex=1） | 1 | 266 | cherri+补丁 | ❌ 失败 |

注意：`Jev_Clipboard_Guard`（无问题、266 动作）**可以**正常导入，
说明不是动作数、cherri 编译产物或签名问题——**只有带导入问题的文件失败**。

## 已排除的干扰项

- 幽灵窗口：必须 `pkill -f "Shortcuts.app/Contents/MacOS/Shortcuts"` 重启 App 后再测；
  残留旧实例会点到已失效的窗口。
- 名称冲突弹框（替换/保留两者/取消）会在同名导入时出现，已通过改名排除。
- 屏幕锁定/显示器休眠会让 AX 请求挂死、截图全黑；测试前必须确认
  `CGSSessionScreenIsLocked=false` 并用 `caffeinate -d -u` 保持唤醒。
- 签名格式：`shortcuts sign` 产物是 **AEA 加密归档**，不能用 plistlib 读取；
  修改内容必须从 `*_u.shortcut`（未签名 plist）改起再重签。

## 对项目的决定

1. **导入问题方案放弃**（至少在当前系统版本上不可用）。
2. 回退到「用户手动编辑 Key」方案：源码里 `@apiKey = "REPLACE_WITH_JEV_API_KEY"`
   占位，用户导入后自己改一次。
3. 空 Key 处理保持为**静默通知 + stop**（`Jev_Clipboard_Guard.cherri:169-173`），
   不用阻塞式 `alert`——因为快捷指令由「打开 App」自动化触发，弹框会卡住自动化。
4. `scripts/patch_import_questions.py` 保留在仓库里（有单元测试），
   便于将来系统修复后一键重新启用导入问题；CI 里的补丁步骤保留。

## 测试工具（/private/tmp，系统重启会清掉）

- `axpress2 <pid> <text> [exact|contains]` — 按 AXDescription 找元素并 AXPress
- `pressnear <pid> <x> <y>` — 找离坐标最近的按钮并 AXPress
- `axfill2 <pid> <text>` — 往第一个 AXTextArea 写值
- `axdump/axtext/axrows <pid>` — AX 树转储
- `clickat <x> <y>` / `rclick <x> <y>` — CGEvent 真实点击
- `keymod <keycode> [cmd]` — 键盘事件
- 屏幕坐标基准：屏幕 1920x1080 点，`screencapture` 3840x2160（4x）；
  预览窗「添加快捷指令」按钮在屏幕点 (1126,537)。
