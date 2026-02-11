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
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent, QIcon
from .translations import tr
from .utils import list_audio_devices, get_default_device
from .macos_utils import get_hf_token_from_keychain, is_mac
from .workers import RecordingWorker
from .batch_panel import BatchPanel
from .constants import SUPPORTED_AUDIO_FORMATS


class InputPanel(QWidget):
    """Panel für Audio-Input (Datei oder Live)."""
    
    # Signals
    file_selected = pyqtSignal(str)  # Signal wenn Datei ausgewählt
    batch_selected = pyqtSignal()  # Signal wenn Batch-Processing gewählt
    recording_started = pyqtSignal()  # Signal wenn Live-Recording startet
    recording_stopped = pyqtSignal()  # Signal wenn Live-Recording endet
    
    SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS
    
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
        self.tabs.addTab(self.create_live_tab(), "🎤 " + tr("input_live_tab"))
        self.tabs.addTab(self.create_file_tab(), "📁 " + tr("input_file_tab"))
        self.tabs.addTab(self.create_batch_tab(), "📦 " + tr("input_batch_tab"))
        
        layout.addWidget(self.tabs)
        layout.addStretch()  # Drückt das Panel auf Minimalgröße zusammen
        self.setLayout(layout)
        
        # Size Policy: Panel nimmt nur minimal benötigten Platz ein
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    
    def create_file_tab(self):
        """Erstellt den Tab für Datei-Auswahl."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Titel
        title = QLabel(tr("input_file_tab_title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)
        
        # Datei-Pfad Display (mit Drag & Drop)
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText(tr("input_placeholder"))
        self.file_path_display.setDragEnabled(False)
        self.file_path_display.setToolTip(tr("tooltip_input_file"))
        
        layout.addWidget(QLabel(tr("input_file_path")))
        layout.addWidget(self.file_path_display)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_browse = QPushButton("📂 " + tr("input_btn_browse"))
        btn_browse.clicked.connect(self.open_file_dialog)
        btn_browse.setToolTip(tr("tooltip_input_file"))
        btn_layout.addWidget(btn_browse)
        
        btn_clear = QPushButton("✕ " + tr("input_btn_clear"))
        btn_clear.clicked.connect(self.clear_file_selection)
        btn_clear.setToolTip(tr("input_clear_tooltip"))
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)
        
        # Unterstützte Formate
        formats_label = QLabel(
            f"✓ {tr('input_formats_supported')}: {', '.join(self.SUPPORTED_FORMATS).upper()}"
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
        title = QLabel(tr("input_live_title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)
        
        # Mikrofon-Auswahl
        layout.addWidget(QLabel(tr("input_available_mics")))
        
        mic_layout = QHBoxLayout()
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("🔍 " + tr("input_btn_refresh") + "...")
        self.mic_combo.setToolTip(tr("tooltip_input_live"))
        self.mic_combo.currentIndexChanged.connect(self.on_microphone_changed)
        mic_layout.addWidget(self.mic_combo)
        
        btn_refresh = QPushButton("🔄 " + tr("input_btn_refresh"))
        btn_refresh.clicked.connect(self.refresh_devices)
        btn_refresh.setToolTip(tr("input_refresh_tooltip"))
        mic_layout.addWidget(btn_refresh)
        
        layout.addLayout(mic_layout)
        
        # Recording Status
        layout.addWidget(QLabel(tr("input_recording_status")))
        self.recording_status = QLabel("🔴 " + tr("input_status_ready"))
        self.recording_status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.recording_status)
        
        # Volume Meter
        layout.addWidget(QLabel(tr("input_volume")))
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        layout.addWidget(self.volume_bar)
        
        # Recording Controls
        control_layout = QHBoxLayout()
        
        self.btn_start_recording = QPushButton("▶️ " + tr("input_btn_start"))
        self.btn_start_recording.clicked.connect(self.start_recording)
        self.btn_start_recording.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_start_recording.setToolTip(tr("tooltip_input_live"))
        control_layout.addWidget(self.btn_start_recording)
        
        self.btn_stop_recording = QPushButton("⏹️ " + tr("input_btn_stop"))
        self.btn_stop_recording.clicked.connect(self.stop_recording)
        self.btn_stop_recording.setEnabled(False)
        self.btn_stop_recording.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.btn_stop_recording.setToolTip(tr("input_stop_tooltip"))
        control_layout.addWidget(self.btn_stop_recording)
        
        layout.addLayout(control_layout)
        
        # Info
        info = QLabel("💡 " + tr("input_recording_info"))
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)
        
        layout.addStretch()
        return widget
    
    def open_file_dialog(self):
        """Öffnet Datei-Dialog für Audio-Auswahl."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("input_file_dialog_title"),
            "",
            f"{tr('input_audio_files_filter')} ({' '.join(f'*.{fmt}' for fmt in self.SUPPORTED_FORMATS)});;{tr('input_all_files')} (*)"
        )
        
        if file_path:
            self.set_file_path(file_path)
    
    def set_file_path(self, file_path: str):
        """Setzt die ausgewählte Datei."""
        path = Path(file_path)
        
        # Validierung
        if not path.exists():
            self.file_path_display.setText(f"❌ {tr('input_file_not_found')}: {file_path}")
            return
        
        if path.suffix.lower().lstrip('.') not in self.SUPPORTED_FORMATS:
            self.file_path_display.setText(f"❌ {tr('input_format_not_supported')}: {path.suffix}")
            return
        
        self.selected_file = str(path)
        self.file_path_display.setText(f"✓ {path.name} ({path.stat().st_size / 1024 / 1024:.1f} MB)")
        self.file_selected.emit(self.selected_file)
    
    def clear_file_selection(self):
        """Löscht die Dateiauswahl."""
        self.selected_file = None
        self.file_path_display.clear()
        self.file_path_display.setPlaceholderText(tr("input_placeholder"))
    
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
                        tr("input_mic_access_title"),
                        error_device.get('error', tr("input_mic_access_title"))
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
            self.history_manager.save_user_preference('last_microphone_id', device_id)
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
                tr("input_mic_unavailable_title"),
                tr("input_mic_unavailable_title")
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
            
            self.recording_status.setText(tr("status_recording_starting"))
            self.recording_status.setStyleSheet("color: red; font-weight: bold;")
            
            self.btn_start_recording.setEnabled(False)
            self.btn_stop_recording.setEnabled(True)
            self.mic_combo.setEnabled(False)
            
            self.recording_started.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("msg_file_open_error_title"),
                f"{tr('input_recording_error_title')}:\n{str(e)}"
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
        
        self.recording_status.setText(tr("status_recording_saving"))
        self.recording_status.setStyleSheet("color: orange; font-weight: bold;")
        
        # UI wird in on_recording_finished() zurückgesetzt
    
    def load_hf_token_from_keychain(self):
        """Lädt HuggingFace Token aus macOS Keychain."""
        token = get_hf_token_from_keychain()
        
        if token:
            self.hf_token_input.setText(token)
            QMessageBox.information(
                self,
                tr('diarization_token_loaded_title'),
                tr('diarization_token_loaded_msg')
            )
        else:
            if is_mac():
                QMessageBox.information(
                    self,
                    tr('diarization_keychain_unavailable_title'),
                    tr('diarization_keychain_hint')
                )
            else:
                QMessageBox.information(
                    self,
                    tr('diarization_keychain_unavailable_title'),
                    tr('diarization_keychain_unavailable_msg')
                )
    
    def get_hf_token(self) -> str:
        """Gibt den eingegebenen oder geladenen HF-Token zurück."""
        return self.hf_token_input.text() if hasattr(self, 'hf_token_input') else ""
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Akzeptiert Drag-and-Drop für Audio-Dateien."""
        # Prüfen welcher Tab aktiv ist
        current_tab = self.tabs.currentIndex()
        
        # Batch-Tab (Index 2): an BatchPanel delegieren
        if current_tab == 2:
            self.batch_panel.dragEnterEvent(event)
            return
        
        # Datei-Tab (Index 1): Einzeldatei-Handling
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
        if current_tab == 1:
            self.file_path_display.setStyleSheet(
                "border: 2px solid #f44336; background-color: #f8f0f0; border-radius: 4px;"
            )
        event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Entfernt visuelles Feedback wenn Drag verlässt."""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 2:
            self.batch_panel.dragLeaveEvent(event)
            return
        
        self.file_path_display.setStyleSheet("")
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Verarbeitet Drop von Audio-Dateien."""
        current_tab = self.tabs.currentIndex()
        
        # Batch-Tab: an BatchPanel delegieren
        if current_tab == 2:
            self.batch_panel.dropEvent(event)
            return
        
        # Datei-Tab: Einzeldatei-Handling
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
        self.recording_status.setText(tr("status_recording_running").format(duration=duration))
    
    def on_recording_error(self, error_msg: str):
        """Wird aufgerufen wenn ein Fehler auftritt."""
        QMessageBox.critical(
            self,
            tr("input_recording_error_title"),
            f"{tr('input_recording_error_title')}:\n{error_msg}"
        )
        
        self.is_recording = False
        self.volume_bar.setValue(0)
        
        self.recording_status.setText(tr("status_recording_error"))
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
        
        self.recording_status.setText(tr("status_recording_saved").format(name=path.name, size=f"{size_mb:.1f}"))
        self.recording_status.setStyleSheet("color: green; font-weight: bold;")
        
        # UI zurücksetzen
        self.volume_bar.setValue(0)
        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)
        self.mic_combo.setEnabled(True)
        
        # Signal für Datei-Auswahl emittieren
        self.file_selected.emit(wav_path)
        self.recording_stopped.emit()
        
        QMessageBox.information(
            self,
            tr("input_recording_saved_title"),
            f"{tr('input_recording_saved_msg')}\n\n{tr('input_file_label')}: {path.name}\n{tr('input_size_label')}: {size_mb:.1f} MB\n\n"
            f"{tr('input_auto_selected_msg')}"
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
            return 'live'
        elif current_index == 1:
            return 'file'
        elif current_index == 2:
            return 'batch'
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

    def refresh_translations(self):
        """Aktualisiert alle übersetzbaren Texte nach einem Sprachwechsel."""
        from .translations import tr

        # Tab-Titel
        self.tabs.setTabText(0, "🎤 " + tr("input_live_tab"))
        self.tabs.setTabText(1, "📁 " + tr("input_file_tab"))
        self.tabs.setTabText(2, "📦 " + tr("input_batch_tab"))

        # File-Tab Widgets
        self.file_path_display.setPlaceholderText(tr("input_placeholder"))
        self.file_path_display.setToolTip(tr("tooltip_input_file"))

        # Live-Tab Widgets
        self.mic_combo.setToolTip(tr("tooltip_input_live"))
        self.recording_status.setText("🔴 " + tr("input_status_ready"))
        self.btn_start_recording.setText(tr("input_btn_start"))
        self.btn_start_recording.setToolTip(tr("tooltip_input_live"))
        self.btn_stop_recording.setText(tr("input_btn_stop"))
        self.btn_stop_recording.setToolTip(tr("input_stop_tooltip"))

