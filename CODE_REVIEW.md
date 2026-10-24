# Jev Clipboard Guard 代码审查报告

审查日期：2026-10-23
审查范围：`Jev_Clipboard_Guard.cherri`、`scripts/*.py`、`scripts/sign_on_mac.command`、`tests/*`、`.github/workflows/build-shortcut.yml`
本地验证：`check_source.py` 9/9 通过；`unittest` 3/3 通过；CI 产物 264 actions，含 typesafe URL / placeholder key / jev-latest，均正确。

## 结论摘要

逻辑主体是健康的：**本地→分享口令→Jev** 的三段式顺序正确，本地识别失败不会外发，剪贴板用空格覆盖而非清空，通知不泄露内容。主要问题集中在 **CI 流水线（当前 main 永久红灯）** 和 **Jev 响应缺失字段时的 fail-open 细节**。

| 严重度 | 数量 | 代表问题 |
|---|---|---|
| high | 1 | main 分支 CI 永远失败（签名硬门禁） |
| medium | 3 | confidence 缺失可能中止/放行；敏感正则覆盖不足；本地风险正则边界 |
| low | 4 | concurrency 反斜杠；sign_hubsign 边界；测试盲区；无 LICENSE |

---

## HIGH

### H1. CI 在 main 上永久红灯
`.github/workflows/build-shortcut.yml:99-103`

前面两个签名步骤都 `continue-on-error: true`，但最后这个门禁没有：

```yaml
- name: Require signed Shortcut on main branch
  if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
  run: |
    test -s dist/Jev_Clipboard_Guard.shortcut
    head -c 4 dist/Jev_Clipboard_Guard.shortcut | grep -q 'AEA1'
```

HubSign 已失效（返回 HTML 验证页，README 也承认），所以 `dist/Jev_Clipboard_Guard.shortcut` 根本不会产生 → 第 102 行 `test -s` 必失败。实测最近 7 次 main push 全部 `failure`，唯一成功的 `39856737592` 是加入该门禁之前的那次。HEAD 提交 `e3d94ed` 的 run `39858087720` 失败步骤正是它。

**建议**：把该门禁改成 `continue-on-error: true`，或仅在检测到真实签名产物时才要求；否则每次推送都是红的，失去信号价值。

### M1. Jev 响应缺 `confidence` 时可能中止快捷指令（fail-open）
`Jev_Clipboard_Guard.cherri:194-203`

```cherri
const confidenceValue = getValue(decisionDictionary, "confidence")
@decision = "{chosenDecision}"
const confidenceNumber = number(confidenceValue)
if @decision == "DENY" { ... } else {
    if @decision == "ALLOW" && confidenceNumber >= 0.85 { ... } else { menu ... }
}
```

若 Jev 返回 `ASK_USER`（无 confidence）或网络错误导致解析为空，`number(空)` 在「快捷指令」里可能直接抛错中止。中止发生在 DENY 分支之后、menu 之前 → **剪贴板原样保留**，属于 fail-open。建议先判空/给默认值（如 `number("0")`），确保一定走到 menu。

### M2. 敏感信息正则覆盖不足
`Jev_Clipboard_Guard.cherri` 的 `localRisk`

已覆盖：password/api_key/secret/bearer/access_token/refresh_token/私钥/AKIA 访问键 ID/sk- ts_ tsp_ 前缀。
缺：
- AWS **Secret Access Key**（40 位 base64，常与 AKIA 成对出现）
- GitHub `ghp_` / `gho_` / `github_pat_` 令牌
- 通用 JWT（`eyJ...\.eyJ...\.`）
- 银行卡号、身份证号

这些都是「本地可直接判死」的高危模式，补上能减少对 Jev 的依赖、也降低误发风险。

### M3. 本地风险正则无边界 + 最小长度 4
`localRisk` 用 `\s*[:=：]\s*\S{4,}`，短于 4 字符的秘密（如 `密码: 12`、`pin=123`）漏掉；同时无 `\b`，可能误命中长单词中的子串（方向偏保守，可接受）。建议：口令类最小长度放宽到 1~2，并给英文关键词加词边界。

---

## LOW

### L1. `concurrency.group` 里的反斜杠
`.github/workflows/build-shortcut.yml:13` `group: build-shortcut-\${{ github.ref }}`
YAML 纯量里 `\` 是字面量，`${{ }}` 仍会被求值，group 变成 `build-shortcut-\refs/heads/main`（多一个反斜杠），按 ref 分组的意图基本还在，但这是笔误，建议去掉 `\`。

### L2. `sign_hubsign.py` 的 `signed` 变量与超时
`scripts/sign_hubsign.py:43-50` 逻辑上没问题（异常会先抛），但 `urlopen` 的 `URLError`（非 HTTPError）未被捕获，栈会直接冒到顶层；`timeout=75` 对 CI 偏长。建议补 `urllib.error.URLError` 的友好提示。

### L3. 测试盲区
`tests/test_share_rules.py` 只验证了「分享正则能被某些文本命中」和「普通文本不命中」，**没有验证**：
- 每个平台规则与目标 App 匹配矩阵（`@targetMatches` 逻辑）
- 微信/支付宝强制确认分支
- 本地风险正则的正/负样例
- Jev 分支的任何逻辑

建议给 `localRisk` 和 target-match 各加一组用例（纯 Python 复刻正则即可）。

### L4. 缺少 LICENSE / 安全声明
仓库无 LICENSE；README 已说明 API Key 客户端存储的风险，但可再加一句「本仓库为个人原型，不构成安全边界」。

---

## 值得肯定的设计

- `@blankClipboard = " "` 用空格覆盖而非空串，避免某些 App 把空剪贴板当「无内容」继续追问。
- 敏感内容在 `jsonRequest` 之前本地拦截（`check_source.py` 还固化了这个顺序契约）。
- 分享口令**原文永不发给 Jev**，只发「普通文本」。
- 通知文案不含剪贴板内容。
- `#define noinput stopwith` 防止手动误跑。
- CI 用 `--skip-sign --derive-uuids` 固定产物，静态检查 + 分享用例双闸。

## 建议优先级

1. 修 H1（否则 CI 信号全红，后续改动无法判断回归）
2. 修 M1（fail-open 是安全产品最不该有的方向）
3. 补 M2 的令牌模式
4. 补 L3 测试，再谈 L1/L2/L4
