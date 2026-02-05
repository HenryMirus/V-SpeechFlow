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
)
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """Hauptfenster der V-SpeechFlow GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V-SpeechFlow - GUI")
        self.setGeometry(100, 100, 1000, 700)
        
        # Zentral-Widget mit Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Placeholder: Label und Button
        title = QLabel("V-SpeechFlow GUI")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Status Bar
        self.statusBar().showMessage("Bereit")
        
        # TODO: Hier werden später die verschiedenen Panels eingefügt
        # - Input Panel (Datei/Live)
        # - Settings Panel (Modell, Threads, etc.)
        # - Output Panel (Vorschau)
        # - Buttons (Start, Stop, etc.)
