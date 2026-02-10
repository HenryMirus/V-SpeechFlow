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
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from .translations import tr
from .model_utils import (
    AVAILABLE_MODELS,
    validate_model_file,
    get_model_info,
)


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
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel("🤖 " + tr("model_panel_title"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
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
        
        # Model Info Box
        info_group = QGroupBox("📋 " + tr("model_available_title"))
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
            
            info_widget_layout.addSpacing(5)
        
        info_widget_layout.addStretch()
        scroll.setWidget(info_widget)
        info_layout.addWidget(scroll)
        
        layout.addWidget(info_group)
        
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
        self.setLayout(layout)
    
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
            info = get_model_info(filename)
            if info:
                # Pfad zum models Ordner
                models_dir = Path(__file__).parent.parent.parent / "models"
                model_path = models_dir / filename
                
                self.model_path_input.setText(str(model_path))
                self.update_model_details(filename, info)
    
    def browse_model_file(self):
        """Öffnet File-Dialog zur Modell-Auswahl."""
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
            self.model_selected.emit(model_path)
        else:
            error = result.get('error', 'Unbekannter Fehler')
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
