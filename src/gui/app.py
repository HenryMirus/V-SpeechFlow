"""
PyQt6 Application Entry Point

Startet die GUI-Anwendung für V-SpeechFlow.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from .main_window import MainWindow
from .history import HistoryManager
from .installation_wizard import InstallationWizard
from .onboarding import OnboardingManager


def main():
    """Haupteinstiegspunkt der GUI-Anwendung."""
    app = QApplication(sys.argv)
    
    # App-Metadaten
    app.setApplicationName("V-SpeechFlow")
    app.setApplicationVersion("0.1.0")
    
    # History-Manager für First-Run Check
    history_manager = HistoryManager()
    
    # Hauptfenster erstellen
    window = MainWindow()
    
    # Prüfen ob erster Start
    if history_manager.is_first_run() or not history_manager.is_wizard_completed():
        # Installation Wizard zeigen - WICHTIG: Übergebe MainWindow's HistoryManager!
        wizard = InstallationWizard(window, window.history_manager)
        
        def on_wizard_completed(data: dict):
            """Handler wenn Wizard abgeschlossen wurde."""
            # History neu laden um Wizard-Änderungen zu übernehmen
            window.history_manager.history_data = window.history_manager._load_history()
            print(f"✓ History nach Wizard neu geladen: first_run={window.history_manager.is_first_run()}, wizard_completed={window.history_manager.is_wizard_completed()}")
            
            # Fenster anzeigen
            window.show()
            
            # Einstellungen in UI laden
            window.apply_wizard_settings(data)
            
            # Onboarding starten wenn gewünscht
            if data.get('start_tutorial', False):
                # Kurz warten damit das Fenster gerendert wird
                QTimer.singleShot(500, lambda: window.start_onboarding())
        
        wizard.wizard_completed.connect(on_wizard_completed)
        wizard.exec()
    else:
        # Normaler Start
        window.show()
        
        # Onboarding anbieten wenn noch nicht absolviert
        if not history_manager.is_onboarding_completed():
            # Kurz warten und dann fragen
            QTimer.singleShot(1000, lambda: window.offer_onboarding())
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
