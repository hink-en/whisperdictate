import unittest
from unittest.mock import Mock, patch

import main
from src.text_injector import TextInjector


class TextOutputTests(unittest.TestCase):
    def test_missing_accessibility_prevents_silent_recording(self):
        app = main.MacHyprwhspr.__new__(main.MacHyprwhspr)
        app.model_busy = False
        app.transcriber = Mock(ready=True)
        app.audio = Mock()
        app.alert = Mock()
        app._update_status = Mock()
        with patch('main.keyboard_permissions', return_value=(False, True)):
            app._start_recording()
        app.audio.start_recording.assert_not_called()
        app.alert.assert_called_once()
        self.assertIn('Accessibility', app.alert.call_args.args[0])

    def test_permission_revocation_does_not_report_success_or_copy(self):
        with patch('src.text_injector.AXIsProcessTrusted', return_value=False), \
                patch('src.text_injector.pyperclip.copy') as copy, \
                patch.object(TextInjector, '_simulate_paste') as paste:
            self.assertFalse(TextInjector().inject('Hello'))
        copy.assert_not_called()
        paste.assert_not_called()

    def test_authorized_output_pastes_preprocessed_text(self):
        with patch('src.text_injector.AXIsProcessTrusted', return_value=True), \
                patch('src.text_injector.pyperclip.copy') as copy, \
                patch.object(TextInjector, '_simulate_paste') as paste:
            self.assertTrue(TextInjector().inject('Hello'))
        copy.assert_called_once_with('Hello ')
        paste.assert_called_once()


if __name__ == '__main__':
    unittest.main()
