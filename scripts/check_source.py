#!/usr/bin/env python3
"""Static safety/contract checks for the Cherri source (not a runtime test)."""
from pathlib import Path
import sys

source_path = Path(__file__).resolve().parents[1] / "Jev_Clipboard_Guard.cherri"
s = source_path.read_text(encoding="utf-8")
checks = {
    "official TypeSafe API endpoint is the default": 'https://api.typesafe.ai/v1/systemone' in s,
    "API endpoint remains editable": '@apiUrl =' in s,
    "API key is a placeholder, not a real credential": '@apiKey = "REPLACE_WITH_JEV_API_KEY"' in s,
    "Jev request includes current model alias and typed choice": '"model": "jev-latest"' in s and '"type": "choice"' in s,
    "clipboard is overwritten with a space, not an empty string": 'setClipboard(" ", true)' in s,
    "sensitive content is checked locally before network request": s.index('@localRisk = matchText') < s.index('@response = jsonRequest'),
    "share payload is handled before sending ordinary text to Jev": s.index('if @shareType != ""') < s.index('@response = jsonRequest'),
    "shopping-consumer allowlist exists for cross-app product shares": '@trustedShoppingConsumer = matchText' in s,
    "uncertain Jev decision prompts the user": 'ASK_USER' in s and 'const userChoice = menu' in s,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
if failed:
    sys.exit(1)
print(f"\n{len(checks)} static checks passed. This does not replace Cherri compilation or iPhone runtime testing.")
