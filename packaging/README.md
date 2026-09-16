# Building Whisper Dictate

Requires macOS 13+, Python 3.10+, and Apple's command-line tools. Build on the
architecture you want to distribute (the initial build is Apple Silicon).

```sh
python3 -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements-build.txt
./scripts/build.sh
```

Outputs:

- `dist/Whisper Dictate.app`: bundled Python, PortAudio, Whisper, and native UI
- `dist/Whisper Dictate.dmg`: compressed installer with an Applications shortcut

Whisper models are intentionally outside the installer. Existing models are reused;
new users download a model from Settings. No Python installation is needed to run
the app. The app requires macOS 13 or later for native login-item management.

The icon source is `scripts/make_icon.py`; regenerate with the build Python.

## Signing and distribution

The default build is ad-hoc signed for local use. It is not notarized. A release
for other users should use a Developer ID Application certificate:

```sh
CODESIGN_IDENTITY='Developer ID Application: Your Name (TEAMID)' ./scripts/build.sh
xcrun notarytool submit 'dist/Whisper Dictate.dmg' --keychain-profile YOUR_PROFILE --wait
xcrun stapler staple 'dist/Whisper Dictate.dmg'
```

Create the keychain profile using your own Apple Developer credentials. Keep the
bundle identifier stable once people begin granting microphone and Accessibility
permissions. A different signature or app identity may require granting permissions
again. The MIT license from the upstream project is included in the app and DMG.

Build design follows [PyInstaller's macOS packaging documentation](https://pyinstaller.org/en/stable/feature-notes.html).
Launch at login uses [Apple's SMAppService](https://developer.apple.com/documentation/servicemanagement/smappservice/mainapp?language=objc),
so macOS manages the login item and any required approval.

## Validation

```sh
.build-venv/bin/python -m unittest discover -s tests -v
codesign --verify --deep --strict 'dist/Whisper Dictate.app'
hdiutil verify 'dist/Whisper Dictate.dmg'
open 'dist/Whisper Dictate.app' --args --settings
```

Before release, also test on a clean Mac: first model download, microphone and
Accessibility prompts, dictation into another app, login item registration and a
new login, and Gatekeeper with the notarized downloaded DMG. Automated tests use
synthetic audio and mocked system services; they do not grant permissions or reboot.
