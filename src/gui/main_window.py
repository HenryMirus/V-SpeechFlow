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
)
from PyQt6.QtCore import Qt
from .input_panel import InputPanel
from .model_panel import ModelPanel
from .settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    """Hauptfenster der V-SpeechFlow GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V-SpeechFlow - Speech to Text mit Speaker Diarization")
        self.setGeometry(100, 100, 1400, 900)
        
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
        
        # TODO: Output Settings Panel wird hier später eingefügt
        
        left_layout.addStretch()
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll, 2)  # 2/3 der Breite
        
        # Rechte Seite: Output Preview + Control Buttons
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        output_title = QLabel("📋 Output Preview")
        output_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        right_layout.addWidget(output_title)
        
        # Output Text Area (wird später für Live-Output genutzt)
        self.output_preview = QLabel("Output wird hier angezeigt...")
        self.output_preview.setStyleSheet("color: gray; background-color: #f5f5f5; padding: 10px; border-radius: 4px;")
        self.output_preview.setWordWrap(True)
        self.output_preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(self.output_preview)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Start Transkription")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_start.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ Stop")
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_transcription)
        button_layout.addWidget(self.btn_stop)
        
        right_layout.addLayout(button_layout)
        
        main_layout.addWidget(right_panel, 1)  # 1/3 der Breite
        
        # Status Bar
        self.statusBar().showMessage("Bereit")
    
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
    
    def on_recording_started(self):
        """Wird aufgerufen wenn Live-Recording startet."""
        self.statusBar().showMessage("🔴 Aufnahme läuft...")
    
    def on_recording_stopped(self):
        """Wird aufgerufen wenn Live-Recording endet."""
        self.statusBar().showMessage("Aufnahme beendet")
    
    def start_transcription(self):
        """Startet die Transkription."""
        # TODO: Validierung + CLI-Prozess starten
        self.statusBar().showMessage("⏳ Transkription läuft...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def stop_transcription(self):
        """Stoppt die Transkription."""
        # TODO: Prozess beenden
        self.statusBar().showMessage("Transkription beendet")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

