"""
Model Panel für Whisper.cpp Modell-Verwaltung

Ermöglicht Auswahl, Validierung und Download von Modellen.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from .translations import tr
from .collapsible_section import CollapsibleSection
from .model_utils import (
    AVAILABLE_MODELS,
    validate_model_file,
    get_model_info,
    get_models_dir,
    get_model_path_in_models_dir,
    is_model_downloaded,
)
from .workers import ModelDownloadWorker
import logging

logger = logging.getLogger(__name__)


class NonScrollableComboBox(QComboBox):
    """ComboBox die nicht mit dem Mausrad scrollbar ist."""
    
    def wheelEvent(self, event):
        """Ignoriert Scroll-Events."""
        event.ignore()


class ModelPanel(QWidget):
    """Panel für Modell-Auswahl und Validierung."""
    
    model_selected = pyqtSignal(str)  # Signal wenn Modell ausgewählt
    
    def __init__(self):
        super().__init__()
        self.selected_model = None
        self.is_model_info_expanded = False
        self._download_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Collapsible Section
        self.section = CollapsibleSection("🤖 " + tr("model_panel_title"))
        layout = self.section.content_layout
        layout.setContentsMargins(10, 5, 0, 5)
        
        # Modell-Auswahl (Vorschläge)
        layout.addWidget(QLabel(tr("model_quick_select")))
        self.model_combo = NonScrollableComboBox()
        self.populate_model_combo()
        self.model_combo.currentTextChanged.connect(self.on_model_combo_changed)
        self.model_combo.setToolTip(tr("tooltip_model_path"))
        layout.addWidget(self.model_combo)
        
        # Modell-Details
        self.model_details = QLabel()
        self.model_details.setStyleSheet("color: gray; font-size: 11px; text-align: justify;")
        self.model_details.setWordWrap(True)
        layout.addWidget(self.model_details)
        
        # Manual Model Path
        layout.addWidget(QLabel(tr("model_or_custom")))
        
        path_layout = QHBoxLayout()
        self.model_path_input = QLineEdit()
        self.model_path_input.setReadOnly(False)
        self.model_path_input.setPlaceholderText("/path/to/ggml-small.bin")
        self.model_path_input.textChanged.connect(self.validate_model_path)
        self.model_path_input.setToolTip(tr("tooltip_model_path"))
        path_layout.addWidget(self.model_path_input)
        
        btn_browse = QPushButton("📂 " + tr("model_btn_browse"))
        btn_browse.clicked.connect(self.browse_model_file)
        btn_browse.setToolTip("Whisper-Modelldatei auswählen")
        path_layout.addWidget(btn_browse)
        
        layout.addLayout(path_layout)
        
        # Validierungs-Status
        self.validation_status = QLabel("⏳ " + tr("model_validation_pending"))
        self.validation_status.setStyleSheet("font-weight: bold; color: gray;")
        layout.addWidget(self.validation_status)
        
        # Model Info Box mit Toggle
        model_info_container_layout = QVBoxLayout()
        
        # Toggle-Header für Model Info
        model_info_header_layout = QHBoxLayout()
        model_info_header_layout.setContentsMargins(0, 5, 0, 5)
        
        self.model_info_toggle_button = QPushButton("▶")
        self.model_info_toggle_button.setFixedWidth(25)
        self.model_info_toggle_button.setToolTip("Verfügbare Modelle ein-/ausblenden")
        self.model_info_toggle_button.clicked.connect(self.toggle_model_info)
        model_info_header_layout.addWidget(self.model_info_toggle_button)
        
        model_info_title = QLabel("📋 " + tr("model_available_title"))
        model_info_title.setStyleSheet("font-weight: bold;")
        model_info_header_layout.addWidget(model_info_title)
        model_info_header_layout.addStretch()
        
        model_info_container_layout.addLayout(model_info_header_layout)
        
        # Model Info Box (Content)
        info_group = QGroupBox()
        info_group.setVisible(False)  # Standardmäßig eingeklappt
        self.model_info_content = info_group
        info_layout = QVBoxLayout(info_group)
        
        # Scrollable Info
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        info_widget = QWidget()
        info_widget_layout = QVBoxLayout(info_widget)
        
        # Mapping von Dateinamen zu Translation Keys
        model_translations = {
            "ggml-base.bin": ("model_base_name", "model_base_desc"),
            "ggml-small.bin": ("model_small_name", "model_small_desc"),
            "ggml-medium.bin": ("model_medium_name", "model_medium_desc"),
            "ggml-large-v3.bin": ("model_large_name", "model_large_desc"),
        }
        
        # Dict für Download-Buttons pro Modell
        self._model_download_btns = {}
        self._model_status_labels = {}
        
        for filename, info in AVAILABLE_MODELS.items():
            # Translation Keys holen
            name_key, desc_key = model_translations.get(filename, (None, None))
            
            # Model Header
            model_name = tr(name_key) if name_key else info['name']
            header = QLabel(f"• {model_name} ({info['size_mb']} MB)")
            header.setStyleSheet("font-weight: bold;")
            info_widget_layout.addWidget(header)
            
            # Model Description
            model_desc = tr(desc_key) if desc_key else info['description']
            desc = QLabel(f"  {model_desc}")
            desc.setStyleSheet("color: gray; font-size: 10px;")
            desc.setWordWrap(True)
            info_widget_layout.addWidget(desc)
            
            # Download Link
            link = QLabel(f'  {tr("model_info_filename")} <a href="{info["url"]}"><code>{filename}</code></a>')
            link.setOpenExternalLinks(True)
            link.setStyleSheet("font-size: 10px;")
            info_widget_layout.addWidget(link)
            
            # Download-Button oder Status pro Modell
            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(15, 2, 0, 2)
            
            if is_model_downloaded(filename):
                status_lbl = QLabel("✅ " + tr("model_download_complete"))
                status_lbl.setStyleSheet("font-size: 10px; color: green;")
                btn_row.addWidget(status_lbl)
                self._model_status_labels[filename] = status_lbl
            else:
                dl_btn = QPushButton("⬇️ " + tr("model_download_btn"))
                dl_btn.setFixedHeight(26)
                dl_btn.clicked.connect(lambda checked, fn=filename: self._start_info_download(fn))
                btn_row.addWidget(dl_btn)
                self._model_download_btns[filename] = dl_btn
                
                status_lbl = QLabel()
                status_lbl.setStyleSheet("font-size: 10px;")
                status_lbl.setVisible(False)
                btn_row.addWidget(status_lbl)
                self._model_status_labels[filename] = status_lbl
            
            btn_row.addStretch()
            info_widget_layout.addLayout(btn_row)
            
            info_widget_layout.addSpacing(5)
        
        info_widget_layout.addStretch()
        scroll.setWidget(info_widget)
        info_layout.addWidget(scroll)
        
        # Gemeinsame Progressbar + Cancel am unteren Rand der Info-Box
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        self.download_progress.setTextVisible(True)
        info_layout.addWidget(self.download_progress)
        
        dl_bottom_layout = QHBoxLayout()
        self.download_status = QLabel()
        self.download_status.setVisible(False)
        self.download_status.setStyleSheet("font-size: 11px; color: gray;")
        dl_bottom_layout.addWidget(self.download_status)
        
        self.download_cancel_btn = QPushButton(tr("cancel"))
        self.download_cancel_btn.clicked.connect(self.cancel_model_download)
        self.download_cancel_btn.setVisible(False)
        dl_bottom_layout.addWidget(self.download_cancel_btn)
        info_layout.addLayout(dl_bottom_layout)
        
        model_info_container_layout.addWidget(info_group)
        layout.addLayout(model_info_container_layout)
        
        # Tipps
        tips = QLabel(
            f"💡 <b>{tr('model_tips_title')}</b><br>"
            f"• <b>Small</b> (500MB): {tr('model_tips_small')}<br>"
            f"• <b>Medium</b> (1.5GB): {tr('model_tips_medium')}<br>"
            f"• {tr('model_tips_download')} <a href=\"https://huggingface.co/ggerganov/whisper.cpp\">HuggingFace</a>"
        )
        tips.setOpenExternalLinks(True)
        tips.setStyleSheet("color: gray; font-size: 10px;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
        
        # Collapsible Section zum Main-Layout hinzufügen
        main_layout.addWidget(self.section)
        self.setLayout(main_layout)
    
    def populate_model_combo(self):
        """Füllt die Model ComboBox mit Vorschlägen."""
        self.model_combo.clear()
        self.model_combo.addItem(tr("model_quick_select") + "...", None)
        
        for filename, info in AVAILABLE_MODELS.items():
            display_text = f"{info['name']} - {filename}"
            self.model_combo.addItem(display_text, filename)
    
    def on_model_combo_changed(self, text: str):
        """Wird aufgerufen wenn Combo-Selection sich ändert."""
        filename = self.model_combo.currentData()
        
        if filename:
            logger.info(f"Model quick-select changed: {filename}")
            info = get_model_info(filename)
            if info:
                model_path = get_model_path_in_models_dir(filename)
                self.model_path_input.setText(str(model_path))
                self.update_model_details(filename, info)
    
    def browse_model_file(self):
        """Öffnet File-Dialog zur Modell-Auswahl."""
        logger.debug("Model file browse dialog opened")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("wizard_model_browse_title"),
            str(Path.home()),
            "Whisper Model (ggml-*.bin);;Alle Dateien (*)"
        )
        
        if file_path:
            self.model_path_input.setText(file_path)
    
    def validate_model_path(self):
        """Validiert den Modell-Pfad."""
        model_path = self.model_path_input.text().strip()
        
        if not model_path:
            self.validation_status.setText("⏳ " + tr("model_validation_pending"))
            self.validation_status.setStyleSheet("font-weight: bold; color: gray;")
            self.selected_model = None
            return
        
        # Validierung
        result = validate_model_file(model_path)
        
        if result['valid']:
            self.validation_status.setText(
                f"{tr('model_validation_valid')} ({result['size_mb']} MB)"
            )
            self.validation_status.setStyleSheet("font-weight: bold; color: green;")
            self.selected_model = model_path
            logger.info(f"Model validated: {model_path} ({result['size_mb']} MB)")
            self.model_selected.emit(model_path)
        else:
            error = result.get('error', 'Unbekannter Fehler')
            logger.warning(f"Model validation failed: {model_path} - {error}")
            self.validation_status.setText(f"✗ {error}")
            self.validation_status.setStyleSheet("font-weight: bold; color: red;")
            self.selected_model = None
    
    def update_model_details(self, filename: str, info: dict):
        """Aktualisiert die Modell-Details-Anzeige."""
        self.model_details.setText(
            f"<b>{info['name']}</b><br>"
            f"Größe: {info['size_mb']} MB<br>"
            f"{info['description']}"
        )
    
    def get_selected_model(self) -> Optional[str]:
        """Gibt den Pfad zum ausgewählten Modell zurück."""
        return self.selected_model
    
    def set_model_path(self, model_path: str):
        """Setzt den Modell-Pfad programmatisch."""
        if model_path and Path(model_path).exists():
            self.model_path_input.setText(model_path)
            self.validate_model_path()
    
    def get_model_path(self) -> str:
        """
        Gibt den aktuellen Modell-Pfad zurück.
        
        Returns:
            Der Pfad aus dem model_path_input Feld
        """
        return self.model_path_input.text().strip()
    
    def get_settings(self) -> dict:
        """
        Gibt die aktuellen Model-Einstellungen zurück.
        
        Returns:
            Dict mit model_path
        """
        return {
            "model_path": self.get_model_path(),
        }
    
    def set_settings(self, settings: dict):
        """
        Setzt die Model-Einstellungen aus einem Dict.
        
        Args:
            settings: Dict mit model_path
        """
        if not isinstance(settings, dict):
            return

        # Schnellauswahl immer auf Standardwert zurücksetzen
        self.model_combo.setCurrentIndex(0)

        # Modell-Pfad setzen (auch wenn Datei noch nicht existiert)
        model_path = settings.get("model_path")
        if model_path:
            self.model_path_input.setText(model_path)
            self.validate_model_path()
    
    # ---- Download-Logik ----

    def _start_info_download(self, filename: str):
        """Startet den Download eines bestimmten Modells aus der Info-Box."""
        if self._download_worker is not None:
            QMessageBox.information(
                self,
                tr("model_download_in_progress"),
                tr("model_download_in_progress"),
            )
            return

        info = get_model_info(filename)
        if not info:
            return

        dest_path = get_model_path_in_models_dir(filename)

        # Bestätigung
        reply = QMessageBox.question(
            self,
            tr("model_download_confirm_title"),
            tr("model_download_confirm_text", name=info['name'], size=info['size_mb']),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._current_download_filename = filename
        logger.info(f"Starting model download: {filename} from {info['url']} ({info['size_mb']} MB)")

        # Per-Model Button deaktivieren
        if filename in self._model_download_btns:
            self._model_download_btns[filename].setEnabled(False)
            self._model_download_btns[filename].setText(tr("model_download_in_progress"))

        # Alle anderen Download-Buttons sperren
        for fn, btn in self._model_download_btns.items():
            btn.setEnabled(False)

        # Gemeinsame Progressbar einblenden
        self.download_cancel_btn.setVisible(True)
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_status.setVisible(True)
        self.download_status.setText(tr("model_download_starting"))
        self.download_status.setStyleSheet("font-size: 11px; color: gray;")

        # Worker starten
        self._download_worker = ModelDownloadWorker(info['url'], dest_path)
        self._download_worker.progress_updated.connect(self._on_download_progress)
        self._download_worker.download_finished.connect(self._on_download_finished)
        self._download_worker.download_error.connect(self._on_download_error)
        self._download_worker.start()

    def start_model_download(self):
        """Legacy: Startet Download für das aktuell in der ComboBox gewählte Modell."""
        filename = self.model_combo.currentData()
        if filename:
            self._start_info_download(filename)

    def cancel_model_download(self):
        """Bricht den laufenden Download ab."""
        logger.info("Model download cancelled by user")
        if self._download_worker:
            self._download_worker.stop()
            self._download_worker.wait(3000)
            self._download_worker = None
        self._reset_download_ui()
        self.download_status.setVisible(True)
        self.download_status.setText(tr("model_download_cancelled"))
        self.download_status.setStyleSheet("font-size: 11px; color: orange;")

    def _on_download_progress(self, downloaded: float, total: float):
        """Aktualisiert die Fortschrittsanzeige."""
        dl_mb = downloaded / (1024 * 1024)
        if total > 0:
            percent = int(downloaded / total * 100)
            self.download_progress.setValue(percent)
            total_mb = total / (1024 * 1024)
            self.download_status.setText(f"{dl_mb:.1f} / {total_mb:.1f} MB ({percent}%)")
        else:
            self.download_progress.setRange(0, 0)  # Indeterminate
            self.download_status.setText(f"{dl_mb:.1f} MB heruntergeladen...")

    def _on_download_finished(self, path: str):
        """Wird aufgerufen wenn der Download erfolgreich abgeschlossen ist."""
        filename = getattr(self, '_current_download_filename', None)
        logger.info(f"Model download completed: {filename} -> {path}")
        self._download_worker = None
        self._reset_download_ui()
        self.download_status.setVisible(True)
        self.download_status.setText("✅ " + tr("model_download_complete"))
        self.download_status.setStyleSheet("font-size: 11px; color: green;")

        # Button durch Status-Label ersetzen
        if filename and filename in self._model_download_btns:
            btn = self._model_download_btns[filename]
            btn.setVisible(False)
            if filename in self._model_status_labels:
                lbl = self._model_status_labels[filename]
                lbl.setText("✅ " + tr("model_download_complete"))
                lbl.setStyleSheet("font-size: 10px; color: green;")
                lbl.setVisible(True)

        # Pfad setzen und validieren
        self.model_path_input.setText(path)
        self.validate_model_path()

    def _on_download_error(self, error: str):
        """Wird aufgerufen wenn der Download fehlschlägt."""
        logger.error(f"Model download failed: {error}")
        self._download_worker = None
        self._reset_download_ui()
        self.download_status.setVisible(True)
        self.download_status.setText("❌ " + tr("model_download_error", error=error))
        self.download_status.setStyleSheet("font-size: 11px; color: red;")
        QMessageBox.warning(self, tr("model_download_error_title"), error)

    def _reset_download_ui(self):
        """Setzt die Download-UI-Elemente zurück."""
        self.download_cancel_btn.setVisible(False)
        self.download_progress.setVisible(False)
        self.download_progress.setValue(0)
        # Alle Buttons wieder aktivieren
        for fn, btn in self._model_download_btns.items():
            if not is_model_downloaded(fn):
                btn.setEnabled(True)
                btn.setText("⬇️ " + tr("model_download_btn"))

    def toggle_model_info(self):
        """Toggle für die verfügbaren Modelle."""
        self.is_model_info_expanded = not self.is_model_info_expanded
        self.model_info_content.setVisible(self.is_model_info_expanded)
        self.model_info_toggle_button.setText("▼" if self.is_model_info_expanded else "▶")

    def refresh_translations(self):
        """Aktualisiert alle übersetzbaren Texte nach einem Sprachwechsel."""
        from .translations import tr

        self.section.set_title(tr("model_panel_title"), icon="🤖")
        self.model_combo.setToolTip(tr("tooltip_model_path"))
        self.model_path_input.setToolTip(tr("tooltip_model_path"))
        self.validation_status.setText("⏳ " + tr("model_validation_pending"))

