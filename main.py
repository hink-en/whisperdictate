#!/usr/bin/env python3
"""Whisper Dictate — standalone macOS menu bar dictation."""
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import rumps

from src.config import Config
from src.shortcuts import DoubleTapShortcut, SingleKeyShortcut
from src.audio import AudioCapture
from src.transcriber import Transcriber
from src.text_injector import TextInjector
from src.models import download_model, find_model
from src.permissions import keyboard_permissions

STATUS_ICONS = Path(__file__).resolve().parent / 'assets' / 'status'


def _log(message):
    print(f"{datetime.now():%H:%M:%S} {message}", flush=True)


class MacHyprwhspr(rumps.App):
    def __init__(self):
        super().__init__(name='Whisper Dictate', icon=str(STATUS_ICONS / 'idle.png'),
                         template=True, quit_button=None)
        self.config = Config()
        self.audio = AudioCapture()
        self.transcriber = Transcriber(self.config)
        self.injector = TextInjector(self.config)
        self.shortcuts = None
        self.f5_shortcut = None
        self.settings = None
        self._permissions = None
        self._permission_poll = 0
        self._shortcut_issue = ''
        self.is_recording = False
        self.model_busy = False
        self.model_message = ''
        self._session = 0
        self._events = queue.Queue()
        self._record_btn = rumps.MenuItem('Start Recording', callback=self.toggle_recording)
        self._status_item = rumps.MenuItem('Status: Starting…')
        self._language_menu = rumps.MenuItem('Language')
        self._language_items = {}
        for code, label in [('en', 'English'), ('sv', 'Svenska'), ('auto', 'Auto-detect')]:
            item = rumps.MenuItem(label, callback=self.select_language)
            self._language_items[code] = item
            self._language_menu.add(item)
        self._update_language_menu()
        self.menu = [self._record_btn, None, self._status_item, self._language_menu, None,
                     rumps.MenuItem('Settings…', callback=self.show_settings),
                     rumps.MenuItem('Open Logs', callback=self.open_logs),
                     rumps.MenuItem('Quit', callback=self.quit_app)]
        self._timer = rumps.Timer(self._drain_events, 0.1)
        self._timer.start()
        self._events.put(self._init_components)

    def _drain_events(self, _):
        # Cocoa controls must only be touched from the main thread.
        for _ in range(100):
            try:
                callback = self._events.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception as error:
                _log(f'[APP] {error}')
                self.alert('Whisper Dictate', str(error))
        # Reconnect automatically when macOS grants access to this running build.
        if self._permissions is not None and time.monotonic() >= self._permission_poll:
            self._permission_poll = time.monotonic() + 2
            if keyboard_permissions() != self._permissions:
                self._setup_shortcuts()
                if not self.is_recording and not self.model_busy:
                    self._update_status('Ready' if self.transcriber.ready else 'Choose a model in Settings')

    @staticmethod
    def alert(title, message):
        rumps.alert(title=title, message=message)

    def _init_components(self):
        shortcuts_ready = self._setup_shortcuts()
        if find_model(self.config.get('model')):
            self.load_model(self.config.get('model'))
        else:
            self._update_status('Choose a model in Settings')
            self.show_settings(None)
        if '--settings' in sys.argv or not shortcuts_ready:
            self.show_settings(None)

    def _setup_shortcuts(self):
        for shortcut in (self.shortcuts, self.f5_shortcut):
            if shortcut:
                shortcut.stop()
        self.shortcuts = None
        self.f5_shortcut = None
        self._permissions = keyboard_permissions()
        accessibility, monitoring = self._permissions
        _log(f'[PERMISSIONS] Accessibility={accessibility}, Input Monitoring={monitoring}')
        self._shortcut_issue = ''
        enabled = self.config.get('double_shift', True) or self.config.get('f5_enabled', True)
        if enabled and not monitoring:
            self._shortcut_issue = 'Input Monitoring required — see Settings → Permissions'
        elif not accessibility:
            self._shortcut_issue = 'Accessibility required for pasting — see Settings → Permissions'
        if enabled and not monitoring:
            self._update_status(self._shortcut_issue)
            return False
        failed = False
        if self.config.get('double_shift', True):
            self.shortcuts = DoubleTapShortcut(modifier='shift', callback=self._on_shortcut)
            failed |= not self.shortcuts.start()
        if self.config.get('f5_enabled', True):
            self.f5_shortcut = SingleKeyShortcut(keycode=96, callback=self._on_shortcut)
            failed |= not self.f5_shortcut.start()
        if failed:
            self._shortcut_issue = 'Keyboard listener unavailable — see Settings → Permissions'
        if self._shortcut_issue:
            self._update_status(self._shortcut_issue)
        return not failed and not self._shortcut_issue

    def _on_shortcut(self):
        self._events.put(lambda: self.toggle_recording(None))

    def toggle_recording(self, _):
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if self.model_busy:
            self._update_status(self.model_message)
            return
        if not self.transcriber.ready:
            self.show_settings(None)
            return
        if not keyboard_permissions()[0]:
            self._update_status('Accessibility required for pasting — see Settings → Permissions')
            self.alert('Accessibility Required',
                       'macOS is blocking text output. Enable Whisper Dictate in '
                       'System Settings → Privacy & Security → Accessibility. '
                       'If it is already enabled, toggle it off and on or remove '
                       'the old entry and add the app from Applications again. '
                       'Then try recording again.')
            return
        microphone = self.config.get('microphone')
        self.audio.device_id = None
        if microphone:
            matching = [device for device in self.audio.list_devices() if device['name'] == microphone]
            if not matching:
                self.alert('Microphone Unavailable', 'Choose an available microphone in Settings.')
                return
            self.audio.device_id = matching[0]['id']
        self._session += 1
        self.is_recording = True
        if self.audio.start_recording(vad_callback=self._on_speech_chunk):
            self._update_icon('recording')
            self._update_status('Listening…')
            self._record_btn.title = 'Stop Recording'
        else:
            self.is_recording = False
            self._update_status('Microphone unavailable')
            self.alert('Microphone', 'Allow Whisper Dictate microphone access in System Settings → Privacy & Security → Microphone, then try again.')

    def _on_speech_chunk(self, audio_data):
        if not self.is_recording:
            return
        session = self._session
        transcriber = self.transcriber
        self._events.put(lambda: self._update_icon('processing') if self.is_recording and session == self._session else None)
        text = transcriber.transcribe(audio_data)

        def finish():
            if not self.is_recording or session != self._session:
                return
            if text and text.strip():
                if self.injector.inject(text):
                    self._update_status('Listening…')
                else:
                    self._update_status('Text output failed — check Accessibility in Settings → Permissions and Open Logs')
            self._update_icon('recording')
        self._events.put(finish)

    def _stop_recording(self):
        self.is_recording = False
        self._session += 1
        self.audio.stop_recording()
        self._update_icon('idle')
        self._update_status('Stopped')
        self._record_btn.title = 'Start Recording'

    def _update_icon(self, state):
        if state not in ('idle', 'recording', 'processing'):
            state = 'idle'
        # Template rendering follows the light/dark menu bar while idle.
        self.template = state == 'idle'
        self.icon = str(STATUS_ICONS / f'{state}.png')

    def _update_status(self, status):
        if not self.is_recording and not self.model_busy and getattr(self, '_shortcut_issue', ''):
            status = self._shortcut_issue
        self._status_item.title = f'Status: {status}'

    def show_settings(self, _):
        if self.is_recording:
            self._stop_recording()
        if self.settings is None:
            from src.settings import SettingsWindow
            self.settings = SettingsWindow.alloc().initWithApp_(self)
        self.settings.show()

    def save_settings(self, values):
        if self.is_recording:
            self._stop_recording()
        previous = self.config.config.copy()
        self.config.config.update(values)
        if not self.config.save():
            self.config.config = previous
            self.alert('Settings Not Saved', f'Could not write {self.config.config_file}.')
            return False
        self._update_language_menu()
        if self._setup_shortcuts():
            self._update_status('Ready' if self.transcriber.ready else 'Choose a model in Settings')
        else:
            self.alert('Keyboard Access', 'Open Settings → Permissions to check Accessibility and Input Monitoring for this app. These permissions are needed for global shortcuts and pasting.')
        return True

    def _update_language_menu(self):
        language = self.config.get('language') or 'auto'
        for code, item in self._language_items.items():
            item.state = int(code == language)
        selected = self._language_items.get(language)
        self._language_menu.title = f'Language: {selected.title if selected else language}'

    def select_language(self, sender):
        language = next(code for code, item in self._language_items.items() if item is sender)
        previous = self.config.get('language')
        self.config.set('language', language)
        if not self.config.save():
            self.config.set('language', previous)
            self.alert('Language Not Saved', f'Could not save to {self.config.config_file}.')
            return
        self._update_language_menu()
        if self.settings and self.settings.window.isVisible():
            self.settings.refresh()

    def _model_progress(self, message, percent=None):
        self.model_message = message
        self._update_status(message)
        if self.settings:
            self.settings.update_progress(message, percent)

    def load_model(self, name, download=False):
        if self.model_busy:
            return
        if self.is_recording:
            self._stop_recording()
        self.model_busy = True
        self._model_progress(f'Preparing {name}…')
        if self.settings:
            self.settings.set_busy(True)

        def worker():
            try:
                if not find_model(name):
                    if not download:
                        raise RuntimeError('Choose a model to download in Settings.')
                    def progress(done, total):
                        message = f'Downloading {name}: {done / 1_000_000:.0f} MB'
                        percent = done * 100 / total if total else None
                        self._events.put(lambda: self._model_progress(message, percent))
                    download_model(name, self.config.get_models_dir(), progress)
                self._events.put(lambda: self._model_progress(f'Loading {name}…'))
                candidate = Transcriber(self.config)
                candidate.model_name = name
                if not candidate.initialize():
                    raise RuntimeError(f'Could not load {name}. Try another model or check Open Logs.')
                self._events.put(lambda: self._model_loaded(name, candidate))
            except Exception as error:
                message = str(error)
                self._events.put(lambda: self._model_failed(message))
        threading.Thread(target=worker, daemon=True).start()

    def _model_loaded(self, name, candidate):
        previous = self.config.get('model')
        self.config.set('model', name)
        if not self.config.save():
            self.config.set('model', previous)
            self._model_failed('Could not save the model setting; the previous model remains active.')
            return
        self.transcriber = candidate
        self.model_busy = False
        self._model_progress(f'Ready · {name}', 100)
        if self.settings:
            self.settings.refresh()

    def _model_failed(self, message):
        self.model_busy = False
        self._model_progress('Model change failed', 0)
        if self.settings:
            self.settings.set_busy(False)
        self.alert('Model Error', message)

    def open_logs(self, _):
        from AppKit import NSWorkspace
        directory = Path.home() / 'Library/Logs/Whisper Dictate'
        directory.mkdir(parents=True, exist_ok=True)
        NSWorkspace.sharedWorkspace().openFile_(str(directory))

    def quit_app(self, _):
        if self.is_recording:
            self._stop_recording()
        for shortcut in (self.shortcuts, self.f5_shortcut):
            if shortcut:
                shortcut.stop()
        rumps.quit_application()


def main():
    # The bundle has no terminal. Keep diagnostic output in a discoverable location.
    if getattr(sys, 'frozen', False):
        import os
        directory = Path.home() / 'Library/Logs/Whisper Dictate'
        directory.mkdir(parents=True, exist_ok=True)
        log = directory / 'app.log'
        if log.exists() and log.stat().st_size > 5_000_000:
            log.replace(directory / 'app.previous.log')
        output = open(log, 'a', buffering=1)
        os.dup2(output.fileno(), 1)
        os.dup2(output.fileno(), 2)
        sys.stdout = output
        sys.stderr = output
    _log('Whisper Dictate starting…')
    app = MacHyprwhspr()
    app.run()


if __name__ == '__main__':
    main()
