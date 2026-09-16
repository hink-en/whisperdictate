import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main
from src import shortcuts


class ShortcutTests(unittest.TestCase):
    def test_missing_global_access_does_not_create_a_local_only_listener(self):
        app = main.MacHyprwhspr.__new__(main.MacHyprwhspr)
        app.config = SimpleNamespace(get=lambda key, default=None: default)
        app.shortcuts = app.f5_shortcut = None
        app._update_status = Mock()
        with patch('main.keyboard_permissions', return_value=(True, False)), \
                patch('main.DoubleTapShortcut') as double, patch('main.SingleKeyShortcut') as single:
            self.assertFalse(app._setup_shortcuts())
            double.assert_not_called()
            single.assert_not_called()
        self.assertIn('Input Monitoring', app._shortcut_issue)

    def test_granted_permissions_start_both_listeners(self):
        app = main.MacHyprwhspr.__new__(main.MacHyprwhspr)
        app.config = SimpleNamespace(get=lambda key, default=None: default)
        app.shortcuts = app.f5_shortcut = None
        app._update_status = Mock()
        with patch('main.keyboard_permissions', return_value=(True, True)), \
                patch('main.DoubleTapShortcut') as double, patch('main.SingleKeyShortcut') as single:
            double.return_value.start.return_value = True
            single.return_value.start.return_value = True
            self.assertTrue(app._setup_shortcuts())
            double.return_value.start.assert_called_once()
            single.return_value.start.assert_called_once()
        self.assertEqual(app._shortcut_issue, '')

    def test_listener_recovers_from_timeout(self):
        for listener in (shortcuts.DoubleTapShortcut(), shortcuts.SingleKeyShortcut(96)):
            with self.subTest(listener=type(listener).__name__):
                listener._tap = object()
                with patch('src.shortcuts.CGEventTapEnable') as enable:
                    listener._event_callback(None, shortcuts.Quartz.kCGEventTapDisabledByTimeout, None, None)
                    enable.assert_called_once_with(listener._tap, True)

    def test_double_shift_calls_callback_once(self):
        callback = Mock()
        listener = shortcuts.DoubleTapShortcut(callback=callback)
        def run_inline(**kwargs):
            return SimpleNamespace(start=kwargs['target'])
        with patch('src.shortcuts.CGEventGetIntegerValueField', return_value=56), \
                patch('src.shortcuts.CGEventGetFlags', side_effect=[shortcuts.kCGEventFlagMaskShift, 0] * 2), \
                patch('time.time', side_effect=[100, 100.2]), \
                patch('src.shortcuts.threading.Thread', side_effect=run_inline):
            for _ in range(4):
                listener._event_callback(None, shortcuts.kCGEventFlagsChanged, object(), None)
        callback.assert_called_once()


if __name__ == '__main__':
    unittest.main()
