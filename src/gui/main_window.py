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
        
        # Logging einrichten
        self.setup_logging()
        self.log_info("V-SpeechFlow GUI gestartet")
        
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
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
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
        
        btn_delete_profile = QPushButton("❌")
        btn_delete_profile.setToolTip("Profil löschen")
        btn_delete_profile.setFixedWidth(35)
        btn_delete_profile.clicked.connect(self.delete_selected_profile)
        profile_layout.addWidget(btn_delete_profile)
        
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
        output_title.setStyleSheet("font-weight: bold; font-size: 12px;")
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
        self.progress_bar.setFormat("%p% - Verarbeitung läuft...")
        right_layout.addWidget(self.progress_bar)
        
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
    
    def on_file_selected(self, file_path: str):
        """Wird aufgerufen wenn eine Datei ausgewählt wird."""
        self.statusBar().showMessage(f"Datei ausgewählt: {file_path}")
    
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
        log_dir = Path.home() / ".vspeechflow" / "logs"
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
    
    def update_status(self):
        """Regelmäßige Status-Updates."""
        # Hier könnten später Auto-Save, etc. implementiert werden
        pass
    
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
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.statusBar().showMessage("⏳ Transkription läuft...")
        
        # === CLI-Worker starten ===
        self.log_info("CLI-Worker wird gestartet...")
        self.cli_worker = CLIWorker(cli_args)
        self.cli_worker.output_received.connect(self.on_cli_output)
        self.cli_worker.error_received.connect(self.on_cli_error)
        self.cli_worker.process_finished.connect(self.on_cli_finished)
        self.cli_worker.start()
        self.log_info("CLI-Worker gestartet")
    
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
        
        return args
    
    def on_cli_output(self, text: str):
        """Wird aufgerufen wenn CLI stdout Output empfängt."""
        self.append_output(text)
    
    def on_cli_error(self, text: str):
        """Wird aufgerufen wenn CLI stderr Output empfängt."""
        # Errors in roter Farbe anzeigen
        self.append_output(f"<span style='color: red;'>[ERROR] {text}</span>")
    
    def on_cli_finished(self, return_code: int):
        """Wird aufgerufen wenn der CLI-Prozess beendet ist."""
        self.log_info(f"CLI-Prozess beendet mit Exit-Code: {return_code}")
        self.is_processing = False
        self.progress_bar.setVisible(False)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        if return_code == 0:
            # Erfolg
            self.append_output("\n" + "="*50)
            self.append_output("✅ Transkription erfolgreich abgeschlossen!")
            self.append_output("="*50)
            
            # Output-Datei Pfad anzeigen
            input_file = self.input_panel.get_selected_file()
            output_path = self.output_panel.get_output_path(input_file)
            self.append_output(f"\n💾 Ausgabe gespeichert: {output_path}")
            
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
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.statusBar().showMessage("Transkription abgebrochen")
    
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
        
        # Profile hinzufügen (Default zuerst)
        profile_names = self.profile_manager.get_profile_names()
        for name in profile_names:
            is_default = self.profile_manager.is_default_profile(name)
            display_name = f"⭐ {name}" if is_default else name
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
        
        self.log_info("=== V-SpeechFlow GUI beendet ===")
        event.accept()

