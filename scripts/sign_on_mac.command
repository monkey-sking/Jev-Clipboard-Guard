#!/bin/zsh
# Sign a CI-built Cherri Shortcut on a Mac signed into the user's own iCloud.
set -euo pipefail
DIR="${0:A:h}"
INPUT="$DIR/Jev_Clipboard_Guard_unsigned.shortcut"
OUTPUT="$DIR/Jev_Clipboard_Guard.shortcut"

if [[ ! -f "$INPUT" ]]; then
  echo "Missing unsigned shortcut: $INPUT"
  echo "Download and extract the GitHub Actions unsigned artifact first."
  exit 1
fi
if ! command -v shortcuts >/dev/null 2>&1; then
  echo "The Apple shortcuts CLI is unavailable. Use macOS 12+ with Shortcuts installed."
  exit 1
fi
echo "Signing with Apple's shortcuts CLI (an iCloud login is required)..."
shortcuts sign -i "$INPUT" -o "$OUTPUT" -m anyone
if [[ ! -s "$OUTPUT" ]]; then
  echo "Signing did not produce $OUTPUT"
  exit 1
fi
echo "Signed file: $OUTPUT"
echo "Transfer this file to your iPhone with AirDrop or iCloud Drive, open it in Files and add it to Shortcuts."
