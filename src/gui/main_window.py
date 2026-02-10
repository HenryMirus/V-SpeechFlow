"""
Hauptfenster der PyQt6 GUI

Stellt die zentrale Benutzeroberfläche mit allen Panels zur Verfügung.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStatusBar,
    QSplitter,
    QScrollArea,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QComboBox,
    QInputDialog,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import QApplication
import sys
import os
import subprocess
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
from .theme_toggle_switch import ThemeToggleSwitch
import logging
from datetime import datetime
from pathlib import Path


class MainWindow(QMainWindow):
    """Hauptfenster der V-SpeechFlow GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(100, 100, 1400, 900)
        
        # Worker für CLI-Prozess
        self.cli_worker = None
        self.batch_worker = None
        self.is_processing = False
        self.is_batch_processing = False
        
        # Profile-Manager
        self.profile_manager = ProfileManager()
        
        # History-Manager
        self.history_manager = HistoryManager()
        
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
        self.log_info("V-SpeechFlow GUI gestartet")
        self.log_info(f"UI Language: {saved_language}")
        
        # Theme anwenden
        self.apply_theme(self.theme_manager.get_current_theme())
        
        # Menu-Bar erstellen
        self.create_menu_bar()
        
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
        
        # 2. Profile-Auswahl
        profile_layout = QHBoxLayout()
        self.profile_label = QLabel("📁 " + tr("profile_label"))
        profile_layout.addWidget(self.profile_label)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem(tr("profile_current_unsaved"))
        self.refresh_profile_list()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        
        btn_save_profile = QPushButton("💾")
        btn_save_profile.setToolTip(tr("profile_save_tooltip"))
        btn_save_profile.setFixedWidth(35)
        btn_save_profile.clicked.connect(self.save_current_profile)
        profile_layout.addWidget(btn_save_profile)
        
        btn_duplicate_profile = QPushButton("📋")
        btn_duplicate_profile.setToolTip(tr("profile_duplicate_tooltip"))
        btn_duplicate_profile.setFixedWidth(35)
        btn_duplicate_profile.clicked.connect(self.duplicate_selected_profile)
        profile_layout.addWidget(btn_duplicate_profile)
        
        btn_delete_profile = QPushButton("❌")
        btn_delete_profile.setToolTip(tr("profile_delete_tooltip"))
        btn_delete_profile.setFixedWidth(35)
        btn_delete_profile.clicked.connect(self.delete_selected_profile)
        profile_layout.addWidget(btn_delete_profile)
        
        # Mehr Options-Button (für Export/Import)
        btn_profile_menu = QPushButton("⋮")
        btn_profile_menu.setToolTip(tr("profile_menu_tooltip"))
        btn_profile_menu.setFixedWidth(35)
        btn_profile_menu.clicked.connect(self.show_profile_menu)
        profile_layout.addWidget(btn_profile_menu)
        
        left_layout.addLayout(profile_layout)
        
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
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_start.setToolTip(tr("start_transcription_tooltip"))
        self.btn_start.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton(tr("stop_button"))
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setToolTip(tr("stop_transcription_tooltip"))
        self.btn_stop.clicked.connect(self.stop_transcription)
        button_layout.addWidget(self.btn_stop)
        
        right_layout.addLayout(button_layout)
        
        main_layout.addWidget(right_panel, 1)  # 1/3 der Breite
        
        # Status Bar
        self.statusBar().showMessage(tr("status_ready"))
        
        # Tastenkürzel einrichten
        self.setup_shortcuts()
        
        # Status-Update Timer (für Auto-Save etc.)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Alle 5 Sekunden
        
        # Progress-Update Timer (für kontinuierliches ETA-Update)
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_display)
        # Timer wird nur während Verarbeitung aktiviert
        
        # Config beim Start laden (initial_config oder last_session)
        QTimer.singleShot(100, self.load_startup_config)  # Nach 100ms
        
        # Model-Update-Check beim Start (verzögert)
        QTimer.singleShot(3000, self.check_model_updates)  # Nach 3 Sekunden
        
        # UI-Texte mit korrekten Übersetzungen initialisieren
        QTimer.singleShot(100, self.refresh_ui)
    
    def on_file_selected(self, file_path: str):
        """Wird aufgerufen wenn eine Datei ausgewählt wird."""
        self.statusBar().showMessage(f"✓ {Path(file_path).name}")
    
    def load_startup_config(self):
        """
        Lädt Konfiguration beim App-Start:
        1. Wenn initial_config vorhanden und nicht angewendet -> Lade initial_config
        2. Sonst -> Lade last_session
        """
        # Prüfe ob initial_config vorhanden und noch nicht angewendet
        initial_config = self.history_manager.get_initial_config()
        
        if initial_config:
            # Erster Start nach Wizard - lade initial_config
            self.log_info("Erster Start nach Wizard - lade Initial-Config")
            self.load_initial_config(initial_config)
            self.history_manager.mark_initial_config_applied()
        else:
            # Normaler Start - lade last_session
            self.log_info("Lade letzte Session")
            self.load_last_session()
    
    def load_initial_config(self, config: dict):
        """
        Lädt die Initial-Konfiguration aus dem Installation-Wizard.
        Wird nur beim ersten Start nach Wizard-Abschluss aufgerufen.
        
        Args:
            config: Dictionary mit Wizard-Einstellungen
        """
        self.log_info("Lade Initial-Config aus Wizard...")
        print(f"\n=== Lade Initial-Config (erster Start) ===")
        print(f"Config-Keys: {list(config.keys())}")
        
        # Model Panel
        if 'default_model' in config and config['default_model']:
            model_path = config['default_model']
            if Path(model_path).exists():
                self.model_panel.set_model_path(model_path)
                self.log_info(f"Model aus Initial-Config geladen: {model_path}")
                print(f"  ✓ Model: {model_path}")
            else:
                self.log_warning(f"Model aus Initial-Config nicht gefunden: {model_path}")
                print(f"  ✗ Model nicht gefunden: {model_path}")
        
        # Settings Panel
        settings_data = {}
        if 'default_threads' in config:
            settings_data['threads'] = config['default_threads']
            print(f"  ✓ Threads: {config['default_threads']}")
        if 'default_language' in config:
            settings_data['language'] = config['default_language']
            print(f"  ✓ Language: {config['default_language']}")
        
        if settings_data:
            self.settings_panel.set_settings(settings_data)
            self.log_info(f"Settings aus Initial-Config geladen: {settings_data}")
        
        # Output Panel - auto_open_transcript
        if 'auto_open_transcript' in config:
            auto_open = config['auto_open_transcript']
            self.output_panel.set_auto_open(auto_open)
            self.log_info(f"Auto-Open aus Initial-Config: {auto_open}")
            print(f"  ✓ Auto-Open: {auto_open}")
        
        # UI Language wird NICHT aus initial_config geladen, da es bereits
        # beim Start aus user_preferences geladen wurde und im Wizard direkt
        # in user_preferences gespeichert wird
        
        # Theme
        if 'preferred_theme' in config:
            theme = config['preferred_theme']
            self.apply_theme(theme)
            if hasattr(self, 'theme_toggle_switch'):
                self.update_theme_switch()
            print(f"  ✓ Theme: {theme}")
        
        print("=== Initial-Config erfolgreich geladen ===")
        self.statusBar().showMessage(tr("loading_initial_config"), 3000)
    
    def load_last_session(self):
        """
        Lädt die letzte Session inkl. aktivem Profil.
        Wird bei jedem Start (außer erstem nach Wizard) aufgerufen.
        """
        last_session = self.history_manager.get_last_session()
        
        if not last_session:
            self.log_info("Keine letzte Session gefunden")
            return
        
        profile_name = last_session.get('profile_name')
        session_data = last_session.get('data')
        
        if not session_data:
            self.log_info("Session-Daten sind leer")
            return
        
        self.log_info(f"Lade letzte Session (Profil: {profile_name or 'Keins'})")
        print(f"\n=== Lade letzte Session ===")
        print(f"Profil: {profile_name or 'Keins'}")
        
        # Wenn ein Profil aktiv war, versuche es zu laden
        if profile_name and profile_name != '-- Aktuell (nicht gespeichert) --':
            profile_data = self.profile_manager.get_profile(profile_name)
            if profile_data:
                self.log_info(f"Lade Profil: {profile_name}")
                print(f"  ✓ Profil '{profile_name}' geladen")
                
                # Setze Profil in Combo
                index = self.profile_combo.findText(profile_name)
                if index >= 0:
                    self.profile_combo.blockSignals(True)
                    self.profile_combo.setCurrentIndex(index)
                    self.profile_combo.blockSignals(False)
                
                # Lade Profil-Daten (analog zu on_profile_selected)
                if 'settings' in profile_data:
                    self.settings_panel.set_settings(profile_data['settings'])
                if 'diarization' in profile_data:
                    self.diarization_panel.set_settings(profile_data['diarization'])
                if 'output' in profile_data:
                    self.output_panel.set_settings(profile_data['output'])
                
                self.statusBar().showMessage(f"{tr('profile_label')} '{profile_name}' wiederhergestellt", 3000)
                return
            else:
                self.log_warning(f"Profil '{profile_name}' nicht gefunden")
                print(f"  ✗ Profil nicht gefunden, lade Session-Daten")
        
        # Kein Profil oder nicht gefunden - lade Session-Daten direkt
        print("  ✓ Lade Session-Daten")
        
        # Input-Datei (nur wenn existent)
        if 'input_file' in session_data:
            input_file = session_data['input_file']
            if input_file and Path(input_file).exists():
                self.input_panel.set_file_path(input_file)
                print(f"    - Input: {Path(input_file).name}")
        
        # Model
        if 'model' in session_data:
            model_path = session_data['model']
            if model_path and Path(model_path).exists():
                self.model_panel.set_model_path(model_path)
                print(f"    - Model: {Path(model_path).name}")
        
        # Settings
        if 'settings' in session_data:
            self.settings_panel.set_settings(session_data['settings'])
            print(f"    - Settings: {session_data['settings'].get('threads')} threads")
        
        # Diarization
        if 'diarization' in session_data:
            self.diarization_panel.set_settings(session_data['diarization'])
            print(f"    - Diarization: {'Ja' if session_data['diarization'].get('enabled') else 'Nein'}")
        
        # Output
        if 'output' in session_data:
            self.output_panel.set_settings(session_data['output'])
            print(f"    - Output: {session_data['output'].get('format')}")
        
        print("=== Letzte Session erfolgreich geladen ===")
        self.statusBar().showMessage(tr("loading_last_session"), 3000)
    
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
            from pathlib import Path
            path_display = Path(output_path).name
        
        self.statusBar().showMessage(
            f"Output: {path_display} | Timestamps: {timestamps} | Format: {format_type}"
        )
    
    def setup_shortcuts(self):
        """Richtet Tastenkürzel ein."""
        # Ctrl+Return / Cmd+Return: Start Transkription
        self.shortcut_start = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_start.activated.connect(self.start_transcription)
        
        # Escape: Stop Transkription
        self.shortcut_stop = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_stop.activated.connect(self.stop_transcription)
        
        # Ctrl+S: Profil speichern
        self.shortcut_save_profile = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save_profile.activated.connect(self.save_current_profile)
        
        # Ctrl+O: Output löschen
        self.shortcut_clear_output = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_clear_output.activated.connect(self.clear_output)
        
        # Ctrl+Q: Beenden
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.activated.connect(self.close)
        
        self.log_info("Tastenkürzel eingerichtet")
    
    def setup_logging(self):
        """Richtet das Logging-System ein."""
        # Log-Verzeichnis erstellen
        log_dir = Path.home() / "V-SpeechFlow" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log-Datei mit Timestamp
        log_file = log_dir / f"gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Logging konfigurieren
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
        self.logger.info("V-SpeechFlow GUI Session gestartet")
        self.logger.info(f"Log-Datei: {log_file}")
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
    
    def create_menu_bar(self):
        """Erstellt die Menu-Bar mit History und anderen Optionen."""
        menubar = self.menuBar()
        
        # Menüleiste explizit sichtbar machen
        menubar.setVisible(True)
        
        # Auf macOS: Menüleiste im Fenster anzeigen statt in System-Menüleiste
        # (Optional: Auskommentieren um macOS-Standard zu nutzen)
        menubar.setNativeMenuBar(False)
        
        # Theme-Toggle-Switch (wird am Ende der Menubar hinzugefügt)
        self.theme_toggle_switch = ThemeToggleSwitch()
        self.theme_toggle_switch.clicked = self.toggle_theme
        self.update_theme_switch()
        
        # Datei-Menü
        self.file_menu = menubar.addMenu("📁 " + tr("menu_file"))
        
        # Recent Files Submenu
        self.recent_files_menu = QMenu("🕒 " + tr("menu_recent_files"), self)
        self.file_menu.addMenu(self.recent_files_menu)
        self.update_recent_files_menu()
        
        self.file_menu.addSeparator()
        
        # Recent Models Submenu
        self.recent_models_menu = QMenu("🤖 " + tr("menu_recent_models"), self)
        self.file_menu.addMenu(self.recent_models_menu)
        self.update_recent_models_menu()
        
        self.file_menu.addSeparator()
        
        # Batch-Processing
        batch_action = QAction("📦 " + tr("menu_batch"), self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self.open_batch_window)
        self.file_menu.addAction(batch_action)
        
        self.file_menu.addSeparator()
        
        # History löschen
        clear_history_action = QAction("🗑️ " + tr("menu_clear_history"), self)
        clear_history_action.triggered.connect(self.clear_history)
        self.file_menu.addAction(clear_history_action)
        
        self.file_menu.addSeparator()
        
        # Beenden
        quit_action = QAction("❌ " + tr("menu_quit"), self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        self.file_menu.addAction(quit_action)
        
        # Profile-Menü
        self.profile_menu = menubar.addMenu("📋 " + tr("menu_profiles_title"))
        
        # Favoriten & Standard-Profile Submenu
        self.favorites_menu = QMenu("⭐ " + tr("menu_profiles_favorites"), self)
        self.profile_menu.addMenu(self.favorites_menu)
        self.update_favorites_menu()

        # Alle anderen Profile Submenu
        self.all_profiles_menu = QMenu("📋 " + tr("menu_profiles_all"), self)
        self.profile_menu.addMenu(self.all_profiles_menu)
        self.update_all_profiles_menu()
        
        self.profile_menu.addSeparator()
        
        # Export Profil
        export_profile_action = QAction("📤 " + tr("menu_profiles_export"), self)
        export_profile_action.triggered.connect(self.export_profile)
        self.profile_menu.addAction(export_profile_action)
        
        # Import Profil
        import_profile_action = QAction("📥 " + tr("menu_profiles_import"), self)
        import_profile_action.triggered.connect(self.import_profile)
        self.profile_menu.addAction(import_profile_action)
        
        # Sprach-Dropdown (wird als Corner Widget hinzugefügt)
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇩🇪", "de")  # userData = language code
        self.language_combo.addItem("🇺🇸", "en")
        self.language_combo.setToolTip(tr("menu_language"))
        self.language_combo.setFixedWidth(70)
        self.language_combo.setFixedHeight(32)
        self.language_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(150, 150, 150, 0.3);
                border-radius: 6px;
                padding: 4px 10px;
                background: rgba(255, 255, 255, 0.05);
                font-size: 20px;
                color: inherit;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(150, 150, 150, 0.5);
            }
            QComboBox:focus {
                border: 1px solid rgba(100, 150, 255, 0.6);
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
                padding-right: 4px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(150, 150, 150, 0.3);
                border-radius: 6px;
                padding: 4px;
                background-color: rgba(255, 255, 255, 0.95);
                selection-background-color: rgba(100, 150, 255, 0.2);
                selection-color: inherit;
                font-size: 18px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(100, 150, 255, 0.15);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(100, 150, 255, 0.25);
            }
        """)
        
        # Aktuelle Sprache auswählen
        current_language = get_translation_manager().get_current_language()
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # Signal verbinden
        self.language_combo.currentIndexChanged.connect(self.on_language_combo_changed)
        
        # Hilfe-Menü
        self.help_menu = menubar.addMenu("❓ " + tr("menu_help"))
        
        # Tutorial/Onboarding
        tutorial_action = QAction("🎓 " + tr("menu_start_onboarding"), self)
        tutorial_action.triggered.connect(self.start_onboarding)
        self.help_menu.addAction(tutorial_action)
        
        self.help_menu.addSeparator()
        
        shortcuts_action = QAction("⌨️ " + tr("menu_shortcuts"), self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        self.help_menu.addAction(shortcuts_action)
        
        self.help_menu.addSeparator()
        
        about_action = QAction("ℹ️ " + tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(about_action)
        
        # Corner Widget mit Sprach-Dropdown und Theme-Toggle-Switch
        corner_container = QWidget()
        corner_container.setContentsMargins(0, 0, 15, 0)  # 15px Abstand vom rechten Rand
        corner_container.setStyleSheet("background: transparent;")  # Transparenter Hintergrund
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(12)  # 12px Abstand zwischen Sprache und Theme
        corner_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Vertikale Zentrierung
        corner_layout.addWidget(self.language_combo)
        corner_layout.addWidget(self.theme_toggle_switch)
        menubar.setCornerWidget(corner_container, Qt.Corner.TopRightCorner)
        
        self.log_info("Menu-Bar erstellt")
    
    def update_recent_files_menu(self):
        """Aktualisiert das Recent Files Menü."""
        self.recent_files_menu.clear()
        
        recent_files = self.history_manager.get_recent_input_files(limit=10)
        
        if not recent_files:
            no_files_action = QAction(tr("menu_no_recent_files"), self)
            no_files_action.setEnabled(False)
            self.recent_files_menu.addAction(no_files_action)
            return
        
        for file_entry in recent_files:
            file_path = file_entry["path"]
            file_name = file_entry["name"]
            size_mb = file_entry.get("size_mb", 0)
            
            action = QAction(f"{file_name} ({size_mb:.1f} MB)", self)
            action.setToolTip(file_path)
            action.triggered.connect(lambda checked, path=file_path: self.load_recent_file(path))
            self.recent_files_menu.addAction(action)
    
    def update_recent_models_menu(self):
        """Aktualisiert das Recent Models Menü."""
        self.recent_models_menu.clear()
        
        recent_models = self.history_manager.get_recent_models(limit=5)
        
        if not recent_models:
            no_models_action = QAction(tr("menu_no_recent_models"), self)
            no_models_action.setEnabled(False)
            self.recent_models_menu.addAction(no_models_action)
            return
        
        for model_entry in recent_models:
            model_path = model_entry["path"]
            model_name = model_entry["name"]
            size_mb = model_entry.get("size_mb", 0)
            
            action = QAction(f"{model_name} ({size_mb:.0f} MB)", self)
            action.setToolTip(model_path)
            action.triggered.connect(lambda checked, path=model_path: self.load_recent_model(path))
            self.recent_models_menu.addAction(action)
    
    def load_recent_file(self, file_path: str):
        """Lädt eine zuletzt verwendete Datei."""
        if Path(file_path).exists():
            self.input_panel.set_file_path(file_path)
            self.log_info(f"Datei aus History geladen: {file_path}")
        else:
            QMessageBox.warning(
                self,
                tr('main_file_not_found_title'),
                f"{tr('main_file_not_exist')}\n{file_path}"
            )
            self.history_manager.remove_input_file(file_path)
            self.update_recent_files_menu()
    
    def load_recent_model(self, model_path: str):
        """Lädt ein zuletzt verwendetes Modell."""
        if Path(model_path).exists():
            self.model_panel.set_model_path(model_path)
            self.log_info(f"Modell aus History geladen: {model_path}")
        else:
            QMessageBox.warning(
                self,
                tr('main_model_not_found_title'),
                f"{tr('main_model_not_exist')}\n{model_path}"
            )
            self.history_manager.remove_model(model_path)
            self.update_recent_models_menu()
    
    def clear_history(self):
        """Löscht die komplette History."""
        reply = QMessageBox.question(
            self,
            tr('main_clear_history_title'),
            tr('main_clear_history_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.update_recent_files_menu()
            self.update_recent_models_menu()
            self.log_info("History gelöscht")
            QMessageBox.information(self, tr('main_done'), tr('main_history_cleared'))
    
    def load_last_settings(self):
        """DEPRECATED: Verwende stattdessen load_last_session(). Bleibt zur Kompatibilität."""
        self.load_last_session()
    
    def save_current_session(self):
        """Speichert die aktuelle Session in der History inkl. aktivem Profil."""
        # Hole aktuelles Profil
        current_profile = self.profile_combo.currentText()
        if current_profile == "-- Aktuell (nicht gespeichert) --":
            current_profile = None
        
        session_data = {
            'input_file': self.input_panel.get_selected_file(),
            'model': self.model_panel.get_selected_model(),
            'settings': self.settings_panel.get_settings(),
            'diarization': self.diarization_panel.get_settings(),
            'output': self.output_panel.get_settings(),
        }
        
        # Session speichern (mit Profil)
        self.history_manager.save_last_session(session_data, current_profile)
        self.log_info(f"Session in History gespeichert (Profil: {current_profile or 'Keins'})")
    
    def show_about(self):
        """Zeigt About-Dialog."""
        QMessageBox.about(
            self,
            "Über V-SpeechFlow",
            "<h2>V-SpeechFlow</h2>"
            "<p><b>Version:</b> 1.0.0</p>"
            "<p><b>Speech-to-Text mit Speaker Diarization</b></p>"
            "<p>Powered by Whisper.cpp und pyannote.audio</p>"
            "<p>© 2026 V-SpeechFlow Team</p>"
        )
    
    def show_shortcuts(self):
        """Zeigt Dialog mit allen Tastenkürzel und deren Funktionen."""
        shortcuts_text = f"""
        <h2>{tr("shortcuts_title")}</h2>
        <table border="1" cellpadding="8" cellspacing="0" width="100%">
            <tr style="background-color: rgba(100, 150, 255, 0.2);">
                <th align="left"><b>Tastenkombination</b></th>
                <th align="left"><b>Funktion</b></th>
            </tr>
            <tr>
                <td><code>Ctrl+Return</code></td>
                <td>{tr("shortcuts_start_transcription")}</td>
            </tr>
            <tr>
                <td><code>Escape</code></td>
                <td>{tr("shortcuts_stop_transcription")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+S</code></td>
                <td>{tr("shortcuts_save_profile")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+L</code></td>
                <td>{tr("shortcuts_clear_output")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+B</code></td>
                <td>{tr("shortcuts_batch_processing")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+Q</code></td>
                <td>{tr("shortcuts_quit")}</td>
            </tr>
        </table>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"⌨️ {tr('shortcuts_title')}")
        msg.setText(shortcuts_text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgba(240, 240, 240, 0.95);
            }
            QMessageBox QLabel {
                color: inherit;
            }
            QMessageBox QMessageBox {
                min-width: 400px;
            }
        """)
        msg.exec()
    
    def open_batch_window(self):
        """Aktiviert den Batch-Tab im Input-Panel."""
        # Wechsle zum Batch-Tab (Index 1)
        self.input_panel.tabs.setCurrentIndex(1)
        self.log_info("Batch-Tab aktiviert")
        self.statusBar().showMessage("📦 Batch-Modus aktiviert", 2000)
    
    def toggle_theme(self):
        """Wechselt zwischen Light und Dark Mode."""
        current = self.theme_manager.get_current_theme()
        new_theme = 'dark' if current == 'light' else 'light'
        
        self.apply_theme(new_theme)
        self.theme_manager.save_theme_preference(new_theme)
        
        # Update Theme-Switch
        self.update_theme_switch()
        
        self.log_info(f"Theme gewechselt zu: {new_theme}")
    
    def update_theme_switch(self):
        """Aktualisiert den Theme-Toggle-Switch basierend auf dem aktuellen Theme."""
        current_theme = self.theme_manager.get_current_theme()
        is_dark = (current_theme == 'dark')
        self.theme_toggle_switch.set_dark_mode(is_dark, animate=True)
        
        # Tooltip setzen
        if is_dark:
            self.theme_toggle_switch.setToolTip("Zu Light Mode wechseln (☀️)")
        else:
            self.theme_toggle_switch.setToolTip("Zu Dark Mode wechseln (🌙)")
    
    def apply_theme(self, theme: str):
        """Wendet das gewählte Theme an."""
        stylesheet = self.theme_manager.get_stylesheet(theme)
        self.setStyleSheet(stylesheet)
        
        # Spezielle Button-Styles die nicht überschrieben werden sollen
        # (z.B. Start/Stop Buttons mit speziellen Farben)
        # Diese müssen explizit gesetzt werden nach Theme-Anwendung
        if hasattr(self, 'btn_start'):
            if theme == 'dark':
                self.btn_start.setStyleSheet(
                    "background-color: #43A047; color: white; font-weight: bold; padding: 8px;"
                )
                self.btn_stop.setStyleSheet(
                    "background-color: #E53935; color: white; font-weight: bold; padding: 8px;"
                )
            else:
                self.btn_start.setStyleSheet(
                    "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;"
                )
                self.btn_stop.setStyleSheet(
                    "background-color: #f44336; color: white; font-weight: bold; padding: 8px;"
                )
    
    
    def update_status(self):
        """Regelmäßige Status-Updates."""
        # Hier könnten später Auto-Save, etc. implementiert werden
        pass
    
    def update_progress_display(self):
        """Aktualisiert die Progress-Anzeige regelmäßig."""
        if not self.is_processing:
            return
        
        # UI aktualisieren basierend auf aktuellem Status
        self._update_progress_ui()
    
    def on_recording_started(self):
        """Wird aufgerufen wenn Live-Recording startet."""
        self.statusBar().showMessage("🔴 Aufnahme läuft...")
    
    def on_recording_stopped(self):
        """Wird aufgerufen wenn Live-Recording endet."""
        self.statusBar().showMessage("Aufnahme beendet")
    
    def start_transcription(self):
        """Startet die Transkription mit vollständiger Validierung."""
        self.log_info("=== Start Transkription angefordert ===")
        
        if self.is_processing:
            self.log_warning("Transkription bereits aktiv, Abbruch")
            QMessageBox.warning(self, tr('main_already_active_title'), tr('main_already_active_msg'))
            return
        
        # Prüfen ob Batch-Modus aktiv ist
        if self.input_panel.is_batch_mode():
            self.start_batch_processing()
            return
        
        # === Validierung aller Panels ===
        validation_errors = []
        
        # 1. Input validieren
        input_file = self.input_panel.get_selected_file()
        if not input_file:
            validation_errors.append("❌ Input: Keine Datei ausgewählt")
        
        # 2. Modell validieren
        model_path = self.model_panel.get_selected_model()
        if not model_path:
            validation_errors.append("❌ Modell: Kein Modell ausgewählt")
        
        # 3. Diarization validieren (wenn aktiviert)
        diarization_settings = self.diarization_panel.get_settings()
        if diarization_settings.get('enabled'):
            is_valid, error = self.diarization_panel.validate_settings()
            if not is_valid:
                validation_errors.append(f"❌ Diarization: {error}")
        
        # 4. Output validieren
        is_valid, error = self.output_panel.validate_settings()
        if not is_valid:
            validation_errors.append(f"❌ Output: {error}")
        
        # Wenn Fehler vorhanden, abbrechen
        if validation_errors:
            self.log_error(f"Validierungsfehler: {len(validation_errors)} Fehler gefunden")
            for error in validation_errors:
                self.log_error(f"  - {error}")
            error_message = f"{tr('main_validation_fix_errors')}\n\n" + "\n".join(validation_errors)
            QMessageBox.critical(self, tr('main_validation_error_title'), error_message)
            return
        
        # === CLI-Argumente zusammenstellen ===
        try:
            cli_args = self.build_cli_arguments()
            self.log_info(f"CLI-Argumente: {' '.join(cli_args)}")
        except Exception as e:
            self.log_error(f"Fehler beim Erstellen der CLI-Argumente: {str(e)}")
            QMessageBox.critical(self, tr('main_error'), f"{tr('main_cli_error')}\n{str(e)}")
            return
        
        # === UI vorbereiten ===
        self.output_preview.clear()
        self.append_output("=== V-SpeechFlow Transkription gestartet ===\n")
        self.append_output(f"Kommando: {' '.join(cli_args)}\n\n")
        
        self.is_processing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.eta_label.setVisible(True)
        self.eta_label.setText("🕒 Startet...")
        self.statusBar().showMessage("⏳ Transkription läuft...")
        
        # === CLI-Worker starten ===
        self.log_info("CLI-Worker wird gestartet...")
        
        # Progress Tracker initialisieren
        self.progress_tracker = ProgressTracker(has_diarization=diarization_settings.get('enabled', False))
        self.progress_tracker.start()  # Timer starten
        
        # Versuche Audio-Länge zu ermitteln (für bessere Progress-Berechnung)
        try:
            duration = self.progress_tracker.get_audio_duration(input_file)
            if duration:
                self.progress_tracker.set_audio_duration(duration)
        except:
            pass  # Nicht kritisch wenn Audio-Länge nicht ermittelt werden kann
        
        self.cli_worker = CLIWorker(cli_args)
        self.cli_worker.output_received.connect(self.on_cli_output)
        self.cli_worker.error_received.connect(self.on_cli_error)
        self.cli_worker.process_finished.connect(self.on_cli_finished)
        self.cli_worker.progress_updated.connect(self.on_cli_progress)
        self.cli_worker.start()
        self.log_info("CLI-Worker gestartet")
        
        # Progress Timer starten für regelmäßige Updates
        self.progress_timer.start(1000)  # Jede Sekunde
        
        # === History speichern ===
        self.history_manager.add_input_file(input_file)
        self.history_manager.add_model(model_path)
        self.save_current_session()
    
    def build_cli_arguments(self) -> list:
        """
        Baut die CLI-Argumente aus allen Panel-Einstellungen zusammen.
        
        Returns:
            Liste von CLI-Argumenten
        """
        args = []
        
        # Input-Datei
        input_file = self.input_panel.get_selected_file()
        if input_file:
            args.extend(["--input", input_file])
        
        # Modell
        model_path = self.model_panel.get_selected_model()
        if model_path:
            args.extend(["--model", model_path])
        
        # Settings
        settings = self.settings_panel.get_settings()
        
        # Threads
        if 'threads' in settings:
            args.extend(["--threads", str(settings['threads'])])
        
        # Sprache
        if 'language' in settings and settings['language'] != 'auto':
            args.extend(["-l", settings['language']])
        
        # Übersetzung
        if settings.get('translate'):
            args.append("--translate")
        
        # Keep Temp
        if settings.get('keep_temp'):
            args.append("--keep-temp")
        
        # Diarization
        diarization = self.diarization_panel.get_settings()
        if diarization.get('enabled'):
            # Diarize Flag aktivieren
            args.append("--diarize")
            
            # HF Token
            if diarization.get('hf_token'):
                args.extend(["--hf-token", diarization['hf_token']])
            
            # Sprecher-Modus
            if diarization['mode'] == 'exact':
                args.extend(["--num-speakers", str(diarization['num_speakers'])])
            else:  # auto
                args.extend(["--min-speakers", str(diarization['min_speakers'])])
                args.extend(["--max-speakers", str(diarization['max_speakers'])])
        
        # Output
        output_settings = self.output_panel.get_settings()
        
        # Output-Pfad
        output_path = self.output_panel.get_output_path(input_file)
        args.extend(["--output", output_path])
        
        # Timestamps
        if output_settings.get('timestamps'):
            args.append("-s")
        
        # Binary Path (optional)
        binary_path = settings.get('binary_path')
        if binary_path and binary_path.strip():
            args.extend(["--binary", binary_path])
        
        return args
    
    def on_cli_output(self, text: str):
        """Wird aufgerufen wenn CLI stdout Output empfängt."""
        self.append_output(text)
        
        # Parse die Ausgabe für Fortschritt
        if self.progress_tracker.parse_output_line(text):
            self._update_progress_ui()
    
    def on_cli_error(self, text: str):
        """Wird aufgerufen wenn CLI stderr Output empfängt."""
        # Prüfe ob es sich um Debug-Informationen oder echte Fehler handelt
        text_lower = text.lower()
        
        # Parse auch stderr für Fortschritt (manche Meldungen kommen über stderr)
        if self.progress_tracker.parse_output_line(text):
            self._update_progress_ui()
        
        # Debug-Präfixe von Whisper/ggml (keine echten Fehler)
        debug_prefixes = (
            'whisper_', 'ggml_', 'metal_', 'backend_', 'compute_',
            'encoder_', 'decoder_', 'kv_cache_', 'model_'
        )
        
        # Echte Fehler-Keywords
        error_keywords = ('error:', 'failed:', 'exception:', 'traceback', 'cannot', 'unable to')
        
        is_debug = any(text_lower.startswith(prefix) for prefix in debug_prefixes)
        is_error = any(keyword in text_lower for keyword in error_keywords)
        
        if is_error and not is_debug:
            # Echter Fehler -> rot
            self.append_output(f"<span style='color: red;'>[ERROR] {text}</span>")
        elif is_debug:
            # Debug-Information -> gedämpfte Farbe (grau)
            self.append_output(f"<span style='color: #888;'>{text}</span>")
        else:
            # Sonstige stderr-Ausgaben -> normal anzeigen
            self.append_output(text)
    
    def on_cli_progress(self, percentage: float, current_timestamp: float):
        """Wird aufgerufen wenn Fortschritt gemeldet wird (Legacy - wird jetzt anders gehandhabt)."""
        # Diese Methode wird noch vom Worker aufgerufen, aber wir nutzen jetzt parse_output_line()
        # Für Kompatibilität behalten wir sie, aber die Logik ist jetzt im ProgressTracker
        pass
    
    def _update_progress_ui(self):
        """Aktualisiert die Progress-UI basierend auf dem ProgressTracker."""
        # Progress Percentage
        progress_pct = self.progress_tracker.get_progress_percentage()
        self.progress_bar.setValue(int(progress_pct))
        
        # Status-Text
        status_text = self.progress_tracker.get_status_text()
        phase_name = self.progress_tracker.get_current_phase_name()
        
        # Elapsed time
        elapsed = self.progress_tracker.get_elapsed_time_str()
        
        # ETA Label mit Phase, Timestamp-Info und elapsed time
        self.eta_label.setText(f"⚙️ {status_text} | 🕒 Verstrichen: {elapsed}")
        
        # Status Bar
        self.statusBar().showMessage(
            f"⏳ {phase_name}: {progress_pct:.1f}%"
        )
    
    def on_cli_finished(self, return_code: int):
        """Wird aufgerufen wenn der CLI-Prozess beendet ist."""
        self.log_info(f"CLI-Prozess beendet mit Exit-Code: {return_code}")
        self.is_processing = False
        self.progress_bar.setVisible(False)
        self.eta_label.setVisible(False)
        # Progress Timer stoppen
        self.progress_timer.stop()
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        # Progress Tracker zurücksetzen
        self.progress_tracker.reset()

        # Warnung nach Transkription zurücksetzen
        self.reset_diarization_warning()
        
        if return_code == 0:
            # Erfolg
            self.append_output("\n" + "="*50)
            self.append_output("✅ Transkription erfolgreich abgeschlossen!")
            self.append_output("="*50)
            
            # Output-Datei Pfad anzeigen
            input_file = self.input_panel.get_selected_file()
            output_path = self.output_panel.get_output_path(input_file)
            self.append_output(f"\n💾 Ausgabe gespeichert: {output_path}")
            
            # History aktualisieren
            self.history_manager.add_output_path(output_path)
            self.update_recent_files_menu()
            self.update_recent_models_menu()
            
            self.statusBar().showMessage("✅ Transkription erfolgreich abgeschlossen!")
            
            # Auto-Open wenn aktiviert
            output_settings = self.output_panel.get_settings()
            if output_settings.get('auto_open'):
                self.open_output_file(output_path)
            
            QMessageBox.information(
                self,
                tr('main_done'),
                f"{tr('main_transcription_success')}\n\n{tr('main_file_saved_at')}\n{output_path}"
            )
        else:
            # Fehler
            self.append_output("\n" + "="*50)
            self.append_output(f"❌ Transkription fehlgeschlagen (Exit Code: {return_code})")
            self.append_output("="*50)
            
            self.statusBar().showMessage(f"❌ Transkription fehlgeschlagen (Code: {return_code})")
            
            QMessageBox.critical(
                self,
                tr('main_error'),
                f"{tr('main_transcription_failed', code=return_code)}\n\n"
                f"{tr('main_check_output')}"
            )
        
        # Worker cleanup
        if self.cli_worker:
            self.cli_worker.deleteLater()
            self.cli_worker = None
    
    def stop_transcription(self):
        """Stoppt die Transkription."""
        if self.is_batch_processing and self.batch_worker:
            self.stop_batch_processing()
            return
        
        if not self.is_processing or not self.cli_worker:
            return
        
        self.log_info("Stop Transkription angefordert")
        
        reply = QMessageBox.question(
            self,
            tr('main_abort_transcription_title'),
            tr('main_abort_transcription_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_warning("Transkription wird abgebrochen...")
            self.append_output("\n⏹️ Transkription wird abgebrochen...")
            self.statusBar().showMessage("⏹️ Abbruch...")
            
            # Worker stoppen
            if self.cli_worker:
                self.cli_worker.stop()
                self.cli_worker.wait(3000)  # 3 Sekunden warten
                
                if self.cli_worker.isRunning():
                    # Falls nicht terminiert, force quit
                    self.cli_worker.terminate()
                    self.cli_worker.wait()
            
            self.append_output("❌ Transkription abgebrochen")
            self.log_info("Transkription abgebrochen")
            self.is_processing = False
            self.progress_bar.setVisible(False)
            self.eta_label.setVisible(False)
            self.btn_start.setEnabled(True)
            # Progress Timer stoppen
            self.progress_timer.stop()
            
            self.btn_stop.setEnabled(False)
            self.statusBar().showMessage("Transkription abgebrochen")
            
            # Progress Tracker zurücksetzen
            self.progress_tracker.reset()
    
    def start_batch_processing(self):
        """Startet das Batch-Processing."""
        self.log_info("=== Batch-Processing gestartet ===")
        
        # Dateien holen
        files = self.input_panel.get_batch_files()
        if not files:
            QMessageBox.warning(self, tr('main_no_files_title'), tr('main_no_batch_files_msg'))
            return
        
        # Modell validieren
        model_path = self.model_panel.get_selected_model()
        if not model_path:
            QMessageBox.warning(self, tr('main_no_model_title'), tr('main_no_model_msg'))
            return
        
        # CLI-Argumente vorbereiten (ohne Input-Datei)
        try:
            cli_args = self.build_cli_arguments()
            # Input-Datei entfernen (wird pro Datei gesetzt)
            if "--input" in cli_args:
                input_index = cli_args.index("--input")
                cli_args.pop(input_index + 1)
                cli_args.pop(input_index)
        except Exception as e:
            QMessageBox.critical(self, tr('main_error'), f"{tr('main_cli_error')}\n{str(e)}")
            return
        
        # Batch-Optionen holen
        batch_options = self.input_panel.get_batch_options()
        
        # UI vorbereiten
        self.output_preview.clear()
        self.append_output("=== Batch-Processing gestartet ===\n")
        self.append_output(f"Dateien: {len(files)}\n")
        self.append_output(f"Optionen: {batch_options}\n\n")
        
        self.is_processing = True
        self.is_batch_processing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)
        self.eta_label.setVisible(True)
        self.eta_label.setText("🕒 Batch läuft...")
        self.statusBar().showMessage(f"⏳ Batch-Processing: 0/{len(files)}")
        
        # Batch-Worker starten
        self.batch_worker = BatchWorker(files, cli_args, batch_options)
        self.batch_worker.progress.connect(self.on_batch_progress)
        self.batch_worker.file_finished.connect(self.on_batch_file_finished)
        self.batch_worker.batch_finished.connect(self.on_batch_finished)
        self.batch_worker.output_received.connect(self.on_cli_output)
        self.batch_worker.start()
        
        self.log_info(f"Batch-Worker gestartet für {len(files)} Dateien")
    
    def stop_batch_processing(self):
        """Stoppt das Batch-Processing."""
        if not self.batch_worker:
            return
        
        reply = QMessageBox.question(
            self,
            tr('main_abort_batch_title'),
            tr('main_abort_batch_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_warning("Batch-Processing wird abgebrochen...")
            self.append_output("\n⏹️ Batch-Processing wird abgebrochen...\n")
            
            if self.batch_worker:
                self.batch_worker.stop()
                self.batch_worker.wait(3000)
                
                if self.batch_worker.isRunning():
                    self.batch_worker.terminate()
                    self.batch_worker.wait()
            
            self.append_output("❌ Batch-Processing abgebrochen\n")
            self.log_info("Batch-Processing abgebrochen")
            self.cleanup_after_batch()
    
    def on_batch_progress(self, current: int, total: int, filename: str):
        """Wird bei Batch-Fortschritt aufgerufen."""
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"⏳ Batch-Processing: {current}/{total} - {filename}")
        self.input_panel.batch_panel.set_progress(current, total, filename)
    
    def on_batch_file_finished(self, filepath: str, success: bool, message: str):
        """Wird aufgerufen wenn eine Datei fertig ist."""
        self.log_info(f"Batch-Datei fertig: {filepath} - {message}")
        self.reset_diarization_warning()
    
    def on_batch_finished(self, successful: int, failed: int):
        """Wird aufgerufen wenn Batch fertig ist."""
        self.log_info(f"Batch abgeschlossen: {successful} erfolgreich, {failed} fehlgeschlagen")
        
        self.append_output(f"\n{'='*60}\n")
        self.append_output("=== Batch-Processing abgeschlossen ===\n")
        self.append_output(f"✅ Erfolgreich: {successful}\n")
        self.append_output(f"❌ Fehlgeschlagen: {failed}\n")
        
        QMessageBox.information(
            self,
            "Batch abgeschlossen",
            f"Batch-Processing abgeschlossen!\n\n"
            f"✅ Erfolgreich: {successful}\n"
            f"❌ Fehlgeschlagen: {failed}"
        )
        
        self.cleanup_after_batch()
    
    def cleanup_after_batch(self):
        """Räumt nach Batch-Processing auf."""
        self.is_processing = False
        self.is_batch_processing = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.eta_label.setVisible(False)
        self.statusBar().showMessage("Batch abgeschlossen")
        self.input_panel.batch_panel.reset_progress()
        self.batch_worker = None
    
    def append_output(self, text: str):
        """
        Fügt Text zum Output-Preview hinzu (für Live-Output).
        
        Args:
            text: Text der hinzugefügt werden soll
        """
        # Unterstütze HTML-Tags für Farben
        if '<span' in text:
            self.output_preview.append(text)
        else:
            self.output_preview.append(text)
        
        # Auto-scroll zum Ende
        scrollbar = self.output_preview.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_output(self):
        """Löscht den Output-Preview."""
        self.output_preview.clear()
    
    def set_output(self, text: str):
        """
        Setzt den kompletten Output-Text (überschreibt alles).
        
        Args:
            text: Neuer Text
        """
        self.output_preview.setPlainText(text)
    
    def open_output_file(self, file_path: str):
        """
        Öffnet die Output-Datei im Standard-Texteditor.
        
        Args:
            file_path: Pfad zur Datei
        """
        import os
        import sys
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            QMessageBox.warning(self, tr('main_file_not_found_title'), f"{tr('main_file_not_found_msg')} {file_path}")
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(self, tr('main_error'), f"{tr('main_file_open_error')}\n{str(e)}")
    
    def refresh_profile_list(self):
        """Aktualisiert die Profil-Liste in der ComboBox."""
        current_text = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        
        # Aktuelle Auswahl merken
        selected_index = self.profile_combo.currentIndex()
        
        # Clear und neu befüllen
        self.profile_combo.clear()
        self.profile_combo.addItem(tr("profile_current_unsaved"))
        
        # Favoriten laden
        favorites = self.profile_manager.get_favorites()
        
        # Profile hinzufügen (Default zuerst, dann User-Profile)
        profile_names = self.profile_manager.get_profile_names()
        for name in profile_names:
            is_default = self.profile_manager.is_default_profile(name)
            is_favorite = name in favorites
            
            # Markiere Defaults und Favoriten mit Stern
            if is_default:
                display_name = f"⭐ {name}"
            elif is_favorite:
                display_name = f"⭐ {name}"
            else:
                display_name = name
            
            self.profile_combo.addItem(display_name, name)
        
        # Versuche vorherige Auswahl wiederherzustellen
        index = self.profile_combo.findText(current_text)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        else:
            self.profile_combo.setCurrentIndex(0)
        
        self.profile_combo.blockSignals(False)
        self.log_info(f"Profil-Liste aktualisiert: {len(profile_names)} Profile")

    
    def on_profile_selected(self, text: str):
        """Wird aufgerufen wenn ein Profil ausgewählt wird."""
        if text.startswith("--") or not text:
            return
        
        # Entferne Stern von Default-Profilen
        profile_name = text.replace("⭐ ", "")
        
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            self.log_warning(f"Profil nicht gefunden: {profile_name}")
            return
        
        # Settings laden
        if 'settings' in profile:
            self.settings_panel.set_settings(profile['settings'])
        
        if 'diarization' in profile:
            self.diarization_panel.set_settings(profile['diarization'])
        
        if 'output' in profile:
            self.output_panel.set_settings(profile['output'])
        
        self.statusBar().showMessage(f"📁 Profil geladen: {profile_name}")
        self.log_info(f"Profil geladen: {profile_name}")
    
    def save_current_profile(self):
        """Speichert das aktuelle Profil."""
        # Dialog für Profil-Name
        name, ok = QInputDialog.getText(
            self,
            tr('main_profile_save_title'),
            tr('main_profile_save_prompt')
        )
        
        if not ok or not name:
            return
        
        # Prüfe ob Default-Profil (überschreiben verhindern)
        if self.profile_manager.is_default_profile(name):
            QMessageBox.warning(
                self,
                tr('main_error'),
                tr('main_profile_reserved', name=name)
            )
            return
        
        # Sammle aktuelle Einstellungen
        profile = {
            "description": f"Benutzerdefiniertes Profil, erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "settings": self.settings_panel.get_settings(),
            "diarization": self.diarization_panel.get_settings(),
            "output": self.output_panel.get_settings(),
        }
        
        # Speichere
        if self.profile_manager.save_profile(name, profile):
            self.refresh_profile_list()
            self.update_profile_menus()
            
            # Wähle das neue Profil aus
            index = self.profile_combo.findData(name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            
            QMessageBox.information(
                self,
                tr('main_success'),
                tr('main_profile_saved', name=name)
            )
            self.log_info(f"Profil gespeichert: {name}")
        else:
            QMessageBox.critical(
                self,
                tr('main_error'),
                tr('main_profile_save_failed', name=name)
            )
            self.log_error(f"Fehler beim Speichern von Profil: {name}")
    
    def delete_selected_profile(self):
        """Löscht das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, tr('main_info'), tr('main_no_profile_selected'))
            return
        
        # Entferne Stern
        profile_name = current_text.replace("⭐ ", "")
        
        # Prüfe ob Default-Profil
        if self.profile_manager.is_default_profile(profile_name):
            QMessageBox.warning(
                self,
                tr('main_error'),
                tr('msg_default_profile_no_delete')
            )
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            tr('msg_delete_profile_title'),
            tr('msg_delete_profile', name=profile_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self.refresh_profile_list()
                self.update_profile_menus()
                self.profile_combo.setCurrentIndex(0)
                QMessageBox.information(self, tr('msg_profile_deleted_title'), tr('msg_profile_deleted', name=profile_name))
                self.log_info(f"Profil gelöscht: {profile_name}")
            else:
                QMessageBox.critical(self, tr('main_error'), tr('msg_profile_delete_error', name=profile_name))
                self.log_error(f"Fehler beim Löschen von Profil: {profile_name}")
    
    def duplicate_selected_profile(self):
        """Dupliziert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, tr('main_info'), tr('msg_no_profile_selected'))
            return
        
        # Entferne Stern
        source_name = current_text.replace("⭐ ", "")
        
        # Neuen Namen eingeben
        new_name, ok = QInputDialog.getText(
            self,
            tr('main_profile_duplicate_title'),
            tr('main_profile_duplicate_prompt', name=source_name),
            text=f"{source_name} (Kopie)"
        )
        
        if ok and new_name:
            if self.profile_manager.duplicate_profile(source_name, new_name):
                self.refresh_profile_list()
                self.update_profile_menus()
                # Wähle das neue Profil aus
                index = self.profile_combo.findText(new_name, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(self, tr('msg_profile_duplicated_title'), tr('msg_profile_duplicated', name=new_name))
                self.log_info(f"Profil dupliziert: {source_name} -> {new_name}")
            else:
                QMessageBox.critical(self, tr('main_error'), tr('msg_profile_duplicate_error'))
    
    def show_profile_menu(self):
        """Zeigt ein Kontextmenü für Profile-Optionen."""
        menu = QMenu(self)
        
        # Favorit markieren/entfernen
        current_text = self.profile_combo.currentText()
        if not current_text.startswith("--"):
            profile_name = current_text.replace("⭐ ", "")
            
            # Prüfe ob bereits Favorit
            favorites = self.profile_manager.get_favorites()
            if profile_name in favorites:
                unfav_action = QAction("❌ " + tr("menu_unmark_favorite"), self)
                unfav_action.triggered.connect(lambda: self.toggle_favorite(profile_name, False))
                menu.addAction(unfav_action)
            else:
                fav_action = QAction("⭐ " + tr("menu_mark_favorite"), self)
                fav_action.triggered.connect(lambda: self.toggle_favorite(profile_name, True))
                menu.addAction(fav_action)
            
            menu.addSeparator()
        
        # Export/Import
        export_action = QAction("📤 " + tr("menu_profiles_export"), self)
        export_action.triggered.connect(self.export_profile)
        menu.addAction(export_action)
        
        import_action = QAction("📥 " + tr("menu_profiles_import"), self)
        import_action.triggered.connect(self.import_profile)
        menu.addAction(import_action)
        
        # Zeige Menü unter dem Button
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def toggle_favorite(self, profile_name: str, mark_as_favorite: bool):
        """Markiert/Entmarkiert Profil als Favorit."""
        if mark_as_favorite:
            if self.profile_manager.mark_as_favorite(profile_name):
                self.log_info(f"Profil als Favorit markiert: {profile_name}")
            else:
                QMessageBox.warning(self, tr('main_error'), tr('msg_favorite_mark_error'))
        else:
            if self.profile_manager.unmark_as_favorite(profile_name):
                self.log_info(f"Favoriten-Markierung entfernt: {profile_name}")
            else:
                QMessageBox.warning(self, tr('main_error'), tr('msg_favorite_unmark_error'))
        
        self.refresh_profile_list()
        self.update_favorites_menu()
        self.update_all_profiles_menu()
    
    def export_profile(self):
        """Exportiert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, tr('main_info'), tr('msg_no_profile_to_export'))
            return
        
        profile_name = current_text.replace("⭐ ", "")
        
        # Datei-Dialog
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr('menu_profiles_export'),
            f"{profile_name}.json",
            tr('main_json_files_filter')
        )
        
        if file_path:
            if self.profile_manager.export_profile(profile_name, Path(file_path)):
                QMessageBox.information(self, tr('msg_profile_exported_title'), tr('msg_profile_exported', path=file_path))
                self.log_info(f"Profil exportiert: {profile_name} -> {file_path}")
            else:
                QMessageBox.critical(self, tr('main_error'), tr('msg_profile_export_error'))
    
    def import_profile(self):
        """Importiert ein Profil aus einer JSON-Datei."""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr('menu_profiles_import'),
            "",
            tr('main_json_files_filter')
        )
        
        if file_path:
            success, profile_name = self.profile_manager.import_profile(Path(file_path))
            
            if success:
                self.refresh_profile_list()
                self.update_profile_menus()
                # Wähle das importierte Profil aus
                index = self.profile_combo.findText(profile_name, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(self, tr('msg_profile_imported_title'), tr('msg_profile_imported', name=profile_name))
                self.log_info(f"Profil importiert: {file_path} -> {profile_name}")
            else:
                QMessageBox.critical(self, tr('main_error'), tr('msg_profile_import_error'))
    
    def update_profile_menus(self):
        """Aktualisiert alle Profil-Menüs (Favoriten+Standard und Alle)."""
        self.update_favorites_menu()
        self.update_all_profiles_menu()
    
    def update_favorites_menu(self):
        """Aktualisiert das Favoriten & Standard-Profile Menü."""
        self.favorites_menu.clear()
        
        # Hole Favoriten und Standard-Profile
        favorites = self.profile_manager.get_favorites()
        all_profiles = self.profile_manager.get_profile_names()
        standard_profiles = [name for name in all_profiles if self.profile_manager.is_default_profile(name)]
        
        # Kombiniere Favoriten und Standard (ohne Duplikate)
        combined = list(favorites)
        for std_name in standard_profiles:
            if std_name not in combined:
                combined.append(std_name)
        
        if not combined:
            no_items_action = QAction(tr("menu_no_favorites"), self)
            no_items_action.setEnabled(False)
            self.favorites_menu.addAction(no_items_action)
            return
        
        # Favoriten zuerst
        if favorites:
            for fav_name in favorites:
                is_standard = self.profile_manager.is_default_profile(fav_name)
                icon = "⭐🔧" if is_standard else "⭐"
                action = QAction(f"{icon} {fav_name}", self)
                action.triggered.connect(lambda checked, name=fav_name: self.load_profile_by_name(name))
                self.favorites_menu.addAction(action)
        
        # Separator wenn sowohl Favoriten als auch Standard-Profile existieren
        non_favorited_standards = [name for name in standard_profiles if name not in favorites]
        if favorites and non_favorited_standards:
            self.favorites_menu.addSeparator()
        
        # Standard-Profile (die nicht favorisiert sind)
        for std_name in non_favorited_standards:
            action = QAction(f"🔧 {std_name}", self)
            action.triggered.connect(lambda checked, name=std_name: self.load_profile_by_name(name))
            self.favorites_menu.addAction(action)
    
    def update_all_profiles_menu(self):
        """Aktualisiert das Alle-Profile Menü (ohne Favoriten und Standard)."""
        self.all_profiles_menu.clear()
        
        all_profiles = self.profile_manager.get_profile_names()
        favorites = self.profile_manager.get_favorites()
        
        # Filtere: Nur Profile die weder Favoriten noch Standard sind
        other_profiles = [
            name for name in all_profiles 
            if name not in favorites and not self.profile_manager.is_default_profile(name)
        ]
        
        if not other_profiles:
            no_profiles_action = QAction(tr("menu_no_other_profiles"), self)
            no_profiles_action.setEnabled(False)
            self.all_profiles_menu.addAction(no_profiles_action)
            return
        
        for profile_name in sorted(other_profiles):
            action = QAction(f"📄 {profile_name}", self)
            action.triggered.connect(lambda checked, name=profile_name: self.load_profile_by_name(name))
            self.all_profiles_menu.addAction(action)
    
    def load_profile_by_name(self, profile_name: str):
        """Lädt ein Profil anhand des Namens."""
        index = self.profile_combo.findText(profile_name, Qt.MatchFlag.MatchContains)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
    
    # ===== Wizard & Onboarding Integration =====
    
    def apply_wizard_settings(self, data: dict):
        """
        Wendet die Einstellungen aus dem Installation Wizard an.
        
        Args:
            data: Dict mit Wizard-Daten (model, token, language, theme, etc.)
        """
        self.log_info("Applying wizard settings...")
        
        # Modell setzen wenn vorhanden
        if data.get('default_model'):
            model_path = data['default_model']
            if Path(model_path).exists():
                self.model_panel.set_model_path(model_path)
                self.log_info(f"Model set from wizard: {model_path}")
        
        # HF Token setzen wenn vorhanden
        if data.get('hf_token'):
            self.diarization_panel.set_hf_token(data['hf_token'])
            self.log_info("HF Token set from wizard")
        
        # Threads setzen
        if data.get('default_threads'):
            self.settings_panel.set_threads(data['default_threads'])
            self.log_info(f"Threads set from wizard: {data['default_threads']}")
        
        # Sprache setzen (ohne Neustart beim ersten Wizard-Durchlauf)
        if data.get('ui_language'):
            language = data['ui_language']
            set_language(language)
            self.history_manager.save_user_preference('ui_language', language)
            self.log_info(f"Language set from wizard: {language}")
            # Keine MessageBox beim ersten Setup!
        
        # Theme setzen
        if data.get('preferred_theme'):
            theme = data['preferred_theme']
            if theme == 'dark' and self.theme_manager.get_current_theme() != 'dark':
                self.toggle_theme()
            elif theme == 'light' and self.theme_manager.get_current_theme() != 'light':
                self.toggle_theme()
        
        # User Preferences anwenden
        if data.get('auto_open_transcript'):
            self.output_panel.set_auto_open(True)
        
        self.log_info("Wizard settings applied successfully")
    
    def start_onboarding(self):
        """Startet das Onboarding-Tutorial."""
        self.log_info("Starting onboarding tutorial...")
        # Als Instanzvariable speichern, damit es nicht vom GC entfernt wird
        self.history_manager.mark_onboarding_completed(complete=False)  # Vorab als nicht abgeschlossen markieren
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
            # Als completed markieren damit nicht mehr gefragt wird
            self.history_manager.mark_onboarding_completed()
    
    def change_language(self, language: str):
        """
        Ändert die UI-Sprache.
        
        Args:
            language: "de" oder "en"
        """
        # Prüfen ob die Sprache bereits gesetzt ist
        current_language = get_translation_manager().get_current_language()
        if current_language == language:
            # Sprache ist bereits gesetzt - nichts tun
            self.log_info(f"Language already set to: {language}")
            return
        
        # Sprache in den Einstellungen speichern
        set_language(language)
        self.history_manager.save_user_preference('ui_language', language)
        
        self.log_info(f"Language changed to: {language}")
        
        # MessageBox anzeigen und App neu starten
        self.restart_application(language)
    
    def refresh_ui(self):
        """Aktualisiert alle UI-Texte nach einem Sprachwechsel."""
        # Window Title
        self.setWindowTitle(tr("app_title"))
        
        # GUI Title
        self.title_label.setText(tr("gui_title"))
        
        # Profile Section
        self.profile_label.setText("📁 " + tr("profile_label"))
        
        # Profile Combo Box - erste Item
        current_text = self.profile_combo.currentText()
        if current_text == "-- Aktuell (nicht gespeichert) --" or current_text == "-- Current (not saved) --":
            self.profile_combo.setItemText(0, tr("profile_current_unsaved")) 
        
        # Profile Buttons Tooltips aktualisieren
        for btn in self.findChildren(QPushButton):
            text = btn.text()
            if text == "💾":
                btn.setToolTip(tr("profile_save_tooltip"))
            elif text == "📋":
                btn.setToolTip(tr("profile_duplicate_tooltip"))
            elif text == "❌" and btn.width() <= 35:  # Kleiner Button = Profil-Delete-Button
                btn.setToolTip(tr("profile_delete_tooltip"))
            elif text == "⋮":
                btn.setToolTip(tr("profile_menu_tooltip"))
        
        # Output Preview Title
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
        
        # Menu Bar - Titel aktualisieren
        if hasattr(self, 'file_menu'):
            self.file_menu.setTitle("📁 " + tr("menu_file"))
            self.recent_files_menu.setTitle("🕒 " + tr("menu_recent_files"))
            self.recent_models_menu.setTitle("🤖 " + tr("menu_recent_models"))
            
            # Menu Actions aktualisieren
            for action in self.file_menu.actions():
                text = action.text()
                if '📦' in text:
                    action.setText("📦 " + tr("menu_batch"))
                elif '🗑️' in text and ('History' in text or 'Verlauf' in text):
                    action.setText("🗑️ " + tr("menu_clear_history"))
                elif '❌' in text:
                    action.setText("❌ " + tr("menu_quit"))
        
        # Profile Menu
        if hasattr(self, 'profile_menu'):
            self.profile_menu.setTitle("📋 " + tr("menu_profiles_title"))
            self.favorites_menu.setTitle("⭐ " + tr("menu_profiles_favorites"))
            self.all_profiles_menu.setTitle("📋 " + tr("menu_profiles_all"))
            
            # Profile Menu Actions aktualisieren
            for action in self.profile_menu.actions():
                text = action.text()
                if '📤' in text:
                    action.setText("📤 " + tr("menu_profiles_export"))
                elif '📥' in text:
                    action.setText("📥 " + tr("menu_profiles_import"))
        
        # Help Menu
        if hasattr(self, 'help_menu'):
            self.help_menu.setTitle("❓ " + tr("menu_help"))
            
            # Help Menu Actions aktualisieren
            for action in self.help_menu.actions():
                text = action.text()
                if '🎓' in text:
                    action.setText("🎓 " + tr("menu_start_onboarding"))
                elif '⌨️' in text:
                    action.setText("⌨️ " + tr("menu_shortcuts"))
                elif 'ℹ️' in text:
                    action.setText("ℹ️ " + tr("menu_about"))
        
        # Theme Switch Tooltip
        self.update_theme_switch()
        
        # Sprach-Dropdown Tooltip aktualisieren
        if hasattr(self, 'language_combo'):
            self.language_combo.setToolTip(tr("menu_language"))
        
        # Menü-Inhalte aktualisieren
        self.update_recent_files_menu()
        self.update_recent_models_menu()
        self.update_favorites_menu()
        self.update_all_profiles_menu()
        
        # Panels aktualisieren (falls sie refresh_ui Methoden haben)
        if hasattr(self.input_panel, 'refresh_ui'):
            self.input_panel.refresh_ui()
        if hasattr(self.model_panel, 'refresh_ui'):
            self.model_panel.refresh_ui()
        if hasattr(self.settings_panel, 'refresh_ui'):
            self.settings_panel.refresh_ui()
        if hasattr(self.diarization_panel, 'refresh_ui'):
            self.diarization_panel.refresh_ui()
        if hasattr(self.output_panel, 'refresh_ui'):
            self.output_panel.refresh_ui()
        
        self.log_info("UI-Texte aktualisiert")
    
    def restart_application(self, language: str):
        """
        Startet die Anwendung neu, um die Sprachänderung vollständig zu übernehmen.
        
        Args:
            language: Die neue Sprache ("de" oder "en")
        """
        # Benachrichtigung anzeigen
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(tr("msg_restart_app_title"))
        msg.setText(tr("msg_restart_app_text"))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        self.log_info(f"Restarting application with language: {language}")
        
        # Python-Interpreter und Arbeitsverzeichnis ermitteln
        python = sys.executable
        
        # Erstelle den Neustart-Befehl: python -m src.gui.app
        # Dies funktioniert unabhängig davon, wie die App ursprünglich gestartet wurde
        restart_cmd = [python, "-m", "src.gui.app"]
        
        # Working Directory ermitteln (Projekt-Root)
        # Falls wir im src/gui Verzeichnis sind, gehen wir zwei Ebenen hoch
        cwd = os.getcwd()
        
        self.log_info(f"Restart command: {' '.join(restart_cmd)} in {cwd}")
        
        # Neuen Prozess im Hintergrund starten
        subprocess.Popen(restart_cmd, cwd=cwd)
        
        # Aktuellen Prozess beenden
        QApplication.quit()
    
    def on_language_combo_changed(self, index: int):
        """Wird aufgerufen wenn die Sprache im Dropdown geändert wird."""
        language = self.language_combo.itemData(index)
        if language:
            self.change_language(language)
    
    def update_language_combo(self):
        """Aktualisiert die Auswahl im Sprach-Dropdown."""
        current_language = get_translation_manager().get_current_language()
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
    
    def check_model_updates(self):
        """Prüft auf Model-Updates (wird beim Start aufgerufen)."""
        model_path = self.model_panel.get_model_path()
        
        if not model_path or not Path(model_path).exists():
            return
        
        # Prüfen ob User Update-Check aktiviert hat
        check_updates = self.history_manager.get_user_preference('check_model_updates', True)
        if not check_updates:
            return
        
        from .model_utils import check_model_updates_with_cache
        
        # Im Background prüfen
        def do_check():
            result = check_model_updates_with_cache(model_path, force=False)
            
            if result and result.get('update_available'):
                # Benachrichtigung in Main-Thread
                QTimer.singleShot(0, lambda: self.show_update_notification(result))
        
        # In separatem Thread um UI nicht zu blockieren
        import threading
        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()
    
    def show_update_notification(self, update_info: dict):
        """
        Zeigt eine Benachrichtigung über verfügbares Model-Update.
        
        Args:
            update_info: Dict mit Update-Informationen
        """
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
            url = update_info.get('download_url', 'https://huggingface.co/ggerganov/whisper.cpp')
            webbrowser.open(url)
    
    def closeEvent(self, event):
        """Wird aufgerufen wenn das Fenster geschlossen wird."""
        # Prüfe ob Prozess läuft
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
            
            # Prozess stoppen
            if self.cli_worker:
                self.cli_worker.stop()
                self.cli_worker.wait(2000)
        
        # Session speichern
        self.save_current_session()
        
        self.log_info("=== V-SpeechFlow GUI beendet ===")
        event.accept()
