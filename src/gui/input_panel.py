"""
Input Panel für Datei- und Live-Aufnahme-Verwaltung

Ermöglicht Auswahl von Audio-Dateien oder Live-Recording vom Mikrofon.
"""

from pathlib import Path
from typing import Optional
import tempfile
from datetime import datetime
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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent, QIcon
from .translations import tr
from .utils import list_audio_devices, get_default_device
from .macos_utils import get_hf_token_from_keychain, is_mac
from .workers import RecordingWorker
from .batch_panel import BatchPanel


class InputPanel(QWidget):
    """Panel für Audio-Input (Datei oder Live)."""
    
    # Signals
    file_selected = pyqtSignal(str)  # Signal wenn Datei ausgewählt
    batch_selected = pyqtSignal()  # Signal wenn Batch-Processing gewählt
    recording_started = pyqtSignal()  # Signal wenn Live-Recording startet
    recording_stopped = pyqtSignal()  # Signal wenn Live-Recording endet
    
    SUPPORTED_FORMATS = ("mp3", "m4a", "wav", "flac", "ogg")
    
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.device_list = []
        self.is_recording = False
        self.recording_worker = None
        self.recorded_file = None
        self.saved_device_id = None  # Für gespeichertes Gerät
        self.history_manager = None  # Wird später gesetzt
        
        # Drag & Drop aktivieren auf dem ganzen Panel
        self.setAcceptDrops(True)
        
        # UI erst erstellen
        self.init_ui()
        
        # DANN Mikrofone laden (nach UI-Erstellung)
        self.refresh_devices()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Tab Widget: Datei vs Batch vs Live
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_live_tab(), "🎤 Live")
        self.tabs.addTab(self.create_file_tab(), "📁 Datei")
        self.tabs.addTab(self.create_batch_tab(), "📦 Batch")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def create_file_tab(self):
        """Erstellt den Tab für Datei-Auswahl."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titel
        title = QLabel("Audio-Datei auswählen")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)
        
        # Datei-Pfad Display (mit Drag & Drop)
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("Ziehe Datei hier hin oder klicke zum Auswählen...")
        self.file_path_display.setDragEnabled(False)
        self.file_path_display.setToolTip(tr("tooltip_input_file"))
        
        layout.addWidget(QLabel("Datei-Pfad:"))
        layout.addWidget(self.file_path_display)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_browse = QPushButton("📂 Durchsuchen")
        btn_browse.clicked.connect(self.open_file_dialog)
        btn_browse.setToolTip(tr("tooltip_input_file"))
        btn_layout.addWidget(btn_browse)
        
        btn_clear = QPushButton("✕ Löschen")
        btn_clear.clicked.connect(self.clear_file_selection)
        btn_clear.setToolTip("Dateiauswahl zurücksetzen")
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)
        
        # Unterstützte Formate
        formats_label = QLabel(
            f"✓ Unterstützte Formate: {', '.join(self.SUPPORTED_FORMATS).upper()}"
        )
        formats_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(formats_label)
        
        layout.addStretch()
        return widget
    
    def create_batch_tab(self):
        """Erstellt den Tab für Batch-Processing."""
        # BatchPanel direkt einbinden
        self.batch_panel = BatchPanel()
        return self.batch_panel
    
    def create_live_tab(self):
        """Erstellt den Tab für Live-Recording."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titel
        title = QLabel("Mikrofon-Aufnahme")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)
        
        # Mikrofon-Auswahl
        layout.addWidget(QLabel("Verfügbare Mikrofone:"))
        
        mic_layout = QHBoxLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("🔍 Mikrofone werden geladen...")
        self.mic_combo.setToolTip(tr("tooltip_input_live"))
        self.mic_combo.currentIndexChanged.connect(self.on_microphone_changed)
        mic_layout.addWidget(self.mic_combo)
        
        btn_refresh = QPushButton("🔄 Aktualisieren")
        btn_refresh.clicked.connect(self.refresh_devices)
        btn_refresh.setToolTip("Mikrofonliste aktualisieren")
        mic_layout.addWidget(btn_refresh)
        
        layout.addLayout(mic_layout)
        
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
        self.btn_start_recording.setToolTip(tr("tooltip_input_live"))
        control_layout.addWidget(self.btn_start_recording)
        
        self.btn_stop_recording = QPushButton("⏹️ Stop Recording")
        self.btn_stop_recording.clicked.connect(self.stop_recording)
        self.btn_stop_recording.setEnabled(False)
        self.btn_stop_recording.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.btn_stop_recording.setToolTip("Aufnahme beenden und Datei speichern")
        control_layout.addWidget(self.btn_stop_recording)
        
        layout.addLayout(control_layout)
        
        # Info
        info = QLabel("💡 Recording wird als temporäre WAV-Datei gespeichert")
        info.setStyleSheet("color: gray; font-size: 11px;")
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
                
                # Intelligente Geräte-Auswahl mit Prioritäten
                self._select_best_device()
        except Exception as e:
            self.mic_combo.clear()
            self.mic_combo.addItem(f"❌ Fehler: {str(e)}")
    
    def _select_best_device(self):
        """Wählt das beste verfügbare Gerät mit Prioritäten:
        1. Gespeichertes Gerät (falls vorhanden)
        2. Standard-Gerät des Systems
        3. Erstes verfügbares Gerät
        """
        selected_index = 0  # Fallback
        
        # Priorität 1: Gespeichertes Gerät
        if self.saved_device_id is not None:
            for i in range(self.mic_combo.count()):
                if self.mic_combo.itemData(i) == self.saved_device_id:
                    selected_index = i
                    print(f"✓ Gespeichertes Mikrofon gefunden: {self.mic_combo.itemText(i)}")
                    self.mic_combo.setCurrentIndex(selected_index)
                    return
            print(f"⚠ Gespeichertes Mikrofon (ID: {self.saved_device_id}) nicht mehr verfügbar")
        
        # Priorität 2: Standard-Gerät vom System
        default_device_id = get_default_device()
        if default_device_id is not None:
            for i in range(self.mic_combo.count()):
                if self.mic_combo.itemData(i) == default_device_id:
                    selected_index = i
                    print(f"✓ Standard-Mikrofon vom System gefunden: {self.mic_combo.itemText(i)}")
                    break
        
        # Priorität 3 (Fallback): Erstes Gerät
        self.mic_combo.setCurrentIndex(selected_index)
        if selected_index == 0 and default_device_id is None:
            print(f"ℹ Verwende erstes verfügbares Mikrofon: {self.mic_combo.itemText(0)}")
    
    def set_history_manager(self, history_manager):
        """Setzt den History-Manager für Speicherung der Mikrofon-Auswahl."""
        self.history_manager = history_manager
        
        # Gespeichertes Mikrofon laden
        self.saved_device_id = history_manager.get_user_preference('last_microphone_id')
        if self.saved_device_id is not None:
            print(f"ℹ Gespeicherte Mikrofon-ID geladen: {self.saved_device_id}")
    
    def save_current_microphone(self):
        """Speichert das aktuell ausgewählte Mikrofon."""
        if self.history_manager is None:
            return
        
        device_id = self.mic_combo.currentData()
        if device_id is not None and device_id >= 0:
            self.history_manager.set_user_preference('last_microphone_id', device_id)
            self.saved_device_id = device_id
            device_name = self.mic_combo.currentText()
            print(f"✓ Mikrofon gespeichert: {device_name} (ID: {device_id})")
    
    def on_microphone_changed(self, index: int):
        """Wird aufgerufen wenn das Mikrofon geändert wird."""
        # Speichere die neue Auswahl
        self.save_current_microphone()
    
    def start_recording(self):
        """Startet die Live-Aufnahme."""
        if self.is_recording:
            return
        
        # Device-Index ermitteln
        device_idx = self.mic_combo.currentData()
        
        # Ausgewähltes Mikrofon speichern
        self.save_current_microphone()
        if device_idx is None or device_idx < 0:
            QMessageBox.warning(
                self,
                "Kein Mikrofon",
                "Bitte wählen Sie ein gültiges Mikrofon aus."
            )
            return
        
        # Temporäre WAV-Datei erstellen
        temp_dir = Path(tempfile.gettempdir()) / "vspeechflow"
        temp_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = temp_dir / f"recording_{timestamp}.wav"
        
        # Recording-Worker erstellen und starten
        self.recording_worker = RecordingWorker(device_idx, output_path)
        self.recording_worker.volume_updated.connect(self.on_volume_updated)
        self.recording_worker.duration_updated.connect(self.on_duration_updated)
        self.recording_worker.recording_error.connect(self.on_recording_error)
        self.recording_worker.recording_finished.connect(self.on_recording_finished)
        
        try:
            self.recording_worker.start()
            
            self.is_recording = True
            self.recorded_file = str(output_path)
            
            self.recording_status.setText("🔴 Aufnahme läuft... (0.0s)")
            self.recording_status.setStyleSheet("color: red; font-weight: bold;")
            
            self.btn_start_recording.setEnabled(False)
            self.btn_stop_recording.setEnabled(True)
            self.mic_combo.setEnabled(False)
            
            self.recording_started.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Konnte Recording nicht starten:\n{str(e)}"
            )
            self.is_recording = False
    
    def stop_recording(self):
        """Stoppt die Live-Aufnahme."""
        if not self.is_recording or not self.recording_worker:
            return
        
        # Worker stoppen
        self.recording_worker.stop()
        self.recording_worker.wait(2000)  # 2 Sekunden warten
        
        self.is_recording = False
        self.volume_bar.setValue(0)
        
        self.recording_status.setText("⏹️ Gestoppt - Speichere...")
        self.recording_status.setStyleSheet("color: orange; font-weight: bold;")
        
        # UI wird in on_recording_finished() zurückgesetzt
    
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
    
    def dragLeaveEvent(self, event: QDragLeaveEvent):
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
                event.acceptProposedAction()
    
    def on_volume_updated(self, volume: float):
        """Wird aufgerufen wenn sich das Volume ändert."""
        self.volume_bar.setValue(int(volume))
    
    def on_duration_updated(self, duration: float):
        """Wird aufgerufen wenn sich die Dauer ändert."""
        self.recording_status.setText(f"🔴 Aufnahme läuft... ({duration:.1f}s)")
    
    def on_recording_error(self, error_msg: str):
        """Wird aufgerufen wenn ein Fehler auftritt."""
        QMessageBox.critical(
            self,
            "Recording-Fehler",
            f"Fehler während der Aufnahme:\n{error_msg}"
        )
        
        self.is_recording = False
        self.volume_bar.setValue(0)
        
        self.recording_status.setText("❌ Fehler")
        self.recording_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)
        self.mic_combo.setEnabled(True)
    
    def on_recording_finished(self, wav_path: str):
        """Wird aufgerufen wenn die Aufnahme beendet ist."""
        self.recorded_file = wav_path
        self.selected_file = wav_path
        
        # Datei-Info anzeigen
        path = Path(wav_path)
        size_mb = path.stat().st_size / 1024 / 1024
        
        self.recording_status.setText(f"✅ Gespeichert: {path.name} ({size_mb:.1f}MB)")
        self.recording_status.setStyleSheet("color: green; font-weight: bold;")
        
        # UI zurücksetzen
        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)
        self.mic_combo.setEnabled(True)
        
        # Signal für Datei-Auswahl emittieren
        self.file_selected.emit(wav_path)
        self.recording_stopped.emit()
        
        QMessageBox.information(
            self,
            "Aufnahme beendet",
            f"Recording erfolgreich gespeichert!\n\nDatei: {path.name}\nGröße: {size_mb:.1f} MB\n\n"
            f"Die Datei wurde automatisch als Input-Datei ausgewählt."
        )
    
    def get_selected_file(self) -> Optional[str]:
        """Gibt den Pfad zur ausgewählten Datei zurück."""
        return self.selected_file
    
    def is_live_mode(self) -> bool:
        """Gibt zurück, ob Live-Mode aktiv ist."""
        return self.is_recording
    
    def get_input_mode(self) -> str:
        """Gibt den aktuellen Input-Modus zurück: 'file', 'batch', oder 'live'."""
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            return 'file'
        elif current_index == 1:
            return 'batch'
        elif current_index == 2:
            return 'live'
        return 'file'
    
    def is_batch_mode(self) -> bool:
        """Gibt zurück, ob Batch-Mode aktiv ist."""
        return self.get_input_mode() == 'batch'
    
    def get_batch_files(self) -> list:
        """Gibt die Liste der Batch-Dateien zurück."""
        if hasattr(self, 'batch_panel'):
            return self.batch_panel.get_file_list()
        return []
    
    def get_batch_options(self) -> dict:
        """Gibt die Batch-Optionen zurück."""
        if hasattr(self, 'batch_panel'):
            return self.batch_panel.get_options()
        return {}
