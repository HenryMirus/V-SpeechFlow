"""
PyQt6 Application Entry Point

Startet die GUI-Anwendung für V-SpeechFlow.
"""

import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def main():
    """Haupteinstiegspunkt der GUI-Anwendung."""
    app = QApplication(sys.argv)
    
    # App-Metadaten
    app.setApplicationName("V-SpeechFlow")
    app.setApplicationVersion("0.1.0")
    
    # Hauptfenster erstellen und anzeigen
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
