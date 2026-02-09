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
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from .input_panel import InputPanel
from .model_panel import ModelPanel
from .settings_panel import SettingsPanel
from .diarization_panel import DiarizationPanel
from .output_panel import OutputPanel
from .workers import CLIWorker
from .profiles import ProfileManager
from .history import HistoryManager
from .batch_panel import BatchPanel
from .theme import ThemeManager
from .progress_tracker import ProgressTracker
from .translations import tr, set_language, get_translation_manager
from .onboarding import OnboardingManager
import logging
from datetime import datetime
from pathlib import Path


class MainWindow(QMainWindow):
    """Hauptfenster der V-SpeechFlow GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V-SpeechFlow - Speech to Text mit Speaker Diarization")
        self.setGeometry(100, 100, 1400, 900)
        
        # Worker für CLI-Prozess
        self.cli_worker = None
        self.is_processing = False
        
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
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Titel
        title = QLabel("V-SpeechFlow GUI")
        title.setStyleSheet("font-size: 19px; font-weight: bold;")
        left_layout.addWidget(title)
        
        # Profile-Auswahl
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("📁 Profil:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("-- Aktuell (nicht gespeichert) --")
        self.refresh_profile_list()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        profile_layout.addWidget(self.profile_combo)
        
        btn_save_profile = QPushButton("💾")
        btn_save_profile.setToolTip("Aktuelles Profil speichern")
        btn_save_profile.setFixedWidth(35)
        btn_save_profile.clicked.connect(self.save_current_profile)
        profile_layout.addWidget(btn_save_profile)
        
        btn_duplicate_profile = QPushButton("📋")
        btn_duplicate_profile.setToolTip("Profil duplizieren")
        btn_duplicate_profile.setFixedWidth(35)
        btn_duplicate_profile.clicked.connect(self.duplicate_selected_profile)
        profile_layout.addWidget(btn_duplicate_profile)
        
        btn_delete_profile = QPushButton("❌")
        btn_delete_profile.setToolTip("Profil löschen")
        btn_delete_profile.setFixedWidth(35)
        btn_delete_profile.clicked.connect(self.delete_selected_profile)
        profile_layout.addWidget(btn_delete_profile)
        
        # Mehr Options-Button (für Export/Import)
        btn_profile_menu = QPushButton("⋮")
        btn_profile_menu.setToolTip("Weitere Optionen")
        btn_profile_menu.setFixedWidth(35)
        btn_profile_menu.clicked.connect(self.show_profile_menu)
        profile_layout.addWidget(btn_profile_menu)
        
        left_layout.addLayout(profile_layout)
        
        # Input Panel
        self.input_panel = InputPanel()
        self.input_panel.file_selected.connect(self.on_file_selected)
        self.input_panel.recording_started.connect(self.on_recording_started)
        self.input_panel.recording_stopped.connect(self.on_recording_stopped)
        left_layout.addWidget(self.input_panel)
        
        # Model Panel
        self.model_panel = ModelPanel()
        self.model_panel.model_selected.connect(self.on_model_selected)
        left_layout.addWidget(self.model_panel)
        
        # Settings Panel
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.on_settings_changed)
        left_layout.addWidget(self.settings_panel)
        
        # Diarization Panel
        self.diarization_panel = DiarizationPanel()
        self.diarization_panel.diarization_changed.connect(self.on_diarization_changed)
        left_layout.addWidget(self.diarization_panel)
        
        # Output Panel
        self.output_panel = OutputPanel()
        self.output_panel.output_changed.connect(self.on_output_changed)
        left_layout.addWidget(self.output_panel)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll, 2)  # 2/3 der Breite
        
        # Rechte Seite: Output Preview + Control Buttons
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        output_title = QLabel("📋 Output Preview / Live-Transkription")
        output_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(output_title)
        
        # Output Text Area mit QTextEdit für Live-Output
        self.output_preview = QTextEdit()
        self.output_preview.setReadOnly(True)
        self.output_preview.setPlaceholderText(
            "Der Transkriptions-Output wird hier in Echtzeit angezeigt...\n\n"
            "Starte eine Transkription um den Output zu sehen."
        )
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
        self.progress_bar.setFormat("%p% - Verarbeitung läuft...")
        right_layout.addWidget(self.progress_bar)
        
        # ETA Label
        self.eta_label = QLabel("")
        self.eta_label.setVisible(False)
        self.eta_label.setStyleSheet("color: gray; font-size: 11px; text-align: center;")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.eta_label)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Start Transkription")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_start.setToolTip("Start Transkription (Strg+Enter)")
        self.btn_start.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ Stop")
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setToolTip("Transkription abbrechen (Escape)")
        self.btn_stop.clicked.connect(self.stop_transcription)
        button_layout.addWidget(self.btn_stop)
        
        right_layout.addLayout(button_layout)
        
        main_layout.addWidget(right_panel, 1)  # 1/3 der Breite
        
        # Status Bar
        self.statusBar().showMessage("Bereit")
        
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
    
    def on_file_selected(self, file_path: str):
        """Wird aufgerufen wenn eine Datei ausgewählt wird."""
        self.statusBar().showMessage(f"Datei ausgewählt: {file_path}")
    
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
        
        # UI Language
        if 'ui_language' in config:
            ui_lang = config['ui_language']
            set_language(ui_lang)
            print(f"  ✓ UI Language: {ui_lang}")
        
        # Theme
        if 'preferred_theme' in config:
            theme = config['preferred_theme']
            self.apply_theme(theme)
            print(f"  ✓ Theme: {theme}")
        
        print("=== Initial-Config erfolgreich geladen ===")
        self.statusBar().showMessage("Willkommen! Wizard-Konfiguration geladen", 3000)
    
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
                
                self.statusBar().showMessage(f"Profil '{profile_name}' wiederhergestellt", 3000)
                return
            else:
                self.log_warning(f"Profil '{profile_name}' nicht gefunden")
                print(f"  ✗ Profil nicht gefunden, lade Session-Daten")
        
        # Kein Profil oder nicht gefunden - lade Session-Daten direkt
        print("  ✓ Lade Session-Daten")
        
        # Input-Datei (nur wenn existent)
        if 'input_file' in session_data:
            input_file = session_data['input_file']
            if Path(input_file).exists():
                self.input_panel.set_file_path(input_file)
                print(f"    - Input: {Path(input_file).name}")
        
        # Model
        if 'model' in session_data:
            model_path = session_data['model']
            if Path(model_path).exists():
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
        self.statusBar().showMessage("Letzte Session wiederhergestellt", 3000)
    
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
        
        # Datei-Menü
        file_menu = menubar.addMenu("📁 Datei")
        
        # Recent Files Submenu
        self.recent_files_menu = QMenu("🕒 Zuletzt verwendet", self)
        file_menu.addMenu(self.recent_files_menu)
        self.update_recent_files_menu()
        
        file_menu.addSeparator()
        
        # Recent Models Submenu
        self.recent_models_menu = QMenu("🤖 Letzte Modelle", self)
        file_menu.addMenu(self.recent_models_menu)
        self.update_recent_models_menu()
        
        file_menu.addSeparator()
        
        # History löschen
        clear_history_action = QAction("🗑️ History löschen", self)
        clear_history_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_history_action)
        
        file_menu.addSeparator()
        
        # Beenden
        quit_action = QAction("❌ Beenden", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Profile-Menü
        profile_menu = menubar.addMenu("📋 Profile")
        
        # Favoriten Submenu
        self.favorites_menu = QMenu("⭐ Favoriten", self)
        profile_menu.addMenu(self.favorites_menu)
        self.update_favorites_menu()
        
        profile_menu.addSeparator()
        
        # Export Profil
        export_profile_action = QAction("📤 Profil exportieren...", self)
        export_profile_action.triggered.connect(self.export_profile)
        profile_menu.addAction(export_profile_action)
        
        # Import Profil
        import_profile_action = QAction("📥 Profil importieren...", self)
        import_profile_action.triggered.connect(self.import_profile)
        profile_menu.addAction(import_profile_action)
        
        # Einstellungen-Menü
        settings_menu = menubar.addMenu("⚙️ Einstellungen")
        
        # Theme Toggle
        self.theme_action = QAction("🌙 Dark Mode", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(self.theme_manager.get_current_theme() == 'dark')
        self.theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(self.theme_action)
        
        settings_menu.addSeparator()
        
        # Language Submenu
        language_menu = QMenu("🌍 Sprache / Language", self)
        settings_menu.addMenu(language_menu)
        
        # Deutsch
        lang_de_action = QAction("🇩🇪 Deutsch", self)
        lang_de_action.setCheckable(True)
        lang_de_action.setChecked(get_translation_manager().get_current_language() == "de")
        lang_de_action.triggered.connect(lambda: self.change_language("de"))
        language_menu.addAction(lang_de_action)
        
        # English
        lang_en_action = QAction("🇺🇸 English", self)
        lang_en_action.setCheckable(True)
        lang_en_action.setChecked(get_translation_manager().get_current_language() == "en")
        lang_en_action.triggered.connect(lambda: self.change_language("en"))
        language_menu.addAction(lang_en_action)
        
        settings_menu.addSeparator()
        
        # Letzte Einstellungen laden
        load_last_settings_action = QAction("⏮️ Letzte Einstellungen laden", self)
        load_last_settings_action.triggered.connect(self.load_last_settings)
        settings_menu.addAction(load_last_settings_action)
        
        # Batch-Processing
        batch_action = QAction("📦 Batch-Processing", self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self.open_batch_window)
        settings_menu.addAction(batch_action)
        
        # Hilfe-Menü
        help_menu = menubar.addMenu("❓ Hilfe")
        
        # Tutorial/Onboarding
        tutorial_action = QAction("🎓 Tutorial starten", self)
        tutorial_action.triggered.connect(self.start_onboarding)
        help_menu.addAction(tutorial_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("ℹ️ Über V-SpeechFlow", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        self.log_info("Menu-Bar erstellt")
    
    def update_recent_files_menu(self):
        """Aktualisiert das Recent Files Menü."""
        self.recent_files_menu.clear()
        
        recent_files = self.history_manager.get_recent_input_files(limit=10)
        
        if not recent_files:
            no_files_action = QAction("(Keine zuletzt verwendeten Dateien)", self)
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
            no_models_action = QAction("(Keine zuletzt verwendeten Modelle)", self)
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
                "Datei nicht gefunden",
                f"Die Datei existiert nicht mehr:\n{file_path}"
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
                "Modell nicht gefunden",
                f"Das Modell existiert nicht mehr:\n{model_path}"
            )
            self.history_manager.remove_model(model_path)
            self.update_recent_models_menu()
    
    def clear_history(self):
        """Löscht die komplette History."""
        reply = QMessageBox.question(
            self,
            "History löschen?",
            "Möchten Sie wirklich die komplette History löschen?\\n\\n"
            "Dies beinhaltet:\\n"
            "• Zuletzt verwendete Dateien\\n"
            "• Zuletzt verwendete Modelle\\n"
            "• Letzte Einstellungen",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_history()
            self.update_recent_files_menu()
            self.update_recent_models_menu()
            self.log_info("History gelöscht")
            QMessageBox.information(self, "Fertig", "History wurde gelöscht.")
    
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
    
    def open_batch_window(self):
        """Öffnet das Batch-Processing Fenster."""
        from .batch_window import BatchWindow
        
        # Settings-Getter Funktion erstellen
        def get_current_cli_args():
            return self.build_cli_arguments()
        
        batch_window = BatchWindow(self, get_current_cli_args)
        batch_window.show()
        self.log_info("Batch-Processing Fenster geöffnet")
    
    def toggle_theme(self):
        """Wechselt zwischen Light und Dark Mode."""
        current = self.theme_manager.get_current_theme()
        new_theme = 'dark' if current == 'light' else 'light'
        
        self.apply_theme(new_theme)
        self.theme_manager.save_theme_preference(new_theme)
        
        # Update Menu-Text
        if new_theme == 'dark':
            self.theme_action.setText("☀️ Light Mode")
        else:
            self.theme_action.setText("🌙 Dark Mode")
        
        self.log_info(f"Theme gewechselt zu: {new_theme}")
    
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
            QMessageBox.warning(self, "Bereits aktiv", "Eine Transkription läuft bereits.")
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
            error_message = "Bitte beheben Sie folgende Fehler:\n\n" + "\n".join(validation_errors)
            QMessageBox.critical(self, "Validierungsfehler", error_message)
            return
        
        # === CLI-Argumente zusammenstellen ===
        try:
            cli_args = self.build_cli_arguments()
            self.log_info(f"CLI-Argumente: {' '.join(cli_args)}")
        except Exception as e:
            self.log_error(f"Fehler beim Erstellen der CLI-Argumente: {str(e)}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen der CLI-Argumente:\n{str(e)}")
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
                "Fertig!",
                f"Transkription erfolgreich abgeschlossen!\n\nDatei gespeichert unter:\n{output_path}"
            )
        else:
            # Fehler
            self.append_output("\n" + "="*50)
            self.append_output(f"❌ Transkription fehlgeschlagen (Exit Code: {return_code})")
            self.append_output("="*50)
            
            self.statusBar().showMessage(f"❌ Transkription fehlgeschlagen (Code: {return_code})")
            
            QMessageBox.critical(
                self,
                "Fehler",
                f"Transkription fehlgeschlagen mit Exit Code {return_code}.\n\n"
                "Bitte prüfen Sie die Fehlerausgabe im Output-Fenster."
            )
        
        # Worker cleanup
        if self.cli_worker:
            self.cli_worker.deleteLater()
            self.cli_worker = None
    
    def stop_transcription(self):
        """Stoppt die Transkription."""
        if not self.is_processing or not self.cli_worker:
            return
        
        self.log_info("Stop Transkription angefordert")
        
        reply = QMessageBox.question(
            self,
            "Transkription abbrechen?",
            "Möchten Sie die laufende Transkription wirklich abbrechen?",
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
            QMessageBox.warning(self, "Datei nicht gefunden", f"Die Datei {file_path} wurde nicht gefunden.")
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Konnte Datei nicht öffnen:\n{str(e)}")
    
    def refresh_profile_list(self):
        """Aktualisiert die Profil-Liste in der ComboBox."""
        current_text = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)
        
        # Aktuelle Auswahl merken
        selected_index = self.profile_combo.currentIndex()
        
        # Clear und neu befüllen
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Aktuell (nicht gespeichert) --")
        
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
            "Profil speichern",
            "Profil-Name eingeben:"
        )
        
        if not ok or not name:
            return
        
        # Prüfe ob Default-Profil (überschreiben verhindern)
        if self.profile_manager.is_default_profile(name):
            QMessageBox.warning(
                self,
                "Fehler",
                f"Der Name '{name}' ist für ein Standard-Profil reserviert.\n"
                "Bitte wählen Sie einen anderen Namen."
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
            
            # Wähle das neue Profil aus
            index = self.profile_combo.findData(name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            
            QMessageBox.information(
                self,
                "Erfolg",
                f"Profil '{name}' wurde gespeichert!"
            )
            self.log_info(f"Profil gespeichert: {name}")
        else:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Profil '{name}' konnte nicht gespeichert werden."
            )
            self.log_error(f"Fehler beim Speichern von Profil: {name}")
    
    def delete_selected_profile(self):
        """Löscht das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, "Info", "Kein Profil ausgewählt.")
            return
        
        # Entferne Stern
        profile_name = current_text.replace("⭐ ", "")
        
        # Prüfe ob Default-Profil
        if self.profile_manager.is_default_profile(profile_name):
            QMessageBox.warning(
                self,
                "Fehler",
                "Standard-Profile können nicht gelöscht werden."
            )
            return
        
        # Bestätigung
        reply = QMessageBox.question(
            self,
            "Profil löschen?",
            f"Möchten Sie das Profil '{profile_name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self.refresh_profile_list()
                self.profile_combo.setCurrentIndex(0)
                QMessageBox.information(self, "Erfolg", f"Profil '{profile_name}' wurde gelöscht.")
                self.log_info(f"Profil gelöscht: {profile_name}")
            else:
                QMessageBox.critical(self, "Fehler", f"Profil '{profile_name}' konnte nicht gelöscht werden.")
                self.log_error(f"Fehler beim Löschen von Profil: {profile_name}")
    
    def duplicate_selected_profile(self):
        """Dupliziert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, "Info", "Kein Profil zum Duplizieren ausgewählt.")
            return
        
        # Entferne Stern
        source_name = current_text.replace("⭐ ", "")
        
        # Neuen Namen eingeben
        new_name, ok = QInputDialog.getText(
            self,
            "Profil duplizieren",
            f"Neuer Name für die Kopie von '{source_name}':",
            text=f"{source_name} (Kopie)"
        )
        
        if ok and new_name:
            if self.profile_manager.duplicate_profile(source_name, new_name):
                self.refresh_profile_list()
                # Wähle das neue Profil aus
                index = self.profile_combo.findText(new_name, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(self, "Erfolg", f"Profil wurde als '{new_name}' dupliziert.")
                self.log_info(f"Profil dupliziert: {source_name} -> {new_name}")
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht dupliziert werden.")
    
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
                unfav_action = QAction("⭐ Als Favorit entfernen", self)
                unfav_action.triggered.connect(lambda: self.toggle_favorite(profile_name, False))
                menu.addAction(unfav_action)
            else:
                fav_action = QAction("⭐ Als Favorit markieren", self)
                fav_action.triggered.connect(lambda: self.toggle_favorite(profile_name, True))
                menu.addAction(fav_action)
            
            menu.addSeparator()
        
        # Export/Import
        export_action = QAction("📤 Profil exportieren...", self)
        export_action.triggered.connect(self.export_profile)
        menu.addAction(export_action)
        
        import_action = QAction("📥 Profil importieren...", self)
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
                QMessageBox.warning(self, "Fehler", "Profil konnte nicht als Favorit markiert werden.")
        else:
            if self.profile_manager.unmark_as_favorite(profile_name):
                self.log_info(f"Favoriten-Markierung entfernt: {profile_name}")
            else:
                QMessageBox.warning(self, "Fehler", "Favoriten-Markierung konnte nicht entfernt werden.")
        
        self.refresh_profile_list()
        self.update_favorites_menu()
    
    def export_profile(self):
        """Exportiert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()
        
        if current_text.startswith("--"):
            QMessageBox.information(self, "Info", "Kein Profil zum Exportieren ausgewählt.")
            return
        
        profile_name = current_text.replace("⭐ ", "")
        
        # Datei-Dialog
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Profil exportieren",
            f"{profile_name}.json",
            "JSON Dateien (*.json)"
        )
        
        if file_path:
            if self.profile_manager.export_profile(profile_name, Path(file_path)):
                QMessageBox.information(self, "Erfolg", f"Profil wurde exportiert nach:\n{file_path}")
                self.log_info(f"Profil exportiert: {profile_name} -> {file_path}")
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht exportiert werden.")
    
    def import_profile(self):
        """Importiert ein Profil aus einer JSON-Datei."""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Profil importieren",
            "",
            "JSON Dateien (*.json)"
        )
        
        if file_path:
            success, profile_name = self.profile_manager.import_profile(Path(file_path))
            
            if success:
                self.refresh_profile_list()
                # Wähle das importierte Profil aus
                index = self.profile_combo.findText(profile_name, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(self, "Erfolg", f"Profil '{profile_name}' wurde importiert.")
                self.log_info(f"Profil importiert: {file_path} -> {profile_name}")
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht importiert werden.\nÜberprüfen Sie die Datei.")
    
    def update_favorites_menu(self):
        """Aktualisiert das Favoriten-Menü."""
        self.favorites_menu.clear()
        
        favorites = self.profile_manager.get_favorites()
        
        if not favorites:
            no_fav_action = QAction("(Keine Favoriten)", self)
            no_fav_action.setEnabled(False)
            self.favorites_menu.addAction(no_fav_action)
            return
        
        for fav_name in favorites:
            action = QAction(f"⭐ {fav_name}", self)
            action.triggered.connect(lambda checked, name=fav_name: self.load_profile_by_name(name))
            self.favorites_menu.addAction(action)
    
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
        self.onboarding_manager = OnboardingManager(self)
        self.onboarding_manager.start()
    
    def offer_onboarding(self):
        """Bietet das Onboarding an (falls noch nicht absolviert)."""
        reply = QMessageBox.question(
            self,
            "Tutorial verfügbar",
            "Möchten Sie ein kurzes Tutorial durchlaufen?\n\n"
            "Es erklärt die wichtigsten Funktionen von V-SpeechFlow.",
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
        set_language(language)
        self.history_manager.save_user_preference('ui_language', language)
        
        QMessageBox.information(
            self,
            "Sprache geändert / Language Changed",
            "Die Sprache wurde geändert.\n"
            "Bitte starten Sie die Anwendung neu um alle Änderungen zu sehen.\n\n"
            "Language has been changed.\n"
            "Please restart the application to see all changes."
        )
        
        self.log_info(f"Language changed to: {language}")
    
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
            "Model-Update verfügbar",
            f"Ein Update für das Modell '{model_name}' ist verfügbar.\n\n"
            f"Lokale Version: {local_size} MB\n"
            f"Neue Version: {remote_size} MB\n\n"
            "Möchten Sie die Download-Seite öffnen?",
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
                "Transkription läuft",
                "Eine Transkription ist noch aktiv. Wirklich beenden?",
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

