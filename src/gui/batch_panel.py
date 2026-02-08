"""
Batch-Processing Panel für V-SpeechFlow

Ermöglicht die Verarbeitung mehrerer Audio-Dateien nacheinander.
"""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QGroupBox,
    QProgressBar,
    QMessageBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent


class BatchPanel(QWidget):
    """Panel für Batch-Processing von mehreren Audio-Dateien."""
    
    # Signals
    batch_started = pyqtSignal()
    batch_finished = pyqtSignal()
    file_processing = pyqtSignal(str, int, int)  # file_path, current, total
    
    SUPPORTED_FORMATS = ("mp3", "m4a", "wav", "flac", "ogg")
    
    def __init__(self):
        super().__init__()
        self.file_list = []
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel("📦 Batch-Processing")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Verarbeite mehrere Audio-Dateien nacheinander")
        info.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info)
        
        # Dateiliste Gruppe
        file_group = QGroupBox("Dateiliste")
        file_layout = QVBoxLayout()
        
        # Liste Widget
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list_widget.setAcceptDrops(True)
        self.file_list_widget.dragEnterEvent = self.dragEnterEvent
        self.file_list_widget.dropEvent = self.dropEvent
        file_layout.addWidget(self.file_list_widget)
        
        # Buttons für Datei-Management
        file_buttons = QHBoxLayout()
        
        btn_add_files = QPushButton("➕ Dateien hinzufügen")
        btn_add_files.clicked.connect(self.add_files)
        file_buttons.addWidget(btn_add_files)
        
        btn_add_folder = QPushButton("📁 Ordner hinzufügen")
        btn_add_folder.clicked.connect(self.add_folder)
        file_buttons.addWidget(btn_add_folder)
        
        btn_remove = QPushButton("➖ Entfernen")
        btn_remove.clicked.connect(self.remove_selected)
        file_buttons.addWidget(btn_remove)
        
        btn_clear = QPushButton("🗑️ Alle löschen")
        btn_clear.clicked.connect(self.clear_all)
        file_buttons.addWidget(btn_clear)
        
        file_layout.addLayout(file_buttons)
        
        # Statistik
        self.stats_label = QLabel("Dateien: 0 | Gesamt: 0 MB")
        self.stats_label.setStyleSheet("color: gray; font-size: 9px;")
        file_layout.addWidget(self.stats_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Optionen
        options_group = QGroupBox("Batch-Optionen")
        options_layout = QVBoxLayout()
        
        self.stop_on_error_checkbox = QCheckBox("Bei Fehler abbrechen")
        self.stop_on_error_checkbox.setChecked(False)
        options_layout.addWidget(self.stop_on_error_checkbox)
        
        self.create_subfolder_checkbox = QCheckBox("Ausgabe in Unterordner speichern")
        self.create_subfolder_checkbox.setChecked(True)
        options_layout.addWidget(self.create_subfolder_checkbox)
        
        hint = QLabel("💡 Alle Dateien werden mit aktuellen Einstellungen verarbeitet")
        hint.setStyleSheet("color: gray; font-size: 9px;")
        hint.setWordWrap(True)
        options_layout.addWidget(hint)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Fortschritt
        progress_group = QGroupBox("Fortschritt")
        progress_layout = QVBoxLayout()
        
        self.current_file_label = QLabel("Bereit...")
        self.current_file_label.setStyleSheet("font-size: 10px;")
        progress_layout.addWidget(self.current_file_label)
        
        self.batch_progress = QProgressBar()
        self.batch_progress.setVisible(False)
        progress_layout.addWidget(self.batch_progress)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag Enter Event für Datei-Drops."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Drop Event für Dateien."""
        urls = event.mimeData().urls()
        files = []
        
        for url in urls:
            file_path = url.toLocalFile()
            path = Path(file_path)
            
            if path.is_file() and path.suffix.lower().lstrip('.') in self.SUPPORTED_FORMATS:
                files.append(str(path))
            elif path.is_dir():
                # Rekursiv alle Audio-Dateien im Ordner finden
                for fmt in self.SUPPORTED_FORMATS:
                    files.extend([str(f) for f in path.rglob(f"*.{fmt}")])
        
        if files:
            self.add_files_to_list(files)
            event.acceptProposedAction()
    
    def add_files(self):
        """Öffnet Dialog zum Hinzufügen von Dateien."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Audio-Dateien auswählen",
            "",
            f"Audio-Dateien ({' '.join(f'*.{fmt}' for fmt in self.SUPPORTED_FORMATS)});;Alle Dateien (*)"
        )
        
        if files:
            self.add_files_to_list(files)
    
    def add_folder(self):
        """Öffnet Dialog zum Hinzufügen eines Ordners."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Ordner auswählen"
        )
        
        if folder:
            folder_path = Path(folder)
            files = []
            for fmt in self.SUPPORTED_FORMATS:
                files.extend([str(f) for f in folder_path.rglob(f"*.{fmt}")])
            
            if files:
                self.add_files_to_list(files)
            else:
                QMessageBox.information(
                    self,
                    "Keine Dateien gefunden",
                    f"Keine unterstützten Audio-Dateien im Ordner gefunden."
                )
    
    def add_files_to_list(self, files: List[str]):
        """Fügt Dateien zur Liste hinzu."""
        for file_path in files:
            if file_path not in self.file_list:
                self.file_list.append(file_path)
                
                path = Path(file_path)
                size_mb = path.stat().st_size / 1024 / 1024
                
                item = QListWidgetItem(f"{path.name} ({size_mb:.1f} MB)")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list_widget.addItem(item)
        
        self.update_stats()
    
    def remove_selected(self):
        """Entfernt ausgewählte Dateien."""
        selected_items = self.file_list_widget.selectedItems()
        
        if not selected_items:
            return
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.file_list:
                self.file_list.remove(file_path)
            self.file_list_widget.takeItem(self.file_list_widget.row(item))
        
        self.update_stats()
    
    def clear_all(self):
        """Löscht alle Dateien aus der Liste."""
        if not self.file_list:
            return
        
        reply = QMessageBox.question(
            self,
            "Alle löschen?",
            "Möchten Sie wirklich alle Dateien aus der Liste entfernen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.file_list.clear()
            self.file_list_widget.clear()
            self.update_stats()
    
    def update_stats(self):
        """Aktualisiert die Statistik-Anzeige."""
        total_size = 0
        for file_path in self.file_list:
            if Path(file_path).exists():
                total_size += Path(file_path).stat().st_size
        
        total_size_mb = total_size / 1024 / 1024
        self.stats_label.setText(f"Dateien: {len(self.file_list)} | Gesamt: {total_size_mb:.1f} MB")
    
    def get_file_list(self) -> List[str]:
        """Gibt die Liste der Dateien zurück."""
        return self.file_list.copy()
    
    def get_options(self) -> dict:
        """Gibt die Batch-Optionen zurück."""
        return {
            'stop_on_error': self.stop_on_error_checkbox.isChecked(),
            'create_subfolder': self.create_subfolder_checkbox.isChecked(),
        }
    
    def set_progress(self, current: int, total: int, file_name: str = ""):
        """Setzt den Batch-Fortschritt."""
        self.batch_progress.setVisible(True)
        self.batch_progress.setMaximum(total)
        self.batch_progress.setValue(current)
        
        if file_name:
            self.current_file_label.setText(f"Verarbeite ({current}/{total}): {file_name}")
        else:
            self.current_file_label.setText(f"Fortschritt: {current}/{total}")
    
    def reset_progress(self):
        """Setzt den Fortschritt zurück."""
        self.batch_progress.setVisible(False)
        self.batch_progress.setValue(0)
        self.current_file_label.setText("Bereit...")
    
    def set_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert die UI während Batch-Processing."""
        self.file_list_widget.setEnabled(enabled)
        self.findChild(QPushButton, "➕ Dateien hinzufügen").setEnabled(enabled) if self.findChild(QPushButton) else None
