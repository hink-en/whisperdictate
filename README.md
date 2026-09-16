# Whisper Dictate

A fast, local speech-to-text dictation app for macOS. Double-tap Shift, speak, and watch your words appear in real-time.

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

- **Double-tap Shift** to start/stop - no awkward key combos
- **Live transcription** - text appears as you pause speaking
- **100% local** - runs entirely on your Mac using Whisper, no cloud/API needed
- **Works everywhere** - types into any app (Slack, VS Code, browser, etc.)
- **Menu bar app** - unobtrusive, always accessible

## Demo

```
Double-tap Shift → 🔴 Recording...
"Hello world, this is a test" → ⏳ Processing...
→ Text appears in your active app: "Hello world, this is a test"
Keep speaking... (transcribes after each pause)
Double-tap Shift → 🎤 Stopped
```

## Install the macOS app

1. Open `Whisper Dictate.dmg` and drag **Whisper Dictate** into **Applications**.
2. Quit the old Terminal-launched copy, then open **Whisper Dictate**.
3. Click the microphone in the menu bar → **Settings…**.
4. Select a model and click **Download & Use Model** if needed. Existing models
   and `~/.config/whisper-dictate/config.json` are reused automatically.
5. Grant microphone access when recording starts. For shortcuts and pasting,
   enable **Whisper Dictate** under System Settings → Privacy & Security →
   Accessibility and Input Monitoring. The app reconnects after access changes;
   reopen it if macOS requests it. **Settings → Permissions…** reports access for
   the running build. If a switch is on but access is denied, toggle it off and on
   or remove the stale entry and add the app from Applications again.
6. Enable **Launch at login** in Settings to keep the app available after signing in.
   If macOS requests approval, allow it under General → Login Items & Extensions.

The app requires macOS 13 or later. It stays in the menu bar and does not need a
Terminal window or a separate Python installation. It starts idle at login;
recording only begins when you use a shortcut or Start Recording.

The initial build is for Apple Silicon and is ad-hoc signed for local use. Public
distribution requires Developer ID signing and notarization; see
[packaging instructions](packaging/README.md).

### Settings

- **Language:** English, Svenska, or Auto-detect; also accessible directly in the menu.
- **Model:** download and activate multilingual models without editing JSON.
  Model changes stop recording and take effect when loading finishes.
- **Microphone:** system default or a specific input device.
- **Shortcuts:** independently enable double-tap Shift and F5.
- **Press Return:** optionally submit text after each transcription.
- **Launch at login:** register the installed app with macOS.

Click **Save Settings** to save language, microphone, and shortcut preferences.
**Download & Use Model** and **Launch at login** apply separately.
Choose **Svenska** to force Swedish. English-only models such as `small.en` do not
support Swedish; use a multilingual model such as `small` or `medium` instead.
Settings are stored automatically and survive restarting the app.

### Run from source

```sh
./setup.sh
./run.sh
```

To build the app and DMG, see [packaging/README.md](packaging/README.md).
The original command-line mode remains available with `python cli.py` from the
virtual environment. Use **Open Logs** in the app menu for packaged-app diagnostics.

## How It Works

1. **Voice Activity Detection (VAD)** monitors your speech
2. When you pause (~0.7s of silence), the audio chunk is sent to Whisper
3. Transcribed text is immediately typed into your active application
4. Recording continues until you double-tap Shift again

## Configuration

The Settings window manages common options. Advanced options remain in
`~/.config/whisper-dictate/config.json`:

```json
{
  "model": "small",
  "auto_submit": false
}
```

### Options

| Setting | Description | Default |
|---------|-------------|---------|
| `model` | Whisper model size | `small` |
| `language` | `en` (English), `sv` (Swedish), or `auto`/`null` (auto-detect) | `null` |
| `auto_submit` | Press Enter after each transcription | `false` |

### Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny.en` | 75 MB | Fastest | Good |
| `base.en` | 142 MB | Fast | Better |
| `small.en` | 466 MB | Medium | Great |
| `medium.en` | 1.5 GB | Slow | Excellent |

Download additional models:
```python
from pywhispercpp.model import Model
Model('small.en')  # Downloads automatically
```

## VAD Tuning

Adjust in `src/audio.py`:

```python
self.silence_threshold = 0.01   # Lower = more sensitive to silence
self.silence_duration = 0.7     # Seconds of silence before transcribing
self.min_chunk_duration = 0.3   # Minimum audio length to process
```

## Troubleshooting

### "Failed to create event tap"
Grant Accessibility permission in System Preferences → Privacy & Security → Accessibility

### "No microphone found"
Grant Microphone permission in System Preferences → Privacy & Security → Microphone

### Double-tap not detected
- Make sure you're tapping Shift quickly (within 0.4 seconds)
- Don't hold Shift - just tap twice
- Check that no other modifiers (Cmd, Alt, Ctrl) are pressed

### Model not found
```bash
python -c "from pywhispercpp.model import Model; Model('base.en')"
```

## Credits

This project is a macOS port inspired by [hyprwhspr](https://github.com/goodroot/hyprwhspr) - a speech-to-text dictation tool for Linux/Hyprland.

Key differences from the original:
- macOS-native using CoreGraphics (CGEvent) instead of evdev/ydotool
- Double-tap Shift shortcut instead of Super+Alt+D
- Live streaming VAD instead of record-then-transcribe
- Menu bar app using rumps instead of Waybar integration

## Tech Stack

- **[pywhispercpp](https://github.com/aarnphm/pywhispercpp)** - Whisper inference via whisper.cpp
- **[rumps](https://github.com/jaredks/rumps)** - macOS menu bar apps
- **[pyobjc](https://pyobjc.readthedocs.io/)** - macOS framework bindings
- **[sounddevice](https://python-sounddevice.readthedocs.io/)** - Audio capture

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

PRs welcome! Some ideas:
- [ ] Configurable shortcut key
- [ ] Per-app language settings
- [ ] Audio feedback (beep on start/stop)
- [ ] Native macOS app bundle (.app)
