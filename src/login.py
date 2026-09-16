"""Use macOS login item management for the installed application."""
import sys
from pathlib import Path


def available():
    return bool(getattr(sys, 'frozen', False)) and '.app/Contents/MacOS/' in sys.executable


def _service():
    from ServiceManagement import SMAppService
    return SMAppService.mainAppService()


def status():
    if not available():
        return 'Install the app in Applications to enable launch at login.'
    return {0: 'Off', 1: 'On', 2: 'Approval needed in System Settings',
            3: 'Not registered'}.get(_service().status(), 'Unavailable')


def enabled():
    return available() and _service().status() in (1, 2)


def set_enabled(value):
    if not available():
        raise RuntimeError('Launch at login is available in the packaged app.')
    bundle = Path(sys.executable).parents[2]
    applications = [Path('/Applications'), Path.home() / 'Applications']
    if value and bundle.parent not in applications:
        raise RuntimeError('Move Whisper Dictate to Applications before enabling launch at login.')
    service = _service()
    if value == enabled():
        return
    success, error = service.registerAndReturnError_(None) if value else service.unregisterAndReturnError_(None)
    if not success:
        raise RuntimeError(str(error.localizedDescription()) if error else 'Could not update login item.')
