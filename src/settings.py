"""Native AppKit settings window for the menu bar app."""
import AppKit as AK
import objc
from Foundation import NSObject, NSURL

from src import login
from src.models import MODELS, find_model
from src.permissions import keyboard_permissions


class SettingsWindow(NSObject):
    def initWithApp_(self, app):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        self.app = app
        self.window = AK.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((0, 0), (580, 630)),
            AK.NSWindowStyleMaskTitled | AK.NSWindowStyleMaskClosable | AK.NSWindowStyleMaskMiniaturizable,
            AK.NSBackingStoreBuffered, False)
        self.window.setTitle_('Whisper Dictate — Settings')
        self.window.setReleasedWhenClosed_(False)
        self.window.center()
        self.content = self.window.contentView()
        self.label('Whisper Dictate', 28, 573, 520, 30, 24)
        self.label('Local dictation in English and Swedish', 28, 545, 520, 24, 13)
        self.label('Language', 28, 495, 130, 24)
        self.language = self.popup(165, 493, 385)
        self.label('Whisper model', 28, 447, 130, 24)
        self.model = self.popup(165, 445, 385)
        self.model.setTarget_(self)
        self.model.setAction_('modelChanged:')
        self.label('Choose a multilingual model for Swedish. Larger models use more memory.',
                   165, 401, 385, 40, 11)
        self.model_button = self.button('Download & Use Model', 165, 361, 245, 'useModel:')
        self.progress = AK.NSProgressIndicator.alloc().initWithFrame_(((165, 342), (385, 12)))
        self.progress.setIndeterminate_(False)
        self.progress.setMinValue_(0)
        self.progress.setMaxValue_(100)
        self.content.addSubview_(self.progress)
        self.model_status = self.label('', 165, 297, 385, 40, 11)
        self.label('Microphone', 28, 256, 130, 24)
        self.microphone = self.popup(165, 254, 385)
        self.double_shift = self.checkbox('Double-tap Shift to start / stop', 165, 216)
        self.f5 = self.checkbox('F5 to start / stop', 165, 186)
        self.auto_submit = self.checkbox('Press Return after each transcription', 165, 156)
        self.launch = self.checkbox('Launch at login', 165, 126)
        self.launch.setTarget_(self)
        self.launch.setAction_('toggleLogin:')
        self.login_status = self.label('', 165, 96, 385, 25, 11)
        self.button('Permissions…', 28, 35, 140, 'permissions:')
        self.save_button = self.button('Save Settings', 385, 35, 165, 'save:')
        return self

    @objc.python_method
    def label(self, text, x, y, width, height, size=13):
        label = AK.NSTextField.alloc().initWithFrame_(((x, y), (width, height)))
        label.setStringValue_(text)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setFont_(AK.NSFont.systemFontOfSize_(size))
        label.setTextColor_(AK.NSColor.labelColor())
        self.content.addSubview_(label)
        return label

    @objc.python_method
    def popup(self, x, y, width):
        control = AK.NSPopUpButton.alloc().initWithFrame_pullsDown_(((x, y), (width, 28)), False)
        self.content.addSubview_(control)
        return control

    @objc.python_method
    def button(self, title, x, y, width, action):
        button = AK.NSButton.alloc().initWithFrame_(((x, y), (width, 32)))
        button.setTitle_(title)
        button.setBezelStyle_(AK.NSBezelStyleRounded)
        button.setTarget_(self)
        button.setAction_(action)
        self.content.addSubview_(button)
        return button

    @objc.python_method
    def checkbox(self, title, x, y):
        button = self.button(title, x, y, 385, None)
        button.setButtonType_(AK.NSButtonTypeSwitch)
        return button

    @objc.python_method
    def show(self):
        self.refresh()
        AK.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        self.window.makeKeyAndOrderFront_(None)

    @objc.python_method
    def refresh(self):
        config = self.app.config
        language = config.get('language') or 'auto'
        self.languages = ['en', 'sv', 'auto']
        labels = ['English', 'Svenska', 'Auto-detect']
        if language not in self.languages:
            self.languages.append(language)
            labels.append(language)
        self.language.removeAllItems()
        self.language.addItemsWithTitles_(labels)
        self.language.selectItemAtIndex_(self.languages.index(language))
        self.models = list(MODELS)
        for model in self.app.transcriber.get_available_models() + [config.get('model')]:
            if model and model not in self.models:
                self.models.append(model)
        self.model.removeAllItems()
        self.model.addItemsWithTitles_([
            MODELS.get(model, model) + (' · downloaded' if find_model(model) else '')
            for model in self.models])
        self.model.selectItemAtIndex_(self.models.index(config.get('model')))
        self.microphones = [None]
        names = ['System default']
        for device in self.app.audio.list_devices():
            if device['name'] not in self.microphones:
                self.microphones.append(device['name'])
                names.append(device['name'])
        chosen = config.get('microphone')
        if chosen not in self.microphones:
            self.microphones.append(chosen)
            names.append(f'{chosen} (unavailable)')
        self.microphone.removeAllItems()
        self.microphone.addItemsWithTitles_(names)
        self.microphone.selectItemAtIndex_(self.microphones.index(chosen))
        self.double_shift.setState_(int(config.get('double_shift', True)))
        self.f5.setState_(int(config.get('f5_enabled', True)))
        self.auto_submit.setState_(int(config.get('auto_submit', False)))
        self.launch.setEnabled_(login.available())
        self.launch.setState_(int(login.enabled()))
        self.login_status.setStringValue_(login.status())
        self.modelChanged_(None)
        self.set_busy(self.app.model_busy)

    @objc.python_method
    def set_busy(self, busy):
        self.model_button.setEnabled_(not busy)
        self.model.setEnabled_(not busy)
        self.save_button.setEnabled_(not busy)
        if busy:
            self.model_status.setStringValue_(self.app.model_message)

    @objc.python_method
    def update_progress(self, text, percent=None):
        self.model_status.setStringValue_(text)
        self.progress.setIndeterminate_(percent is None)
        if percent is None:
            self.progress.startAnimation_(None)
        else:
            self.progress.stopAnimation_(None)
            self.progress.setDoubleValue_(percent)

    def modelChanged_(self, sender):
        name = self.models[self.model.indexOfSelectedItem()]
        installed = find_model(name)
        self.model_button.setTitle_('Use Model' if installed else 'Download & Use Model')
        if not self.app.model_busy:
            active = self.app.config.get('model')
            suffix = 'English only — choose a multilingual model for Swedish.' if '.en' in name else 'Supports Swedish and English.'
            self.model_status.setStringValue_(f'Active: {active}. {suffix}')

    def useModel_(self, sender):
        self.app.load_model(self.models[self.model.indexOfSelectedItem()], download=True)

    def save_(self, sender):
        values = {
            'language': self.languages[self.language.indexOfSelectedItem()],
            'microphone': self.microphones[self.microphone.indexOfSelectedItem()],
            'double_shift': bool(self.double_shift.state()),
            'f5_enabled': bool(self.f5.state()),
            'auto_submit': bool(self.auto_submit.state()),
        }
        if self.app.save_settings(values):
            self.window.orderOut_(None)

    def toggleLogin_(self, sender):
        try:
            login.set_enabled(bool(sender.state()))
        except Exception as error:
            self.app.alert('Launch at Login', str(error))
        self.launch.setState_(int(login.enabled()))
        self.login_status.setStringValue_(login.status())

    def permissions_(self, sender):
        accessibility, monitoring = keyboard_permissions()
        self.app.alert('Permissions',
                       f"Access for this running app:\n"
                       f"Accessibility: {'Allowed' if accessibility else 'Not allowed'}\n"
                       f"Input Monitoring: {'Allowed' if monitoring else 'Not allowed'}\n\n"
                       'Enable Whisper Dictate under both categories in Privacy & Security. '
                       'If a switch is already on but access is reported as not allowed, turn it off and on again. '
                       'If necessary, remove the old entry and add Whisper Dictate from Applications. '
                       'Reopen the app if macOS requests it. Microphone access is requested when recording starts.')
        AK.NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(
            'x-apple.systempreferences:com.apple.preference.security?' +
            ('Privacy_ListenEvent' if not monitoring else 'Privacy_Accessibility')))
