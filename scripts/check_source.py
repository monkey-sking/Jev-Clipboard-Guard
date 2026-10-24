#!/usr/bin/env python3
"""Static safety/contract checks for the Cherri source (not a runtime test)."""
from pathlib import Path
import sys

source_path = Path(__file__).resolve().parents[1] / "Jev_Clipboard_Guard.cherri"
s = source_path.read_text(encoding="utf-8")
checks = {
    "official TypeSafe API endpoint is the default": 'https://api.typesafe.ai/v1/systemone' in s,
    "API endpoint remains editable": '@apiUrl =' in s,
    "API key placeholder stays in source (filled in by hand after import)": (
        '@apiKey = "REPLACE_WITH_JEV_API_KEY"' in s
        and '#question jevApiKey' not in s
    ),
    "unconfigured API key stops before any network request": (
        s.index('if @apiKey == "REPLACE_WITH_JEV_API_KEY"') < s.index('@response = jsonRequest')
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
