import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.config import Config
from src.models import download_model
from src import login
import main


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with patch('src.config.Path.home', return_value=Path(self.directory.name)):
            self.config = Config()

    def test_atomic_save_failure_preserves_previous_file(self):
        old = self.config.config_file.read_bytes()
        self.config.set('language', 'sv')
        with patch('src.config.os.replace', side_effect=OSError('disk error')):
            self.assertFalse(self.config.save())
        self.assertEqual(self.config.config_file.read_bytes(), old)
        self.assertEqual(list(self.config.config_dir.iterdir()), [self.config.config_file])

    def test_failed_settings_save_rolls_back_unknown_and_known_settings(self):
        app = main.MacHyprwhspr.__new__(main.MacHyprwhspr)
        app.config = self.config
        app.is_recording = False
        app.alert = Mock()
        app._setup_shortcuts = Mock()
        original = self.config.config.copy()
        with patch.object(self.config, 'save', return_value=False):
            self.assertFalse(app.save_settings({'language': 'sv', 'microphone': 'Test mic'}))
        self.assertEqual(self.config.config, original)
        app._setup_shortcuts.assert_not_called()

    def test_model_swap_occurs_only_after_successful_save(self):
        app = main.MacHyprwhspr.__new__(main.MacHyprwhspr)
        app.config = self.config
        original = app.transcriber = Mock()
        app._model_failed = Mock()
        app._model_progress = Mock()
        app.settings = None
        candidate = Mock()
        with patch.object(self.config, 'save', return_value=False):
            app._model_loaded('medium', candidate)
        self.assertIs(app.transcriber, original)
        self.assertEqual(self.config.get('model'), 'small')
        app._model_loaded('medium', candidate)
        self.assertIs(app.transcriber, candidate)
        self.assertEqual(json.loads(self.config.config_file.read_text())['model'], 'medium')

    def test_download_failure_does_not_publish_partial_model(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.headers = {'content-length': '100'}
        response.iter_content.return_value = [b'lmggpartial']
        directory = Path(self.directory.name) / 'models'
        with patch('src.models.requests.get', return_value=response):
            with self.assertRaises(ValueError):
                download_model('tiny', directory, Mock())
        self.assertEqual(list(directory.iterdir()), [])

    def test_complete_download_publishes_model(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.headers = {'content-length': '8'}
        response.iter_content.return_value = [b'lmggdata']
        directory = Path(self.directory.name) / 'models'
        with patch('src.models.requests.get', return_value=response):
            result = download_model('tiny', directory, Mock())
        self.assertEqual(result.read_bytes(), b'lmggdata')
        self.assertEqual(list(directory.iterdir()), [result])

    def test_login_registration_reports_os_errors(self):
        service = Mock()
        service.status.return_value = 0
        service.registerAndReturnError_.return_value = (False, SimpleNamespace(localizedDescription=lambda: 'Denied'))
        with patch.object(login, 'available', return_value=True), \
                patch.object(login, '_service', return_value=service), \
                patch('src.login.sys.executable', '/Applications/Whisper Dictate.app/Contents/MacOS/Whisper Dictate'):
            with self.assertRaisesRegex(RuntimeError, 'Denied'):
                login.set_enabled(True)


if __name__ == '__main__':
    unittest.main()
