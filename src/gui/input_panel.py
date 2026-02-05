"""
Input Panel für Datei- und Live-Aufnahme-Verwaltung

Ermöglicht Auswahl von Audio-Dateien oder Live-Recording vom Mikrofon.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTabWidget,
    QFileDialog,
    QProgressBar,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from .utils import list_audio_devices
from .macos_utils import get_hf_token_from_keychain, is_mac


class InputPanel(QWidget):
    """Panel für Audio-Input (Datei oder Live)."""
    
    # Signals
    file_selected = pyqtSignal(str)  # Signal wenn Datei ausgewählt
    recording_started = pyqtSignal()  # Signal wenn Live-Recording startet
    recording_stopped = pyqtSignal()  # Signal wenn Live-Recording endet
    
    SUPPORTED_FORMATS = ("mp3", "m4a", "wav", "flac", "ogg")
    
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.device_list = []
        self.is_recording = False
        
        # Drag & Drop aktivieren auf dem ganzen Panel
        self.setAcceptDrops(True)
        
        # UI erst erstellen
        self.init_ui()
        
        # DANN Mikrofone laden (nach UI-Erstellung)
        self.refresh_devices()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Tab Widget: Datei vs Live
        tabs = QTabWidget()
        tabs.addTab(self.create_file_tab(), "📁 Datei")
        tabs.addTab(self.create_live_tab(), "🎤 Live")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def create_file_tab(self):
        """Erstellt den Tab für Datei-Auswahl."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titel
        title = QLabel("Audio-Datei auswählen")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Datei-Pfad Display (mit Drag & Drop)
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("Ziehe Datei hier hin oder klicke zum Auswählen...")
        self.file_path_display.setDragEnabled(False)
        
        layout.addWidget(QLabel("Datei-Pfad:"))
        layout.addWidget(self.file_path_display)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_browse = QPushButton("📂 Durchsuchen")
        btn_browse.clicked.connect(self.open_file_dialog)
        btn_layout.addWidget(btn_browse)
        
        btn_clear = QPushButton("✕ Löschen")
        btn_clear.clicked.connect(self.clear_file_selection)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)
        
        # Unterstützte Formate
        formats_label = QLabel(
            f"✓ Unterstützte Formate: {', '.join(self.SUPPORTED_FORMATS).upper()}"
        )
        formats_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(formats_label)
        
        layout.addStretch()
        return widget
    
    def create_live_tab(self):
        """Erstellt den Tab für Live-Recording."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titel
        title = QLabel("Mikrofon-Aufnahme")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Mikrofon-Auswahl
        layout.addWidget(QLabel("Verfügbare Mikrofone:"))
        
        mic_layout = QHBoxLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("🔍 Mikrofone werden geladen...")
        mic_layout.addWidget(self.mic_combo)
        
        btn_refresh = QPushButton("🔄 Aktualisieren")
        btn_refresh.clicked.connect(self.refresh_devices)
        mic_layout.addWidget(btn_refresh)
        
        layout.addLayout(mic_layout)
        
        # HuggingFace Token (nur bei macOS relevant, aber cross-platform)
        if is_mac() or True:  # Immer anzeigen für Transparenz
            layout.addWidget(QLabel("HuggingFace Token (für Speaker Diarization):"))
            
            token_layout = QHBoxLayout()
            self.hf_token_input = QLineEdit()
            self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.hf_token_input.setPlaceholderText("Token wird aus Keychain geladen / hier eingeben...")
            token_layout.addWidget(self.hf_token_input)
            
            btn_load_keychain = QPushButton("🔑 Aus Keychain laden")
            btn_load_keychain.clicked.connect(self.load_hf_token_from_keychain)
            token_layout.addWidget(btn_load_keychain)
            
            layout.addLayout(token_layout)
            
            # Hint
            hint = QLabel("💡 macOS: Token mit speichern: `security add-generic-password -s HF_V-Speechflow -w \"hf_xxx\"`")
            hint.setStyleSheet("color: gray; font-size: 9px;")
            layout.addWidget(hint)
        
        # Recording Status
        layout.addWidget(QLabel("Recording Status:"))
        self.recording_status = QLabel("🔴 Bereit")
        self.recording_status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.recording_status)
        
        # Volume Meter
        layout.addWidget(QLabel("Volume:"))
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        layout.addWidget(self.volume_bar)
        
        # Recording Controls
        control_layout = QHBoxLayout()
        
        self.btn_start_recording = QPushButton("▶️ Start Recording")
        self.btn_start_recording.clicked.connect(self.start_recording)
        self.btn_start_recording.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        control_layout.addWidget(self.btn_start_recording)
        
        self.btn_stop_recording = QPushButton("⏹️ Stop Recording")
        self.btn_stop_recording.clicked.connect(self.stop_recording)
        self.btn_stop_recording.setEnabled(False)
        self.btn_stop_recording.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        control_layout.addWidget(self.btn_stop_recording)
        
        layout.addLayout(control_layout)
        
        # Info
        info = QLabel("💡 Recording wird als temporäre WAV-Datei gespeichert")
        info.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info)
        
        layout.addStretch()
        return widget
    
    def open_file_dialog(self):
        """Öffnet Datei-Dialog für Audio-Auswahl."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Audio-Datei wählen",
            "",
            f"Audio-Dateien ({' '.join(f'*.{fmt}' for fmt in self.SUPPORTED_FORMATS)});;Alle Dateien (*)"
        )
        
        if file_path:
            self.set_file_path(file_path)
    
    def set_file_path(self, file_path: str):
        """Setzt die ausgewählte Datei."""
        path = Path(file_path)
        
        # Validierung
        if not path.exists():
            self.file_path_display.setText(f"❌ Datei nicht gefunden: {file_path}")
            return
        
        if path.suffix.lower().lstrip('.') not in self.SUPPORTED_FORMATS:
            self.file_path_display.setText(f"❌ Nicht unterstütztes Format: {path.suffix}")
            return
        
        self.selected_file = str(path)
        self.file_path_display.setText(f"✓ {path.name} ({path.stat().st_size / 1024 / 1024:.1f} MB)")
        self.file_selected.emit(self.selected_file)
    
    def clear_file_selection(self):
        """Löscht die Dateiauswahl."""
        self.selected_file = None
        self.file_path_display.clear()
        self.file_path_display.setPlaceholderText("Ziehe Datei hier hin oder klicke zum Auswählen...")
    
    def refresh_devices(self):
        """Aktualisiert die Liste der verfügbaren Mikrofone."""
        try:
            self.device_list = list_audio_devices()
            self.mic_combo.clear()
            
            if not self.device_list or self.device_list[0]['id'] == -1:
                error_device = self.device_list[0] if self.device_list else {}
                device_name = error_device.get('name', '❌ Keine Geräte gefunden')
                self.mic_combo.addItem(device_name)
                
                # Permission-Error anzeigen
                if error_device.get('is_permission_error'):
                    QMessageBox.warning(
                        self,
                        "🔒 Mikrofonzugriff erforderlich",
                        error_device.get('error', 'Mikrofonzugriff verwehrt')
                    )
            else:
                for device in self.device_list:
                    display_text = f"{device['name']} ({device['channels']}ch, {device['sample_rate']}Hz)"
                    self.mic_combo.addItem(display_text, device['id'])
                
                self.mic_combo.setCurrentIndex(0)
        except Exception as e:
            self.mic_combo.clear()
            self.mic_combo.addItem(f"❌ Fehler: {str(e)}")
    
    def start_recording(self):
        """Startet die Live-Aufnahme."""
        if self.is_recording:
            return
        
        self.is_recording = True
        device_idx = self.mic_combo.currentData()
        
        self.recording_status.setText("🔴 Aufnahme läuft...")
        self.recording_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.btn_start_recording.setEnabled(False)
        self.btn_stop_recording.setEnabled(True)
        self.mic_combo.setEnabled(False)
        
        self.recording_started.emit()
    
    def stop_recording(self):
        """Stoppt die Live-Aufnahme."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        self.recording_status.setText("🔴 Bereit")
        self.recording_status.setStyleSheet("color: green; font-weight: bold;")
        
        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)
        self.mic_combo.setEnabled(True)
        
        self.recording_stopped.emit()
    
    def load_hf_token_from_keychain(self):
        """Lädt HuggingFace Token aus macOS Keychain."""
        token = get_hf_token_from_keychain()
        
        if token:
            self.hf_token_input.setText(token)
            QMessageBox.information(
                self,
                "✓ Token geladen",
                "HuggingFace Token erfolgreich aus Keychain geladen!"
            )
        else:
            if is_mac():
                QMessageBox.information(
                    self,
                    "ℹ️ Token nicht gefunden",
                    "Token nicht im Keychain gespeichert.\n\n"
                    "Um den Token zu speichern, führen Sie in der Terminal aus:\n\n"
                    "security add-generic-password -s HF_V-Speechflow -a user -w \"hf_xxxx\"\n\n"
                    "Alternativ können Sie den Token oben manuell eingeben."
                )
            else:
                QMessageBox.information(
                    self,
                    "ℹ️ macOS nur",
                    "Keychain-Integration ist nur auf macOS verfügbar.\n"
                    "Bitte geben Sie den Token manuell ein."
                )
    
    def get_hf_token(self) -> str:
        """Gibt den eingegebenen oder geladenen HF-Token zurück."""
        return self.hf_token_input.text() if hasattr(self, 'hf_token_input') else ""
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Akzeptiert Drag-and-Drop für Audio-Dateien."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(self.SUPPORTED_FORMATS):
                    # Visuelles Feedback: Highlight im Input-Widget
                    self.file_path_display.setStyleSheet(
                        "border: 2px solid #4CAF50; background-color: #f0f8f0; border-radius: 4px;"
                    )
                    event.acceptProposedAction()
                    return
        
        # Falls nicht akzeptiert - rotes Highlight
        self.file_path_display.setStyleSheet(
            "border: 2px solid #f44336; background-color: #f8f0f0; border-radius: 4px;"
        )
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Entfernt visuelles Feedback wenn Drag verlässt."""
        self.file_path_display.setStyleSheet("")
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Verarbeitet Drop von Audio-Dateien."""
        self.file_path_display.setStyleSheet("")  # Highlighting entfernen
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.set_file_path(file_path)
    
    def get_selected_file(self) -> str:
        """Gibt den Pfad zur ausgewählten Datei zurück."""
        return self.selected_file
    
    def is_live_mode(self) -> bool:
        """Gibt zurück, ob Live-Mode aktiv ist."""
        return self.is_recording
