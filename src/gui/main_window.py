"""
Hauptfenster der PyQt6 GUI

Stellt die zentrale Benutzeroberfläche mit allen Panels zur Verfügung.
Delegiert Menü-, Profil-, Transkriptions- und Session-Logik an Controller-Klassen.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStatusBar,
    QScrollArea,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QComboBox,
    QSizePolicy,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtWidgets import QApplication
import sys
import os
import subprocess
from pathlib import Path
from .input_panel import InputPanel
from .model_panel import ModelPanel
from .settings_panel import SettingsPanel
from .diarization_panel import DiarizationPanel
from .output_panel import OutputPanel
from .workers import CLIWorker
from .profiles import ProfileManager
from .history import HistoryManager
from .batch_panel import BatchPanel
from .batch_window import BatchWindow, BatchWorker
from .theme import ThemeManager
from .progress_tracker import ProgressTracker
from .translations import tr, set_language, get_translation_manager
from .onboarding import OnboardingManager
from .menu_manager import MenuManager
from .profile_controller import ProfileController
from .transcription_controller import TranscriptionController
from .session_manager import SessionManager
from .constants import (
    MAIN_WINDOW_SIZE,
    STARTUP_CONFIG_DELAY_MS,
    MODEL_CHECK_DELAY_MS,
    COLOR_SUCCESS,
    COLOR_SUCCESS_DARK,
    COLOR_ERROR,
    COLOR_ERROR_DARK,
)
import logging
from datetime import datetime


class MainWindow(QMainWindow):
    """Hauptfenster der V-SpeechFlow GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(100, 100, *MAIN_WINDOW_SIZE)
        
        # Worker für CLI-Prozess
        self.cli_worker = None
        self.batch_worker = None
        self.is_processing = False
        self.is_batch_processing = False
        
        # Profile-Manager
        self.profile_manager = ProfileManager()
        
        # History-Manager (Singleton)
        self.history_manager = HistoryManager.get_instance()
        
        # Onboarding-Manager (wird erst beim Start initialisiert)
        self.onboarding_manager = None
        
        # Theme-Manager
        self.theme_manager = ThemeManager()
        
        # Time-Estimator für Fortschritts-Berechnung
        self.progress_tracker = ProgressTracker()

        # Diarization warning: nur einmal pro Transkription
        self.diarization_warning_shown = False
        
        # Sprache laden und setzen
        saved_language = self.history_manager.get_user_preference('ui_language', 'de')
        set_language(saved_language)
        
        # Logging einrichten
        self.setup_logging()
        self.log_info("V-SpeechFlow GUI started")
        self.log_info(f"UI Language: {saved_language}")
        
        # Theme anwenden
        self.apply_theme(self.theme_manager.get_current_theme())
        
        # === Controller erstellen ===
        self.menu_manager = MenuManager(self)
        self.profile_controller = ProfileController(self)
        self.transcription_controller = TranscriptionController(self)
        self.session_manager = SessionManager(self)
        
        # Menu-Bar erstellen (via MenuManager)
        self.menu_manager.create_menu_bar()
        
        # Zentral-Widget mit Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Linke Seite: Input + Settings (Scroll für lange Form)
        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Titel
        self.title_label = QLabel(tr("gui_title"))
        self.title_label.setStyleSheet("font-size: 19px; font-weight: bold;")
        left_layout.addWidget(self.title_label)
        
        # 1. Input Panel
        self.input_panel = InputPanel()
        self.input_panel.set_history_manager(self.history_manager)
        self.input_panel.file_selected.connect(self.on_file_selected)
        self.input_panel.recording_started.connect(self.on_recording_started)
        self.input_panel.recording_stopped.connect(self.on_recording_stopped)
        left_layout.addWidget(self.input_panel)
        
        # === Überschrift: Transkriptionseinstellungen ===
        left_layout.addSpacing(15)
        transcription_title = QLabel(tr("transcription_settings_title"))
        transcription_font = QFont()
        transcription_font.setPointSize(14)
        transcription_font.setBold(True)
        transcription_title.setFont(transcription_font)
        left_layout.addWidget(transcription_title)
        left_layout.addSpacing(5)
        
        # 2. Profile-Auswahl (in GroupBox)
        self.profile_group = QGroupBox("📁 " + tr("profile_label"))
        self.profile_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; font-size: 13pt; }")
        profile_group_layout = QVBoxLayout()
        
        profile_layout = QHBoxLayout()
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem(tr("profile_current_unsaved"))
        self.profile_controller.refresh_profile_list()
        self.profile_combo.currentTextChanged.connect(self.profile_controller.on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        
        btn_save_profile = QPushButton("💾")
        btn_save_profile.setToolTip(tr("profile_save_tooltip"))
        btn_save_profile.setFixedWidth(35)
        btn_save_profile.clicked.connect(self.profile_controller.save_current_profile)
        profile_layout.addWidget(btn_save_profile)
        
        btn_duplicate_profile = QPushButton("📋")
        btn_duplicate_profile.setToolTip(tr("profile_duplicate_tooltip"))
        btn_duplicate_profile.setFixedWidth(35)
        btn_duplicate_profile.clicked.connect(self.profile_controller.duplicate_selected_profile)
        profile_layout.addWidget(btn_duplicate_profile)
        
        btn_delete_profile = QPushButton("❌")
        btn_delete_profile.setToolTip(tr("profile_delete_tooltip"))
        btn_delete_profile.setFixedWidth(35)
        btn_delete_profile.clicked.connect(self.profile_controller.delete_selected_profile)
        profile_layout.addWidget(btn_delete_profile)
        
        # Mehr Options-Button (für Export/Import)
        btn_profile_menu = QPushButton("⋮")
        btn_profile_menu.setToolTip(tr("profile_menu_tooltip"))
        btn_profile_menu.setFixedWidth(35)
        btn_profile_menu.clicked.connect(self.profile_controller.show_profile_menu)
        profile_layout.addWidget(btn_profile_menu)
        
        profile_group_layout.addLayout(profile_layout)
        self.profile_group.setLayout(profile_group_layout)
        left_layout.addWidget(self.profile_group)
        
        # 3. Model Panel
        self.model_panel = ModelPanel()
        self.model_panel.model_selected.connect(self.on_model_selected)
        left_layout.addWidget(self.model_panel)
        
        # 4. Diarization Panel
        self.diarization_panel = DiarizationPanel()
        self.diarization_panel.diarization_changed.connect(self.on_diarization_changed)
        left_layout.addWidget(self.diarization_panel)
        
        # 5. Output Panel
        self.output_panel = OutputPanel()
        self.output_panel.output_changed.connect(self.on_output_changed)
        left_layout.addWidget(self.output_panel)
        
        # 6. Settings Panel (Weitere Einstellungen / Verarbeitungsoptionen)
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.on_settings_changed)
        left_layout.addWidget(self.settings_panel)
        
        left_layout.addStretch()
        self.left_scroll.setWidget(left_panel)
        main_layout.addWidget(self.left_scroll, 2)  # 2/3 der Breite
        
        # Rechte Seite: Output Preview + Control Buttons
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.output_title = QLabel(tr("output_preview_title"))
        self.output_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(self.output_title)
        
        # Output Text Area mit QTextEdit für Live-Output
        self.output_preview = QTextEdit()
        self.output_preview.setReadOnly(True)
        self.output_preview.setPlaceholderText(tr("output_preview_placeholder"))
        self.output_preview.setStyleSheet(
            "color: #333; background-color: #f5f5f5; padding: 10px; "
            "border-radius: 4px; font-family: 'Consolas', 'Monaco', monospace; font-size: 10pt;"
        )
        right_layout.addWidget(self.output_preview)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("progress_format"))
        right_layout.addWidget(self.progress_bar)
        
        # ETA Label
        self.eta_label = QLabel("")
        self.eta_label.setVisible(False)
        self.eta_label.setStyleSheet("color: gray; font-size: 11px; text-align: center;")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.eta_label)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton(tr("start_transcription_button"))
        self.btn_start.setStyleSheet(
            f"background-color: {COLOR_SUCCESS}; color: white; font-weight: bold; padding: 8px;"
        )
        self.btn_start.setToolTip(tr("start_transcription_tooltip"))
        self.btn_start.clicked.connect(self.transcription_controller.start_transcription)
        button_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton(tr("stop_button"))
        self.btn_stop.setStyleSheet(
            f"background-color: {COLOR_ERROR}; color: white; font-weight: bold; padding: 8px;"
        )
        self.btn_stop.setEnabled(False)
        self.btn_stop.setToolTip(tr("stop_transcription_tooltip"))
        self.btn_stop.clicked.connect(self.transcription_controller.stop_transcription)
        button_layout.addWidget(self.btn_stop)
        
        right_layout.addLayout(button_layout)
        
        main_layout.addWidget(right_panel, 1)  # 1/3 der Breite
        
        # Status Bar
        self.statusBar().showMessage(tr("status_ready"))
        
        # Tastenkürzel einrichten
        self.setup_shortcuts()
        
        # Progress-Update Timer (für kontinuierliches ETA-Update)
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(
            self.transcription_controller.update_progress_display
        )
        # Timer wird nur während Verarbeitung aktiviert
        
        # Config beim Start laden (initial_config oder last_session)
        QTimer.singleShot(STARTUP_CONFIG_DELAY_MS, self.session_manager.load_startup_config)
        
        # Model-Update-Check beim Start (verzögert)
        QTimer.singleShot(MODEL_CHECK_DELAY_MS, self.check_model_updates)
        
        # UI-Texte mit korrekten Übersetzungen initialisieren
        QTimer.singleShot(STARTUP_CONFIG_DELAY_MS, self.refresh_ui)
    
    # ===== Signal-Handler (dünne Schicht) =====
    
    def on_file_selected(self, file_path: str):
        """Wird aufgerufen wenn eine Datei ausgewählt wird."""
        self.statusBar().showMessage(f"✓ {Path(file_path).name}")
    
    def on_model_selected(self, model_path: str):
        """Wird aufgerufen wenn ein Modell ausgewählt wird."""
        self.statusBar().showMessage(f"Modell ausgewählt: {model_path}")
    
    def on_settings_changed(self, settings: dict):
        """Wird aufgerufen wenn sich Settings ändern."""
        threads = settings.get('threads', 6)
        lang = settings.get('language', 'de')
        translate = "✓" if settings.get('translate') else "✗"
        self.statusBar().showMessage(
            f"Threads: {threads} | Sprache: {lang} | Translation: {translate}"
        )
    
    def on_diarization_changed(self, settings: dict):
        """Wird aufgerufen wenn sich Diarization Settings ändern."""
        self.maybe_show_diarization_warning(settings)
        if settings.get('enabled'):
            mode = settings.get('mode', 'exact')
            if mode == 'exact':
                num = settings.get('num_speakers', 2)
                self.statusBar().showMessage(f"Diarization: {num} Sprecher (Exakt)")
            else:
                min_s = settings.get('min_speakers', 1)
                max_s = settings.get('max_speakers', 5)
                self.statusBar().showMessage(f"Diarization: {min_s}-{max_s} Sprecher (Auto)")
        else:
            self.statusBar().showMessage("Diarization: Deaktiviert")

    def maybe_show_diarization_warning(self, settings: dict):
        """Zeigt einmalig eine Warnung bei >10 Sprechern (pro Transkription)."""
        if self.diarization_warning_shown:
            return
        if not settings.get('enabled'):
            return

        if settings.get('mode') == 'exact':
            speaker_count = settings.get('num_speakers')
        else:
            speaker_count = settings.get('max_speakers')

        if speaker_count and speaker_count > 10:
            QMessageBox.information(
                self,
                tr("diarization_warning_title"),
                tr("diarization_warning_msg")
            )
            self.diarization_warning_shown = True

    def reset_diarization_warning(self):
        """Setzt den einmaligen Diarization-Warnhinweis zurück."""
        self.diarization_warning_shown = False
    
    def on_output_changed(self, settings: dict):
        """Wird aufgerufen wenn sich Output Settings ändern."""
        output_path = settings.get('output_path', 'Auto')
        timestamps = "✓" if settings.get('timestamps') else "✗"
        format_type = settings.get('format', 'plain')
        
        if output_path == 'Auto' or not output_path:
            path_display = "Auto"
        else:
            path_display = Path(output_path).name
        
        self.statusBar().showMessage(
            f"Output: {path_display} | Timestamps: {timestamps} | Format: {format_type}"
        )
    
    def on_recording_started(self):
        """Wird aufgerufen wenn Live-Recording startet."""
        self.statusBar().showMessage(tr("status_recording"))
    
    def on_recording_stopped(self):
        """Wird aufgerufen wenn Live-Recording endet."""
        self.statusBar().showMessage(tr("status_recording_stopped"))
    
    # ===== Shortcuts =====
    
    def setup_shortcuts(self):
        """Richtet Tastenkürzel ein."""
        self.shortcut_start = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_start.activated.connect(
            self.transcription_controller.start_transcription
        )
        
        self.shortcut_stop = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_stop.activated.connect(
            self.transcription_controller.stop_transcription
        )
        
        self.shortcut_save_profile = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save_profile.activated.connect(
            self.profile_controller.save_current_profile
        )
        
        self.shortcut_clear_output = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_clear_output.activated.connect(self.clear_output)
        
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.activated.connect(self.close)
        
        self.log_info("Keyboard shortcuts configured")
    
    # ===== Logging =====
    
    def setup_logging(self):
        """Richtet das Logging-System ein."""
        log_dir = Path.home() / "V-SpeechFlow" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 50)
        self.logger.info("V-SpeechFlow GUI session started")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info("=" * 50)
    
    def log_info(self, message: str):
        """Loggt eine Info-Nachricht."""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Loggt eine Error-Nachricht."""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """Loggt eine Warning-Nachricht."""
        self.logger.warning(message)
    
    # ===== Theme =====
    
    def apply_theme(self, theme: str):
        """Wendet das gewählte Theme an."""
        stylesheet = self.theme_manager.get_stylesheet(theme)
        self.setStyleSheet(stylesheet)
        
        if hasattr(self, 'btn_start'):
            if theme == 'dark':
                self.btn_start.setStyleSheet(
                    f"background-color: {COLOR_SUCCESS_DARK}; color: white; "
                    f"font-weight: bold; padding: 8px;"
                )
                self.btn_stop.setStyleSheet(
                    f"background-color: {COLOR_ERROR_DARK}; color: white; "
                    f"font-weight: bold; padding: 8px;"
                )
            else:
                self.btn_start.setStyleSheet(
                    f"background-color: {COLOR_SUCCESS}; color: white; "
                    f"font-weight: bold; padding: 8px;"
                )
                self.btn_stop.setStyleSheet(
                    f"background-color: {COLOR_ERROR}; color: white; "
                    f"font-weight: bold; padding: 8px;"
                )
    
    # ===== Output =====
    
    def append_output(self, text: str):
        """Fügt Text zum Output-Preview hinzu (für Live-Output)."""
        self.output_preview.append(text)
        scrollbar = self.output_preview.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_output(self):
        """Löscht den Output-Preview."""
        self.output_preview.clear()
    
    def set_output(self, text: str):
        """Setzt den kompletten Output-Text (überschreibt alles)."""
        self.output_preview.setPlainText(text)
    
    def open_output_file(self, file_path: str):
        """Öffnet die Output-Datei im Standard-Texteditor."""
        path = Path(file_path)
        if not path.exists():
            QMessageBox.warning(
                self, tr('main_file_not_found_title'),
                f"{tr('main_file_not_found_msg')} {file_path}"
            )
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(
                self, tr('main_error'),
                f"{tr('main_file_open_error')}\n{str(e)}"
            )
    
    # ===== Wizard & Onboarding =====
    
    def apply_wizard_settings(self, data: dict):
        """Wendet die Einstellungen aus dem Installation Wizard an."""
        self.session_manager.apply_wizard_settings(data)
    
    def start_onboarding(self):
        """Startet das Onboarding-Tutorial."""
        self.log_info("Starting onboarding tutorial...")
        self.history_manager.mark_onboarding_completed(complete=False)
        self.onboarding_manager = OnboardingManager(self)
        self.onboarding_manager.start()
    
    def offer_onboarding(self):
        """Bietet das Onboarding an (falls noch nicht absolviert)."""
        reply = QMessageBox.question(
            self,
            tr('msg_tutorial_available_title'),
            tr('msg_tutorial_available'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_onboarding()
        else:
            self.history_manager.mark_onboarding_completed()
    
    # ===== Sprache =====
    
    def change_language(self, language: str):
        """Ändert die UI-Sprache."""
        current_language = get_translation_manager().get_current_language()
        if current_language == language:
            self.log_info(f"Language already set to: {language}")
            return
        
        set_language(language)
        self.history_manager.save_user_preference('ui_language', language)
        self.log_info(f"Language changed to: {language}")
        self.restart_application(language)
    
    def refresh_ui(self):
        """
        Aktualisiert alle UI-Texte nach einem Sprachwechsel.
        Delegiert an Controller und Panel refresh_translations()-Methoden.
        """
        # Window Title
        self.setWindowTitle(tr("app_title"))
        self.title_label.setText(tr("gui_title"))
        
        # Profile Section
        self.profile_group.setTitle("📁 " + tr("profile_label"))
        
        # Profile Combo Box - erstes Item
        current_text = self.profile_combo.currentText()
        if current_text in (
            "-- Aktuell (nicht gespeichert) --",
            "-- Current (not saved) --"
        ):
            self.profile_combo.setItemText(0, tr("profile_current_unsaved"))
        
        # Profile Buttons Tooltips
        for btn in self.findChildren(QPushButton):
            text = btn.text()
            if text == "💾":
                btn.setToolTip(tr("profile_save_tooltip"))
            elif text == "📋":
                btn.setToolTip(tr("profile_duplicate_tooltip"))
            elif text == "❌" and btn.width() <= 35:
                btn.setToolTip(tr("profile_delete_tooltip"))
            elif text == "⋮":
                btn.setToolTip(tr("profile_menu_tooltip"))
        
        # Output Preview
        self.output_title.setText(tr("output_preview_title"))
        
        # Buttons
        self.btn_start.setText(tr("start_transcription_button"))
        self.btn_start.setToolTip(tr("start_transcription_tooltip"))
        self.btn_stop.setText(tr("stop_button"))
        self.btn_stop.setToolTip(tr("stop_transcription_tooltip"))
        
        # Progress Bar
        self.progress_bar.setFormat(tr("progress_format"))
        
        # Status Bar
        if not self.is_processing:
            self.statusBar().showMessage(tr("status_ready"))
        
        # Menü-Übersetzungen an MenuManager delegieren
        self.menu_manager.refresh_translations()
        
        # Panel-Übersetzungen delegieren
        self.input_panel.refresh_translations()
        self.model_panel.refresh_translations()
        self.settings_panel.refresh_translations()
        self.diarization_panel.refresh_translations()
        self.output_panel.refresh_translations()
        
        self.log_info("UI texts updated")
    
    def restart_application(self, language: str):
        """Startet die Anwendung neu, um die Sprachänderung vollständig zu übernehmen."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(tr("msg_restart_app_title"))
        msg.setText(tr("msg_restart_app_text"))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        self.log_info(f"Restarting application with language: {language}")
        
        python = sys.executable
        restart_cmd = [python, "-m", "src.gui.app"]
        cwd = os.getcwd()
        
        self.log_info(f"Restart command: {' '.join(restart_cmd)} in {cwd}")
        
        subprocess.Popen(restart_cmd, cwd=cwd)
        QApplication.quit()
    
    # ===== Model-Update-Check =====
    
    def check_model_updates(self):
        """Prüft auf Model-Updates (wird beim Start aufgerufen)."""
        model_path = self.model_panel.get_model_path()
        
        if not model_path or not Path(model_path).exists():
            return
        
        check_updates = self.history_manager.get_user_preference(
            'check_model_updates', True
        )
        if not check_updates:
            return
        
        from .model_utils import check_model_updates_with_cache
        
        def do_check():
            result = check_model_updates_with_cache(model_path, force=False)
            if result and result.get('update_available'):
                QTimer.singleShot(
                    0, lambda: self.show_update_notification(result)
                )
        
        import threading
        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()
    
    def show_update_notification(self, update_info: dict):
        """Zeigt eine Benachrichtigung über verfügbares Model-Update."""
        model_name = update_info.get('model_name', 'Unknown')
        local_size = update_info.get('local_size_mb', 0)
        remote_size = update_info.get('remote_size_mb', 0)
        
        reply = QMessageBox.question(
            self,
            tr('msg_model_update_title'),
            tr('msg_model_update', name=model_name, local=local_size, remote=remote_size),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import webbrowser
            url = update_info.get(
                'download_url', 'https://huggingface.co/ggerganov/whisper.cpp'
            )
            webbrowser.open(url)
    
    # ===== Fenster-Lifecycle =====
    
    def closeEvent(self, event):
        """Wird aufgerufen wenn das Fenster geschlossen wird."""
        if self.is_processing:
            reply = QMessageBox.question(
                self,
                tr('msg_close_window_title'),
                tr('msg_close_window'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            if self.cli_worker:
                self.cli_worker.stop()
                self.cli_worker.wait(2000)
        
        # Session speichern
        self.session_manager.save_current_session()
        
        self.log_info("=== V-SpeechFlow GUI terminated ===")
        event.accept()
