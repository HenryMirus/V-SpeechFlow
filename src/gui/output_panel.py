"""
Output Panel für Ausgabe-Verwaltung

Ermöglicht Konfiguration von Ausgabedatei, Format und Timestamps.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .translations import tr
from .translations import tr


class OutputPanel(QWidget):
    """Panel für Output-Einstellungen."""
    
    # Signals
    output_changed = pyqtSignal(dict)  # Emitted wenn sich Settings ändern
    
    def __init__(self):
        super().__init__()
        self.selected_output_path = None
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel("📝 Ausgabe-Einstellungen")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # === Ausgabedatei ===
        output_group = QGroupBox("Ausgabedatei")
        output_layout = QVBoxLayout()
        
        # Pfad-Auswahl
        path_layout = QHBoxLayout()
        
        self.output_path_input = QLineEdit()
        self.output_path_input.setPlaceholderText("Automatisch neben Input-Datei oder eigenen Pfad wählen...")
        self.output_path_input.textChanged.connect(self.on_path_changed)
        self.output_path_input.setToolTip(tr("tooltip_output_path"))
        path_layout.addWidget(self.output_path_input)
        
        btn_browse = QPushButton("📂 Speichern unter...")
        btn_browse.clicked.connect(self.browse_output_file)
        btn_browse.setToolTip(tr("tooltip_output_path"))
        path_layout.addWidget(btn_browse)
        
        btn_clear = QPushButton("✕")
        btn_clear.setFixedWidth(40)
        btn_clear.clicked.connect(self.clear_output_path)
        btn_clear.setToolTip("Pfad löschen (automatische Benennung)")
        path_layout.addWidget(btn_clear)
        
        output_layout.addLayout(path_layout)
        
        # Validierungs-Status
        self.path_status = QLabel("💡 Automatisch: <input_name>_transcript.txt")
        self.path_status.setStyleSheet("color: gray; font-size: 10px;")
        self.path_status.setWordWrap(True)
        output_layout.addWidget(self.path_status)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # === Format-Optionen ===
        format_group = QGroupBox("Format & Struktur")
        format_layout = QVBoxLayout()
        
        # Timestamps Checkbox
        self.timestamps_checkbox = QCheckBox("Segmente mit Timestamps (-s)")
        self.timestamps_checkbox.setChecked(False)
        self.timestamps_checkbox.stateChanged.connect(self.emit_settings_changed)
        self.timestamps_checkbox.setToolTip(tr("tooltip_segments"))
        format_layout.addWidget(self.timestamps_checkbox)
        
        timestamps_hint = QLabel("💡 Beispiel: [00:00:00.000 --> 00:00:05.000] Text hier...")
        timestamps_hint.setStyleSheet("color: gray; font-size: 10px; margin-left: 20px;")
        timestamps_hint.setWordWrap(True)
        format_layout.addWidget(timestamps_hint)
        
        format_layout.addSpacing(10)
        
        # Output-Format Auswahl
        format_layout.addWidget(QLabel("Ausgabe-Format:"))
        
        self.format_group = QButtonGroup(self)
        
        self.plain_radio = QRadioButton("Plain Text (.txt)")
        self.plain_radio.setChecked(True)
        self.plain_radio.toggled.connect(self.emit_settings_changed)
        self.plain_radio.setToolTip("Einfacher Text ohne Metadaten")
        self.format_group.addButton(self.plain_radio, 1)
        format_layout.addWidget(self.plain_radio)
        
        plain_hint = QLabel("Einfacher Text, ideal für Notizen und Dokumentation")
        plain_hint.setStyleSheet("color: gray; font-size: 10px; margin-left: 20px;")
        format_layout.addWidget(plain_hint)
        
        self.structured_radio = QRadioButton("Strukturiert mit Metadaten (.txt)")
        self.structured_radio.toggled.connect(self.emit_settings_changed)
        self.structured_radio.setToolTip("Mit Header (Datum, Modell, Settings)")
        self.format_group.addButton(self.structured_radio, 2)
        format_layout.addWidget(self.structured_radio)
        
        structured_hint = QLabel("Mit Header (Datum, Modell, Settings, etc.)")
        structured_hint.setStyleSheet("color: gray; font-size: 10px; margin-left: 20px;")
        format_layout.addWidget(structured_hint)
        
        format_layout.addSpacing(10)
        
        # Preview Example
        preview_label = QLabel("📋 Vorschau-Beispiel:")
        preview_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        format_layout.addWidget(preview_label)
        
        self.preview_text = QLabel(self._get_preview_text())
        self.preview_text.setStyleSheet(
            "background-color: #f5f5f5; padding: 10px; "
            "border-radius: 4px; font-family: monospace; font-size: 10px; color: black;"
        )
        self.preview_text.setWordWrap(True)
        self.preview_text.setTextFormat(Qt.TextFormat.PlainText)
        format_layout.addWidget(self.preview_text)
        
        # Preview aktualisieren wenn Format sich ändert
        self.timestamps_checkbox.stateChanged.connect(self.update_preview)
        self.plain_radio.toggled.connect(self.update_preview)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # === Zusätzliche Optionen ===
        extra_group = QGroupBox("Zusätzliche Optionen")
        extra_layout = QVBoxLayout()
        
        self.auto_open_checkbox = QCheckBox("Transkript nach Fertigstellung automatisch öffnen")
        self.auto_open_checkbox.setChecked(False)
        self.auto_open_checkbox.stateChanged.connect(self.emit_settings_changed)
        self.auto_open_checkbox.setToolTip("Öffnet die Ausgabedatei automatisch nach erfolgreicher Transkription")
        extra_layout.addWidget(self.auto_open_checkbox)
        
        extra_group.setLayout(extra_layout)
        layout.addWidget(extra_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def browse_output_file(self):
        """Öffnet Dialog zur Auswahl des Ausgabepfads."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Ausgabedatei wählen",
            "",
            "Text Dateien (*.txt);;Alle Dateien (*)"
        )
        
        if file_path:
            # Stelle sicher dass .txt Extension vorhanden ist
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            
            self.output_path_input.setText(file_path)
    
    def clear_output_path(self):
        """Löscht den Ausgabepfad (zurück zu automatisch)."""
        self.output_path_input.clear()
        self.selected_output_path = None
    
    def on_path_changed(self):
        """Wird aufgerufen wenn sich der Pfad ändert."""
        path_text = self.output_path_input.text().strip()
        
        if not path_text:
            self.selected_output_path = None
            self.path_status.setText("💡 Automatisch: <input_name>_transcript.txt")
            self.path_status.setStyleSheet("color: gray; font-size: 10px;")
        else:
            # Validiere Pfad
            path = Path(path_text)
            
            # Prüfe ob Parent-Verzeichnis existiert (oder erstellt werden kann)
            parent = path.parent
            
            if parent.exists() and parent.is_dir():
                self.selected_output_path = str(path)
                self.path_status.setText(f"✓ Ausgabe nach: {path.name}")
                self.path_status.setStyleSheet("color: green; font-size: 10px;")
            elif str(parent) == ".":
                # Relativer Pfad, nur Dateiname
                self.selected_output_path = str(path)
                self.path_status.setText(f"✓ Ausgabe: {path.name} (im aktuellen Verzeichnis)")
                self.path_status.setStyleSheet("color: green; font-size: 10px;")
            else:
                self.selected_output_path = str(path)
                self.path_status.setText(f"⚠ Verzeichnis existiert nicht: {parent}")
                self.path_status.setStyleSheet("color: orange; font-size: 10px;")
        
        self.emit_settings_changed()
    
    def update_preview(self):
        """Aktualisiert die Vorschau basierend auf den aktuellen Einstellungen."""
        self.preview_text.setText(self._get_preview_text())
    
    def _get_preview_text(self) -> str:
        """Generiert Beispiel-Text basierend auf aktuellen Einstellungen."""
        has_timestamps = self.timestamps_checkbox.isChecked()
        is_structured = self.structured_radio.isChecked()
        
        if is_structured:
            preview = """=== V-SpeechFlow Transkript ===
Datum: 2026-02-05 14:30:00
Modell: ggml-small.bin
Sprache: Deutsch
Diarization: 2 Sprecher
================================

"""
        else:
            preview = ""
        
        if has_timestamps:
            preview += "[00:00:00.000 --> 00:00:05.120]  SPEAKER_00: Hallo und willkommen...\n"
            preview += "[00:00:05.200 --> 00:00:10.340]  SPEAKER_01: Vielen Dank für die Einladung."
        else:
            preview += "SPEAKER_00: Hallo und willkommen...\n"
            preview += "SPEAKER_01: Vielen Dank für die Einladung."
        
        return preview
    
    def emit_settings_changed(self):
        """Emittiert Signal mit aktuellen Output-Settings."""
        settings = self.get_settings()
        self.output_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """
        Gibt alle aktuellen Output-Einstellungen zurück.
        
        Returns:
            Dict mit allen Einstellungen
        """
        output_format = 'structured' if self.structured_radio.isChecked() else 'plain'
        
        return {
            'output_path': self.selected_output_path,
            'timestamps': self.timestamps_checkbox.isChecked(),
            'format': output_format,
            'auto_open': self.auto_open_checkbox.isChecked(),
        }
    
    def validate_settings(self) -> tuple[bool, Optional[str]]:
        """
        Validiert die Output-Einstellungen.
        
        Returns:
            Tuple (is_valid, error_message)
        """
        settings = self.get_settings()
        
        # Wenn custom output path gesetzt, prüfe Schreibbarkeit
        if settings['output_path']:
            path = Path(settings['output_path'])
            parent = path.parent
            
            # Prüfe ob Parent-Verzeichnis existiert oder erstellt werden kann
            if not parent.exists():
                try:
                    # Versuche zu erstellen (dry-run, nicht wirklich erstellen)
                    # Nur prüfen ob es grundsätzlich möglich wäre
                    if not str(parent).startswith(('/', 'C:', 'D:', 'E:')):
                        # Relativer Pfad ist OK
                        pass
                    elif not parent.parent.exists():
                        return False, f"Übergeordnetes Verzeichnis existiert nicht: {parent.parent}"
                except Exception as e:
                    return False, f"Ungültiger Ausgabepfad: {str(e)}"
            
            # Prüfe ob Verzeichnis schreibbar ist
            if parent.exists() and not parent.is_dir():
                return False, f"Pfad ist keine Verzeichnis: {parent}"
        
        return True, None
    
    def set_settings(self, settings: dict):
        """
        Setzt Output-Einstellungen (z.B. aus gespeicherten Profilen).
        
        Args:
            settings: Dict mit Einstellungen
        """
        if 'output_path' in settings and settings['output_path']:
            self.output_path_input.setText(settings['output_path'])
        
        if 'timestamps' in settings:
            self.timestamps_checkbox.setChecked(settings['timestamps'])
        
        if 'format' in settings:
            if settings['format'] == 'structured':
                self.structured_radio.setChecked(True)
            else:
                self.plain_radio.setChecked(True)
        
        if 'auto_open' in settings:
            self.auto_open_checkbox.setChecked(settings['auto_open'])
    
    def get_output_path(self, input_file: Optional[str] = None) -> str:
        """
        Gibt den finalen Ausgabepfad zurück.
        
        Args:
            input_file: Optional Input-Datei für automatische Benennung
        
        Returns:
            Pfad zur Ausgabedatei
        """
        if self.selected_output_path:
            return self.selected_output_path
        
        # Automatische Benennung basierend auf Input
        if input_file:
            input_path = Path(input_file)
            output_name = f"{input_path.stem}_transcript.txt"
            return str(input_path.parent / output_name)
        
        # Fallback
        return "transcript_output.txt"
    
    def set_auto_open(self, enabled: bool):
        """
        Setzt den Auto-Open Zustand der Checkbox.
        
        Args:
            enabled: True um Auto-Open zu aktivieren, False zum Deaktivieren
        """
        self.auto_open_checkbox.setChecked(enabled)
