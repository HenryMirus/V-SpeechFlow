"""
Session-Manager für V-SpeechFlow

Extrahiert Session-Persistenz und Wiederherstellung aus MainWindow:
Startup-Config, Last-Session, Wizard-Settings.
"""

from pathlib import Path
from .translations import tr, set_language
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Verwaltet Session-Persistenz und Wiederherstellung.

    Args:
        main_window: Referenz auf das MainWindow
    """

    def __init__(self, main_window):
        self.mw = main_window

    @property
    def history_manager(self):
        return self.mw.history_manager

    def save_current_session(self):
        """Speichert die aktuelle Session in der History inkl. aktivem Profil."""
        current_profile = self.mw.profile_combo.currentText()
        unsaved_label = tr("profile_current_unsaved")
        if current_profile == unsaved_label:
            current_profile = None

        session_data = {
            'input_file': self.mw.input_panel.get_selected_file(),
            'model': self.mw.model_panel.get_selected_model(),
            'settings': self.mw.settings_panel.get_settings(),
            'diarization': self.mw.diarization_panel.get_settings(),
            'output': self.mw.output_panel.get_settings(),
        }

        self.history_manager.save_last_session(session_data, current_profile)
        logger.info(
            f"Session saved (Profile: {current_profile or 'None'})"
        )

    def load_startup_config(self):
        """
        Lädt Konfiguration beim App-Start:
        1. Wenn initial_config vorhanden und nicht angewendet -> Lade initial_config
        2. Sonst -> Lade last_session
        """
        initial_config = self.history_manager.get_initial_config()

        if initial_config:
            logger.info("First start after wizard - loading initial config")
            self.load_initial_config(initial_config)
            self.history_manager.mark_initial_config_applied()
        else:
            logger.info("Loading last session")
            self.load_last_session()

    def load_initial_config(self, config: dict):
        """
        Lädt die Initial-Konfiguration aus dem Installation-Wizard.
        Wird nur beim ersten Start nach Wizard-Abschluss aufgerufen.

        Args:
            config: Dictionary mit Wizard-Einstellungen
        """
        logger.info(f"Loading initial config from wizard, keys: {list(config.keys())}")

        # Model Panel
        if 'default_model' in config and config['default_model']:
            model_path = config['default_model']
            if Path(model_path).exists():
                self.mw.model_panel.set_model_path(model_path)
                logger.info(f"Model loaded from initial config: {model_path}")
            else:
                logger.warning(
                    f"Model from initial config not found: {model_path}"
                )

        # Settings Panel
        settings_data = {}
        if 'default_threads' in config:
            settings_data['threads'] = config['default_threads']
            logger.debug(f"Threads from config: {config['default_threads']}")
        if 'default_language' in config:
            settings_data['language'] = config['default_language']
            logger.debug(f"Language from config: {config['default_language']}")

        if settings_data:
            self.mw.settings_panel.set_settings(settings_data)
            logger.info(f"Settings loaded from initial config: {settings_data}")

        # Output Panel - auto_open_transcript
        if 'auto_open_transcript' in config:
            auto_open = config['auto_open_transcript']
            self.mw.output_panel.set_auto_open(auto_open)
            logger.info(f"Auto-open from initial config: {auto_open}")

        # Theme
        if 'preferred_theme' in config:
            theme = config['preferred_theme']
            self.mw.apply_theme(theme)
            if hasattr(self.mw, 'menu_manager') and self.mw.menu_manager.theme_toggle_switch:
                self.mw.menu_manager.update_theme_switch()
            logger.info(f"Theme from initial config: {theme}")

        logger.info("Initial config loaded successfully")
        self.mw.statusBar().showMessage(tr("loading_initial_config"), 3000)

    def load_last_session(self):
        """
        Lädt die letzte Session inkl. aktivem Profil.
        Wird bei jedem Start (außer erstem nach Wizard) aufgerufen.
        """
        last_session = self.history_manager.get_last_session()

        if not last_session:
            logger.info("No last session found")
            return

        profile_name = last_session.get('profile_name')
        session_data = last_session.get('data')

        if not session_data:
            logger.info("Session data is empty")
            return

        logger.info(
            f"Loading last session (Profile: {profile_name or 'None'})"
        )

        # Wenn ein Profil aktiv war, versuche es zu laden
        if profile_name and profile_name != '-- Aktuell (nicht gespeichert) --':
            profile_data = self.mw.profile_manager.get_profile(profile_name)
            if profile_data:
                logger.info(f"Loading profile from last session: {profile_name}")

                index = self.mw.profile_combo.findText(profile_name)
                if index >= 0:
                    self.mw.profile_combo.blockSignals(True)
                    self.mw.profile_combo.setCurrentIndex(index)
                    self.mw.profile_combo.blockSignals(False)

                if 'settings' in profile_data:
                    self.mw.settings_panel.set_settings(profile_data['settings'])
                if 'diarization' in profile_data:
                    self.mw.diarization_panel.set_settings(profile_data['diarization'])
                if 'output' in profile_data:
                    self.mw.output_panel.set_settings(profile_data['output'])

                self.mw.statusBar().showMessage(
                    tr("profile_restored", name=profile_name), 3000
                )
                return
            else:
                logger.warning(f"Profile '{profile_name}' not found, loading session data")

        # No profile or not found - load session data directly
        logger.debug("Loading session data directly")

        if 'input_file' in session_data:
            input_file = session_data['input_file']
            if input_file and Path(input_file).exists():
                self.mw.input_panel.set_file_path(input_file)
                logger.debug(f"Session input: {Path(input_file).name}")

        if 'model' in session_data:
            model_path = session_data['model']
            if model_path and Path(model_path).exists():
                self.mw.model_panel.set_model_path(model_path)
                logger.debug(f"Session model: {Path(model_path).name}")

        if 'settings' in session_data:
            self.mw.settings_panel.set_settings(session_data['settings'])
            logger.debug(
                f"Session settings: {session_data['settings'].get('threads')} threads"
            )

        if 'diarization' in session_data:
            self.mw.diarization_panel.set_settings(session_data['diarization'])
            enabled = session_data['diarization'].get('enabled')
            logger.debug(f"Session diarization: {'Yes' if enabled else 'No'}")

        if 'output' in session_data:
            self.mw.output_panel.set_settings(session_data['output'])
            logger.debug(f"Session output format: {session_data['output'].get('format')}")

        logger.info("Last session loaded successfully")
        self.mw.statusBar().showMessage(tr("loading_last_session"), 3000)

    def apply_wizard_settings(self, data: dict):
        """
        Wendet die Einstellungen aus dem Installation Wizard an.

        Args:
            data: Dict mit Wizard-Daten (model, token, language, theme, etc.)
        """
        logger.info("Applying wizard settings...")

        if data.get('default_model'):
            model_path = data['default_model']
            if Path(model_path).exists():
                self.mw.model_panel.set_model_path(model_path)
                logger.info(f"Model set from wizard: {model_path}")

        if data.get('hf_token'):
            self.mw.diarization_panel.set_hf_token(data['hf_token'])
            logger.info("HF Token set from wizard")

        if data.get('default_threads'):
            self.mw.settings_panel.set_threads(data['default_threads'])
            logger.info(f"Threads set from wizard: {data['default_threads']}")

        if data.get('ui_language'):
            language = data['ui_language']
            set_language(language)
            self.history_manager.save_user_preference('ui_language', language)
            logger.info(f"Language set from wizard: {language}")

        if data.get('preferred_theme'):
            theme = data['preferred_theme']
            if theme != self.mw.theme_manager.get_current_theme():
                self.mw.menu_manager.toggle_theme()

        if data.get('auto_open_transcript'):
            self.mw.output_panel.set_auto_open(True)

        logger.info("Wizard settings applied successfully")
