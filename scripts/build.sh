#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.build-venv/bin/python}"
export PYINSTALLER_CONFIG_DIR="$PWD/build/pyinstaller-cache"
"$PYTHON" -m PyInstaller --noconfirm --clean packaging/WhisperDictate.spec
/usr/bin/codesign --verify --deep --strict 'dist/Whisper Dictate.app'
STAGING=$(mktemp -d "$PWD/build/dmg.XXXXXX")
trap 'rm -rf "$STAGING"' EXIT
/usr/bin/ditto 'dist/Whisper Dictate.app' "$STAGING/Whisper Dictate.app"
ln -s /Applications "$STAGING/Applications"
cp LICENSE "$STAGING/LICENSE.txt"
/usr/bin/hdiutil create -volname 'Whisper Dictate' -srcfolder "$STAGING" -ov -format UDZO 'dist/Whisper Dictate.dmg'
echo 'Built dist/Whisper Dictate.app and dist/Whisper Dictate.dmg'
