#!/usr/bin/env python3
"""Static safety/contract checks for the Cherri source (not a runtime test)."""
from pathlib import Path
import sys

source_path = Path(__file__).resolve().parents[1] / "Jev_Clipboard_Guard.cherri"
s = source_path.read_text(encoding="utf-8")
checks = {
    "official TypeSafe API endpoint is the default": 'https://api.typesafe.ai/v1/systemone' in s,
    "API endpoint remains editable": '@apiUrl =' in s,
    "API key is read from Shortcuts Storage (Store Content)": (
        "action 'is.workflow.actions.getstoredcontent' loadStore" in s
        and 'loadStore("jev.apiKey", true)' in s
        and '#question jevApiKey' not in s
    ),
    "first run asks for the key once and persists it": (
        "action 'is.workflow.actions.setstoredcontent' saveStore" in s
        and "saveStore(\"jev.apiKey\", enteredKeyText, true)" in s
    ),
    "other config keys are also read from Storage": (
        'loadStore("jev.targetApps", true)' in s
        and 'loadStore("jev.notifyOnResult", true)' in s
        and 'loadStore("jev.onSensitive", true)' in s
        and 'loadStore("jev.sendToJev", true)' in s
    ),
    "unconfigured API key stops before any network request": (
        s.index('if apiKeyCheck == "" || apiKeyCheck == "REPLACE_WITH_JEV_API_KEY"') < s.index('@response = jsonRequest')
    ),
    "target app is resolved from Get Current App, not only ShortcutInput": (
        "action 'is.workflow.actions.getcurrentapp' getCurrentApp" in s
        and 'const detectedAppRaw = getCurrentApp("Current")' in s
        and 'const detectedApp = getName(detectedAppRaw)' in s
        and s.index("const detectedAppRaw = getCurrentApp") < s.index("const clip = getClipboard()")
    ),
    "ShortcutInput stays as the fallback for explicit-input runs": (
        'const inputAppText = "{ShortcutInput}"' in s
        and 'const afterInputText = "{@currentApp}"' in s
        and 'if detectedAppText == "" || isSelfAppText != "" {' in s
    ),
    "no noinput guard aborts App Is Opened automations": (
        "#define noinput stopwith" not in s
    ),
    "Jev request includes current model alias and typed choice": '"model": "jev-latest"' in s and '"type": "choice"' in s,
    "clipboard is overwritten with a space, not an empty string": '@blankClipboard = " "' in s and 'setClipboard(@blankClipboard, true)' in s and 'setClipboard(" ", true)' not in s,
    "sensitive content is checked locally before network request": s.index('const localRisk = matchText') < s.index('@response = jsonRequest'),
    "share payload is handled before sending ordinary text to Jev": s.index('if @shareType != ""') < s.index('@response = jsonRequest'),
    "shopping-consumer allowlist exists for cross-app product shares": 'const trustedShoppingConsumer = matchText' in s,
    "uncertain Jev decision prompts the user": 'ASK_USER' in s and 'menu "Jev 无法高置信度自动放行，请选择"' in s,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
if failed:
    sys.exit(1)
print(f"\n{len(checks)} static checks passed. This does not replace Cherri compilation or iPhone runtime testing.")
