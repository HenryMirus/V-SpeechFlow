"""
Settings Panel für Verarbeitungs-Optionen

Thread-Konfiguration, Sprache, Übersetzung, etc.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .translations import tr
from .collapsible_section import CollapsibleSection
from .system_utils import get_system_info, get_recommended_threads


class NoScrollSlider(QSlider):
    """Slider der nicht auf Mausrad-Scroll reagiert."""
    
    def wheelEvent(self, event):
        """Ignoriert Mausrad-Events."""
        event.ignore()


class NoScrollSpinBox(QSpinBox):
    """SpinBox der nicht auf Mausrad-Scroll reagiert."""
    
    def wheelEvent(self, event):
        """Ignoriert Mausrad-Events."""
        event.ignore()


class SettingsPanel(QWidget):
    """Panel für Verarbeitungs-Einstellungen."""
    
    # Signals
    settings_changed = pyqtSignal(dict)  # Emitted wenn sich Setting ändert
    
    def __init__(self):
        super().__init__()
        self.system_info = get_system_info()
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Collapsible Section
        self.section = CollapsibleSection("⚙️ " + tr("settings_title"))
        layout = self.section.content_layout
        
        # ===== Thread Configuration =====
        thread_group = QGroupBox("🔧 " + tr("settings_thread_config"))
        thread_layout = QVBoxLayout()
        
        # CPU Info
        cpu_brand = self.system_info.get('cpu_brand', 'N/A')
        cpu_count = self.system_info.get('cpu_count', 4)
        recommended = self.system_info.get('recommended_threads', 6)
        
        cpu_info_text = "💻 " + tr("settings_cpu_info", brand=cpu_brand, count=cpu_count, rec=recommended)
        cpu_info = QLabel(cpu_info_text)
        cpu_info.setStyleSheet("color: gray; font-size: 11px;")
        thread_layout.addWidget(cpu_info)
        
        # Thread Slider + Spinner
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel(tr("settings_threads")))
        
        self.thread_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.thread_slider.setMinimum(1)
        self.thread_slider.setMaximum(cpu_count)
        self.thread_slider.setValue(recommended)
        self.thread_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.thread_slider.setTickInterval(1)
        self.thread_slider.setToolTip(tr("tooltip_threads"))
        slider_layout.addWidget(self.thread_slider)
        
        self.thread_spinbox = NoScrollSpinBox()
        self.thread_spinbox.setMinimum(1)
        self.thread_spinbox.setMaximum(cpu_count)
        self.thread_spinbox.setValue(recommended)
        self.thread_spinbox.setToolTip(tr("tooltip_threads"))
        slider_layout.addWidget(self.thread_spinbox)
        
        # Slider & Spinbox verbinden
        self.thread_slider.valueChanged.connect(self.thread_spinbox.setValue)
        self.thread_spinbox.valueChanged.connect(self.thread_slider.setValue)
        
        self.thread_slider.valueChanged.connect(self.emit_settings_changed)
        
        thread_layout.addLayout(slider_layout)
        
        hint = QLabel("💡 " + tr("settings_thread_hint"))
        hint.setStyleSheet("color: gray; font-size: 10px;")
        hint.setWordWrap(True)
        thread_layout.addWidget(hint)
        
        thread_group.setLayout(thread_layout)
        layout.addWidget(thread_group)
        
        # ===== Language & Translation =====
        lang_group = QGroupBox("🌍 " + tr("settings_lang_translation"))
        lang_layout = QVBoxLayout()
        
        # Language Selection
        lang_layout.addWidget(QLabel(tr("settings_input_language")))
        
        lang_combo_layout = QHBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇩🇪 Deutsch", "de")
        self.language_combo.addItem("🇬🇧 English", "en")
        self.language_combo.addItem("🇫🇷 Français", "fr")
        self.language_combo.addItem("🇪🇸 Español", "es")
        self.language_combo.addItem("Auto Detect", "auto")
        self.language_combo.setCurrentIndex(0)  # Deutsch default
        self.language_combo.currentIndexChanged.connect(self.emit_settings_changed)
        self.language_combo.setToolTip(tr("tooltip_language"))
        lang_combo_layout.addWidget(self.language_combo)
        lang_combo_layout.addStretch()
        
        lang_layout.addLayout(lang_combo_layout)
        
        # Translation Checkbox
        self.translate_checkbox = QCheckBox(tr("settings_translate"))
        self.translate_checkbox.setChecked(False)
        self.translate_checkbox.stateChanged.connect(self.emit_settings_changed)
        self.translate_checkbox.setToolTip(tr("tooltip_translate"))
        lang_layout.addWidget(self.translate_checkbox)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # ===== Output Options =====
        output_group = QGroupBox("📁 " + tr("settings_output_options"))
        output_layout = QVBoxLayout()
        
        # Keep Temp
        self.keep_temp_checkbox = QCheckBox(tr("settings_keep_temp"))
        self.keep_temp_checkbox.setChecked(False)
        self.keep_temp_checkbox.stateChanged.connect(self.emit_settings_changed)
        self.keep_temp_checkbox.setToolTip(tr("settings_keep_temp_tooltip"))
        output_layout.addWidget(self.keep_temp_checkbox)
        
        hint2 = QLabel("💡 " + tr("settings_keep_temp_hint"))
        hint2.setStyleSheet("color: gray; font-size: 10px;")
        hint2.setWordWrap(True)
        output_layout.addWidget(hint2)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        layout.addStretch()
        
        # Collapsible Section zum Main-Layout hinzufügen
        main_layout.addWidget(self.section)
        self.setLayout(main_layout)
    
    def emit_settings_changed(self):
        """Emittiert Signal mit aktuellen Settings."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """Gibt alle aktuellen Einstellungen zurück."""
        return {
            'threads': self.thread_spinbox.value(),
            'language': self.language_combo.currentData(),
            'translate': self.translate_checkbox.isChecked(),
            'keep_temp': self.keep_temp_checkbox.isChecked(),
        }
    
    def set_settings(self, settings: dict):
        """Setzt Einstellungen (z.B. aus gespeicherten Profilen)."""
        if 'threads' in settings:
            self.thread_spinbox.setValue(settings['threads'])
        
        if 'language' in settings:
            index = self.language_combo.findData(settings['language'])
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
        
        if 'translate' in settings:
            self.translate_checkbox.setChecked(settings['translate'])
        
        if 'keep_temp' in settings:
            self.keep_temp_checkbox.setChecked(settings['keep_temp'])
    
    def set_threads(self, threads: int):
        """
        Setzt die Thread-Anzahl im Slider und Spinbox.
        
        Args:
            threads: Anzahl der Threads (1-cpu_count)
        """
        # Wert begrenzen auf gültigen Bereich
        cpu_count = self.system_info.get('cpu_count', 16)
        threads = max(1, min(cpu_count, threads))
        # Setze beide Widgets (sie sind bereits miteinander verbunden)
        self.thread_spinbox.setValue(threads)

    def refresh_translations(self):
        """Aktualisiert alle übersetzbaren Texte nach einem Sprachwechsel."""
        from .translations import tr

        self.section.set_title(tr("settings_title"), icon="⚙️")
        self.thread_slider.setToolTip(tr("tooltip_threads"))
        self.thread_spinbox.setToolTip(tr("tooltip_threads"))
        self.language_combo.setToolTip(tr("tooltip_language"))
        self.translate_checkbox.setText(tr("settings_translate"))
        self.translate_checkbox.setToolTip(tr("tooltip_translate"))
        self.keep_temp_checkbox.setText(tr("settings_keep_temp"))
        self.keep_temp_checkbox.setToolTip(tr("settings_keep_temp_tooltip"))
    
