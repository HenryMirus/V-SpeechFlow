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
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QDragLeaveEvent
from .translations import tr
from .constants import SUPPORTED_AUDIO_FORMATS
import logging

logger = logging.getLogger(__name__)


class BatchPanel(QWidget):
    """Panel für Batch-Processing von mehreren Audio-Dateien."""
    
    # Signals
    batch_started = pyqtSignal()
    batch_finished = pyqtSignal()
    file_processing = pyqtSignal(str, int, int)  # file_path, current, total
    
    SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS
    
    def __init__(self):
        super().__init__()
        self.file_list = []
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Drag & Drop auf dem gesamten Panel aktivieren
        self.setAcceptDrops(True)
        
        # Titel
        title = QLabel("📦 " + tr("batch_title"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Drop-Hinweis
        self.drop_hint = QLabel("⬇️ " + tr("batch_drop_hint"))
        self.drop_hint.setStyleSheet("color: gray; font-size: 11px; font-style: italic;")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.drop_hint)
        
        info = QLabel(tr("batch_info"))
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)
        
        # Dateiliste Gruppe
        file_group = QGroupBox(tr("batch_file_list"))
        file_layout = QVBoxLayout()
        
        # Liste Widget – Drag & Drop wird über das Panel gesteuert
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list_widget.setAcceptDrops(False)
        file_layout.addWidget(self.file_list_widget)
        
        # Buttons für Datei-Management
        file_buttons = QHBoxLayout()
        
        btn_add_files = QPushButton("➕ " + tr("batch_btn_add_files"))
        btn_add_files.clicked.connect(self.add_files)
        file_buttons.addWidget(btn_add_files)
        
        btn_add_folder = QPushButton("📁 " + tr("batch_btn_add_folder"))
        btn_add_folder.clicked.connect(self.add_folder)
        file_buttons.addWidget(btn_add_folder)
        
        btn_remove = QPushButton("➖ " + tr("batch_btn_remove"))
        btn_remove.clicked.connect(self.remove_selected)
        file_buttons.addWidget(btn_remove)
        
        btn_clear = QPushButton("🗑️ " + tr("batch_btn_clear"))
        btn_clear.clicked.connect(self.clear_all)
        file_buttons.addWidget(btn_clear)
        
        file_layout.addLayout(file_buttons)
        
        # Statistik
        self.stats_label = QLabel(tr("batch_stats", count=0, size=0))
        self.stats_label.setStyleSheet("color: gray; font-size: 10px;")
        file_layout.addWidget(self.stats_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Optionen
        options_group = QGroupBox(tr("batch_options"))
        options_layout = QVBoxLayout()
        
        self.stop_on_error_checkbox = QCheckBox(tr("batch_stop_on_error"))
        self.stop_on_error_checkbox.setChecked(False)
        options_layout.addWidget(self.stop_on_error_checkbox)
        
        self.create_subfolder_checkbox = QCheckBox(tr("batch_subfolder"))
        self.create_subfolder_checkbox.setChecked(True)
        options_layout.addWidget(self.create_subfolder_checkbox)
        
        hint = QLabel("💡 " + tr("batch_hint"))
        hint.setStyleSheet("color: gray; font-size: 10px;")
        hint.setWordWrap(True)
        options_layout.addWidget(hint)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Fortschritt
        progress_group = QGroupBox(tr("batch_progress_title"))
        progress_layout = QVBoxLayout()
        
        self.current_file_label = QLabel(tr("batch_status_ready"))
        self.current_file_label.setStyleSheet("font-size: 11px;")
        progress_layout.addWidget(self.current_file_label)
        
        self.batch_progress = QProgressBar()
        self.batch_progress.setVisible(False)
        progress_layout.addWidget(self.batch_progress)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag Enter Event für Datei-Drops mit visuellem Feedback."""
        if event.mimeData().hasUrls():
            # Prüfen ob mindestens eine gültige Audio-Datei oder ein Ordner dabei ist
            has_valid = False
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                path = Path(file_path)
                if path.is_dir():
                    has_valid = True
                    break
                if path.is_file() and path.suffix.lower().lstrip('.') in self.SUPPORTED_FORMATS:
                    has_valid = True
                    break
            
            if has_valid:
                # Grünes Highlight – gültige Dateien
                self.file_list_widget.setStyleSheet(
                    "QListWidget { border: 2px solid #4CAF50; background-color: #f0f8f0; border-radius: 4px; }"
                )
                self.drop_hint.setText("✅ Loslassen zum Hinzufügen")
                self.drop_hint.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
                event.acceptProposedAction()
                return
        
        # Rotes Highlight – ungültige Dateien
        self.file_list_widget.setStyleSheet(
            "QListWidget { border: 2px solid #f44336; background-color: #f8f0f0; border-radius: 4px; }"
        )
        self.drop_hint.setText("❌ Nicht unterstütztes Format")
        self.drop_hint.setStyleSheet("color: #f44336; font-size: 11px; font-weight: bold;")
        event.ignore()
    
    def dragLeaveEvent(self, event: QDragLeaveEvent):
        """Entfernt visuelles Feedback wenn Drag verlässt."""
        self.file_list_widget.setStyleSheet("")
        self.drop_hint.setText("⬇️ " + tr("batch_drop_hint"))
        self.drop_hint.setStyleSheet("color: gray; font-size: 11px; font-style: italic;")
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Drop Event für Dateien."""
        # Visuelles Feedback zurücksetzen
        self.file_list_widget.setStyleSheet("")
        self.drop_hint.setText("⬇️ " + tr("batch_drop_hint"))
        self.drop_hint.setStyleSheet("color: gray; font-size: 11px; font-style: italic;")
        
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
            tr("batch_file_dialog_title"),
            "",
            f"Audio-Dateien ({' '.join(f'*.{fmt}' for fmt in self.SUPPORTED_FORMATS)});;Alle Dateien (*)"
        )
        
        if files:
            self.add_files_to_list(files)
    
    def add_folder(self):
        """Öffnet Dialog zum Hinzufügen eines Ordners."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("batch_folder_dialog_title")
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
                    tr("batch_no_files_title"),
                    tr("batch_no_files_msg")
                )
    
    def add_files_to_list(self, files: List[str]):
        """Fügt Dateien zur Liste hinzu."""
        added_count = 0
        for file_path in files:
            if file_path not in self.file_list:
                self.file_list.append(file_path)
                added_count += 1
                
                path = Path(file_path)
                size_mb = path.stat().st_size / 1024 / 1024
                
                item = QListWidgetItem(f"{path.name} ({size_mb:.1f} MB)")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list_widget.addItem(item)
        
        if added_count > 0:
            logger.info(f"Batch: {added_count} file(s) added, total: {len(self.file_list)}")
        self.update_stats()
    
    def remove_selected(self):
        """Entfernt ausgewählte Dateien."""
        selected_items = self.file_list_widget.selectedItems()
        
        if not selected_items:
            return
        
        logger.info(f"Batch: removing {len(selected_items)} selected file(s)")
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
            tr("batch_clear_confirm_title"),
            tr("batch_clear_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Batch: clearing all {len(self.file_list)} files")
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
        self.stats_label.setText(tr("batch_stats", count=len(self.file_list), size=f"{total_size_mb:.1f}"))
    
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
        self.current_file_label.setText(tr("batch_status_ready"))
    
    def set_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert die UI während Batch-Processing."""
        self.file_list_widget.setEnabled(enabled)
        # Buttons werden über das parent-Widget gesteuert
