#!/usr/bin/env python3
"""Sign a Cherri-generated XML shortcut through RoutineHub's HubSign endpoint.

Only built-in Python modules are used. Never send personalized API credentials
inside a compiled Shortcut: the public source must retain placeholder values.
"""
import json
import plistlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://hubsign.routinehub.services/sign"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: sign_hubsign.py INPUT_UNSIGNED_PLIST OUTPUT_SIGNED_SHORTCUT", file=sys.stderr)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    parsed = plistlib.loads(raw)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("WFWorkflowActions"), list):
        raise ValueError("not a valid unsigned Shortcut workflow")
    if b"REPLACE_WITH_JEV_API_KEY" not in raw:
        raise ValueError("unsigned payload lacks expected safe API key placeholder")
    if not raw.startswith(b"<?xml"):
        raise ValueError("HubSign requires XML plist, not binary plist")
    data = json.dumps(
        {"shortcutName": "Jev Clipboard Guard", "shortcut": raw.decode("utf-8")},
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/octet-stream",
        "Origin": "https://routinehub.co",
        "Referer": "https://routinehub.co/",
        "User-Agent": "Mozilla/5.0 (compatible; JevClipboardGuard-GitHubActions/1.0)",
    }
    request = urllib.request.Request(ENDPOINT, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=75) as response:
            signed = response.read(10_000_000)
            print(f"HubSign: status={response.status}, response_bytes={len(signed)}")
    except urllib.error.HTTPError as exc:
        detail = exc.read(400).decode("utf-8", errors="replace")
        raise RuntimeError(f"HubSign HTTP {exc.code}: {detail!r}") from exc
    if not signed.startswith(b"AEA1") or len(signed) < 1000:
        raise ValueError(f"HubSign returned non-signed content ({len(signed)} bytes; prefix={signed[:8]!r})")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(signed)
    print(f"Successfully produced signed Shortcut: {dst}, {len(signed)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
