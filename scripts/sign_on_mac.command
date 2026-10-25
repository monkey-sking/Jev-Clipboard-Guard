#!/bin/zsh
# Sign a Cherri-built Shortcut on a Mac signed into the user's own iCloud.
#
# Why this step exists: only Apple can produce a file Shortcuts will import.
# An unsigned plist (even renamed to .shortcut) is rejected with
#   「无法打开快捷指令 / 不支持导入未签名的快捷指令文件。」
# The `shortcuts sign` CLI needs an iCloud-logged-in Mac, so it cannot run on
# a GitHub-hosted runner. Third-party signing services (RoutineHub HubSign)
# stopped returning AEA1 payloads, so local signing is the supported path.
set -euo pipefail

DIR="${0:A:h}"
ROOT="${DIR:h}"

# The Cherri source declares `#define name ...`, and Cherri uses that value for
# the OUTPUT FILENAME only — it never writes WFWorkflowName into the plist.
# Shortcuts derives the imported shortcut's name from the file name, so this
# constant is effectively the user-visible product name. Keep the two in sync.
NAME="Jev 剪贴板守卫"
INPUT="$ROOT/${NAME}_unsigned.shortcut"
OUTPUT="$ROOT/${NAME}.shortcut"

# Accept whatever the build produced. Local Cherri builds land on
# "${NAME}_unsigned.shortcut"; the GitHub Actions artifact is an ASCII name with
# a .plist extension. Either is fine — `shortcuts sign` reads the plist itself.
if [[ ! -f "$INPUT" ]]; then
  candidates=( "$ROOT"/*_unsigned.shortcut(N) "$ROOT"/*_unsigned.plist(N) )
  if [[ ${#candidates[@]} -eq 1 ]]; then
    INPUT="${candidates[1]}"
    echo "Using unsigned input: ${INPUT:t}"
  elif [[ ${#candidates[@]} -gt 1 ]]; then
    echo "Found several unsigned inputs; rename the one you want to ${NAME}_unsigned.shortcut:"
    printf '  %s\n' "${candidates[@]:t}"
    exit 1
  fi
fi
if [[ ! -f "$INPUT" ]]; then
  echo "Missing unsigned shortcut: $INPUT"
  echo "Build it first:  cherri \"$ROOT/Jev_Clipboard_Guard.cherri\" --skip-sign --derive-uuids"
  exit 1
fi
if ! command -v shortcuts >/dev/null 2>&1; then
  echo "The Apple shortcuts CLI is unavailable. Use macOS 12+ with Shortcuts installed."
  exit 1
fi

# `shortcuts sign` intermittently fails with
#   Error: The operation couldn't be completed. (NSURLErrorDomain error 500.)
# when it talks to Apple's timestamp service. It is transient — retrying works.
echo "Signing with Apple's shortcuts CLI (an iCloud login is required)..."
SIGNED=0
for attempt in 1 2 3 4 5; do
  if shortcuts sign -m anyone -i "$INPUT" -o "$OUTPUT" 2>&1; then
    SIGNED=1
    break
  fi
  echo "Attempt $attempt failed (transient network error); retrying..."
  sleep 5
done
if [[ "$SIGNED" -ne 1 ]]; then
  echo "Signing failed after 5 attempts. Check your iCloud login and network."
  exit 1
fi

if [[ ! -s "$OUTPUT" ]]; then
  echo "Signing did not produce $OUTPUT"
  exit 1
fi
if [[ "$(head -c 4 "$OUTPUT")" != "AEA1" ]]; then
  echo "$OUTPUT is not an AEA1 archive — Shortcuts will refuse it."
  exit 1
fi

echo "Signed file: $OUTPUT  ($(stat -f%z "$OUTPUT") bytes)"
echo
echo "Next: AirDrop or iCloud-Drive this file to your iPhone, open it in Files,"
echo "tap 'Add Shortcut'. The shortcut will be named after the file: ${NAME}"
echo
echo "Note: right after importing, the Shortcuts library may still show"
echo "'0 actions' for the new entry. Quit and reopen Shortcuts to refresh it."