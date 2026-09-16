# Build on macOS for the current architecture.
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH).parent
whisper_data, whisper_binaries, whisper_imports = collect_all('pywhispercpp')
a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=whisper_binaries,
    datas=whisper_data + [(str(root / 'LICENSE'), '.'),
                          (str(root / 'assets/status'), 'assets/status')] + copy_metadata('pywhispercpp'),
    hiddenimports=whisper_imports + ['ServiceManagement', 'AppKit', 'Foundation', 'Quartz',
                                   '_sounddevice_data', '_cffi_backend'],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'IPython', 'pytest'],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Whisper Dictate',
          console=False, argv_emulation=False,
          entitlements_file=str(root / 'packaging/entitlements.plist'),
          codesign_identity=os.environ.get('CODESIGN_IDENTITY'))
coll = COLLECT(exe, a.binaries, a.datas, name='Whisper Dictate')
app = BUNDLE(coll, name='Whisper Dictate.app', bundle_identifier='se.hinken.whisperdictate',
             icon=str(root / 'assets/WhisperDictate.icns'),
             info_plist={
                 'CFBundleDisplayName': 'Whisper Dictate',
                 'CFBundleShortVersionString': '0.1.0',
                 'CFBundleVersion': '1',
                 'LSMinimumSystemVersion': '13.0',
                 'LSUIElement': True,
                 'NSMicrophoneUsageDescription': 'Whisper Dictate uses your microphone to transcribe speech locally on your Mac.',
                 'NSHighResolutionCapable': True,
             })
