"""
Installation Wizard für V-SpeechFlow

Führt neue Benutzer durch die Ersteinrichtung.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QStackedWidget,
    QWidget,
    QTextBrowser,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from .translations import tr
from .history import HistoryManager
from .system_utils import get_recommended_threads
from .macos_utils import save_hf_token_to_keychain, is_mac
from pathlib import Path
import platform


class WizardPage(QWidget):
    """Basis-Klasse für Wizard-Seiten."""
    
    def __init__(self, title: str, description: str):
        super().__init__()
        self.title = title
        self.description = description
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI der Seite."""
        layout = QVBoxLayout()
        
        # Titel
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(17)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Beschreibung
        desc_label = QLabel(self.description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addSpacing(20)
        
        # Content-Bereich (wird von Subklassen gefüllt)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        layout.addWidget(self.content_widget)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self) -> dict:
        """Gibt die Daten der Seite zurück."""
        return {}
    
    def is_valid(self) -> bool:
        """Prüft ob die Seite valide ist."""
        return True


class WelcomePage(WizardPage):
    """Willkommensseite des Wizards."""
    
    def __init__(self):
        super().__init__(
            tr("wizard_welcome"),
            tr("wizard_welcome_text")
        )


class ModelPage(WizardPage):
    """Seite zur Modell-Auswahl."""
    
    def __init__(self, history_manager: HistoryManager = None):
        super().__init__(
            tr("wizard_model_title"),
            tr("wizard_model_text")
        )
        
        # Lade bereits gespeichertes Modell aus der History
        saved_model = None
        if history_manager:
            saved_model = history_manager.get_app_setting("default_model")
        
        # Modell-Pfad Eingabe
        model_group = QGroupBox(tr("wizard_model_path"))
        model_layout = QHBoxLayout()
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("z.B. models/ggml-small.bin")
        # Setze gespeichertes Modell, falls vorhanden
        if saved_model:
            self.model_input.setText(saved_model)
        model_layout.addWidget(self.model_input)
        
        browse_btn = QPushButton(tr("browse"))
        browse_btn.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_btn)
        
        model_group.setLayout(model_layout)
        self.content_layout.addWidget(model_group)
        
        # Download-Info
        info_label = QLabel(tr("wizard_model_download"))
        info_label.setWordWrap(True)
        self.content_layout.addWidget(info_label)
        
        # Link
        link_label = QLabel('<a href="https://huggingface.co/ggerganov/whisper.cpp">https://huggingface.co/ggerganov/whisper.cpp</a>')
        link_label.setOpenExternalLinks(True)
        self.content_layout.addWidget(link_label)
        
        # Empfohlene Modelle
        recommendations = QLabel(
            "\n<b>Empfehlungen:</b><br>"
            "• ggml-base.bin (~150 MB) - Schnell<br>"
            "• ggml-small.bin (~500 MB) - Ausgewogen<br>"
            "• ggml-medium.bin (~1.5 GB) - Genau<br>"
            "• ggml-large-v3.bin (~3 GB) - Beste Qualität"
        )
        self.content_layout.addWidget(recommendations)
    
    def browse_model(self):
        """Öffnet Datei-Dialog für Modell-Auswahl."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Modell auswählen",
            str(Path.home()),
            "Whisper Models (*.bin);;All Files (*)"
        )
        if file_path:
            self.model_input.setText(file_path)
    
    def get_data(self) -> dict:
        """Gibt Modell-Pfad zurück."""
        return {"default_model": self.model_input.text()}
    
    def is_valid(self) -> bool:
        """Prüft ob Modell-Pfad optional valid ist."""
        # Modell ist optional beim Setup
        model_path = self.model_input.text().strip()
        if not model_path:
            return True  # Optional
        return Path(model_path).exists()


class TokenPage(WizardPage):
    """Seite für HuggingFace Token."""
    
    def __init__(self):
        super().__init__(
            tr("wizard_token_title"),
            tr("wizard_token_text")
        )
        
        # Token-Eingabe
        token_group = QGroupBox(tr("wizard_token_input"))
        token_layout = QVBoxLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("hf_xxxxxxxxxxxxxxxxxxxx")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout.addWidget(self.token_input)
        
        # Show/Hide Button
        show_btn = QCheckBox("Token anzeigen")
        show_btn.toggled.connect(lambda checked: 
            self.token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            ))
        token_layout.addWidget(show_btn)
        
        token_group.setLayout(token_layout)
        self.content_layout.addWidget(token_group)
        
        # Hilfe-Text
        help_label = QLabel(tr("wizard_token_help"))
        help_label.setWordWrap(True)
        self.content_layout.addWidget(help_label)
        
        # Link
        link_label = QLabel('<a href="https://huggingface.co/settings/tokens">https://huggingface.co/settings/tokens</a>')
        link_label.setOpenExternalLinks(True)
        self.content_layout.addWidget(link_label)
        
        # Info
        keychain_info = "in der macOS Keychain" if is_mac() else "lokal"
        info_label = QLabel(
            f"\n<i>Hinweis: Der Token wird sicher {keychain_info} gespeichert und kann später "
            "jederzeit geändert werden. Sie können diesen Schritt auch überspringen.</i>"
        )
        info_label.setWordWrap(True)
        self.content_layout.addWidget(info_label)
    
    def get_data(self) -> dict:
        """Gibt HF Token zurück."""
        return {"hf_token": self.token_input.text().strip()}
    
    def is_valid(self) -> bool:
        """Token ist optional."""
        return True


class PreferencesPage(WizardPage):
    """Seite für Benutzer-Präferenzen."""
    
    def __init__(self, history_manager: HistoryManager = None):
        super().__init__(
            tr("wizard_preferences_title"),
            tr("wizard_preferences_text")
        )
        
        # Lade bereits gespeicherte Einstellungen aus der History
        saved_ui_lang = None
        saved_theme = None
        saved_threads = None
        saved_auto_open = False
        saved_check_updates = True
        
        if history_manager:
            saved_ui_lang = history_manager.get_app_setting("ui_language")
            saved_theme = history_manager.get_app_setting("preferred_theme")
            saved_threads = history_manager.get_app_setting("default_threads")
            saved_auto_open = history_manager.get_user_preference("auto_open_transcript", False)
            saved_check_updates = history_manager.get_user_preference("check_model_updates", True)
        
        # Sprache
        lang_group = QGroupBox(tr("wizard_language"))
        lang_layout = QHBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Deutsch", "English"])
        # Setze gespeicherte Sprache, falls vorhanden
        if saved_ui_lang == "en":
            self.language_combo.setCurrentIndex(1)
        elif saved_ui_lang == "de":
            self.language_combo.setCurrentIndex(0)
        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        self.content_layout.addWidget(lang_group)
        
        # Theme
        theme_group = QGroupBox(tr("wizard_theme"))
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Hell", "Dunkel"])
        # Setze gespeichertes Theme, falls vorhanden
        if saved_theme == "dark":
            self.theme_combo.setCurrentIndex(1)
        elif saved_theme == "light":
            self.theme_combo.setCurrentIndex(0)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        self.content_layout.addWidget(theme_group)
        
        # Threads
        threads_group = QGroupBox(tr("wizard_threads"))
        threads_layout = QHBoxLayout()
        self.threads_spin = QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(32)
        # Verwende gespeicherten Wert oder empfohlenen Default
        default_threads = saved_threads if saved_threads else get_recommended_threads()
        self.threads_spin.setValue(default_threads)
        threads_layout.addWidget(self.threads_spin)
        recommended_label = QLabel(f"(Empfohlen: {get_recommended_threads()})")
        threads_layout.addWidget(recommended_label)
        threads_layout.addStretch()
        threads_group.setLayout(threads_layout)
        self.content_layout.addWidget(threads_group)
        
        # Checkboxes
        self.auto_open_check = QCheckBox(tr("wizard_auto_open"))
        self.auto_open_check.setChecked(saved_auto_open)
        self.content_layout.addWidget(self.auto_open_check)
        
        self.check_updates_check = QCheckBox(tr("wizard_check_updates"))
        self.check_updates_check.setChecked(saved_check_updates)
        self.content_layout.addWidget(self.check_updates_check)
    
    def get_data(self) -> dict:
        """Gibt Präferenzen zurück."""
        return {
            "ui_language": "de" if self.language_combo.currentIndex() == 0 else "en",
            "preferred_theme": "light" if self.theme_combo.currentIndex() == 0 else "dark",
            "default_threads": self.threads_spin.value(),
            "auto_open_transcript": self.auto_open_check.isChecked(),
            "check_model_updates": self.check_updates_check.isChecked(),
        }


class CompletePage(WizardPage):
    """Abschlussseite des Wizards."""
    
    tutorial_requested = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__(
            tr("wizard_complete_title"),
            tr("wizard_complete_text")
        )
        
        # Info-Text
        info_label = QLabel(
            "Möchten Sie ein kurzes Tutorial starten?\n"
            "Es erklärt die wichtigsten Funktionen von V-SpeechFlow."
        )
        info_label.setWordWrap(True)
        self.content_layout.addWidget(info_label)
        
        self.content_layout.addSpacing(20)
        
        # Tutorial-Buttons
        button_layout = QHBoxLayout()
        
        self.tutorial_btn = QPushButton(tr("wizard_start_tutorial"))
        self.tutorial_btn.clicked.connect(lambda: self.on_tutorial_choice(True))
        button_layout.addWidget(self.tutorial_btn)
        
        self.skip_btn = QPushButton(tr("wizard_skip_tutorial"))
        self.skip_btn.clicked.connect(lambda: self.on_tutorial_choice(False))
        button_layout.addWidget(self.skip_btn)
        
        self.content_layout.addLayout(button_layout)
        
        self.start_tutorial = False
    
    def on_tutorial_choice(self, start: bool):
        """Handler für Tutorial-Auswahl."""
        self.start_tutorial = start
        self.tutorial_requested.emit(start)
    
    def get_data(self) -> dict:
        """Gibt Tutorial-Präferenz zurück."""
        return {"start_tutorial": self.start_tutorial}


class InstallationWizard(QDialog):
    """
    Setup-Wizard für die Ersteinrichtung von V-SpeechFlow.
    
    Führt durch:
    1. Willkommen
    2. Modell-Auswahl
    3. HF-Token (optional)
    4. Präferenzen
    5. Abschluss
    """
    
    wizard_completed = pyqtSignal(dict)  # Emittiert alle gesammelten Daten
    
    def __init__(self, parent=None, history_manager=None):
        super().__init__(parent)
        self.setWindowTitle(tr("wizard_title"))
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # Verwende übergebenen HistoryManager oder erstelle neuen
        if history_manager is not None:
            print("✓ Wizard verwendet übergebenen HistoryManager")
            self.history_manager = history_manager
        else:
            print("⚠ Wizard erstellt eigenen HistoryManager")
            self.history_manager = HistoryManager()
        
        # Stelle sicher, dass History-Datei und Verzeichnis existieren
        self.history_manager.history_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 History-Datei: {self.history_manager.history_file}")
        print(f"📊 Vor Wizard - first_run: {self.history_manager.is_first_run()}, wizard_completed: {self.history_manager.is_wizard_completed()}")
        
        self.collected_data = {}
        self.wizard_is_first_run = self.history_manager.is_first_run()
        
        # Sobald der Wizard startet, ist es kein erster Start mehr
        if self.wizard_is_first_run:
            print("=== Wizard startet zum ersten Mal - setze first_run auf False ===")
            self.history_manager.save_app_setting("first_run", False)
            print(f"📊 Nach first_run=False - Status: {self.history_manager.is_first_run()}")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI des Wizards."""
        layout = QVBoxLayout()
        
        # Stacked Widget für Seiten
        self.pages = QStackedWidget()
        
        # Seiten hinzufügen (mit History-Manager für gespeicherte Werte)
        self.welcome_page = WelcomePage()
        self.model_page = ModelPage(self.history_manager)
        self.token_page = TokenPage()
        self.preferences_page = PreferencesPage(self.history_manager)
        self.complete_page = CompletePage()
        
        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.model_page)
        self.pages.addWidget(self.token_page)
        self.pages.addWidget(self.preferences_page)
        self.pages.addWidget(self.complete_page)
        
        layout.addWidget(self.pages)
        
        # Navigation-Buttons
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton(tr("back"))
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        button_layout.addWidget(self.back_btn)
        
        button_layout.addStretch()
        
        self.next_btn = QPushButton(tr("next"))
        self.next_btn.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_btn)
        
        self.finish_btn = QPushButton(tr("finish"))
        self.finish_btn.clicked.connect(self.finish_wizard)
        self.finish_btn.setVisible(False)
        button_layout.addWidget(self.finish_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Tutorial-Signal verbinden
        self.complete_page.tutorial_requested.connect(self.on_tutorial_requested)
    
    def go_next(self):
        """Geht zur nächsten Seite."""
        current_index = self.pages.currentIndex()
        current_page = self.pages.currentWidget()
        
        print(f"=== go_next() - Seite {current_index} ===")
        
        # Validierung
        if not current_page.is_valid():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Ungültige Eingabe",
                "Bitte überprüfen Sie Ihre Eingaben."
            )
            return
        
        # Daten sammeln
        page_data = current_page.get_data()
        print(f"Seiten-Daten: {page_data}")
        self.collected_data.update(page_data)
        
        print(f"Gesammelte Daten bisher: {self.collected_data}")
        
        # Zur nächsten Seite
        if current_index < self.pages.count() - 1:
            self.pages.setCurrentIndex(current_index + 1)
            self.update_buttons()
    
    def go_back(self):
        """Geht zur vorherigen Seite."""
        current_index = self.pages.currentIndex()
        if current_index > 0:
            self.pages.setCurrentIndex(current_index - 1)
            self.update_buttons()
    
    def update_buttons(self):
        """Aktualisiert die Button-Zustände."""
        current_index = self.pages.currentIndex()
        
        # Back-Button
        self.back_btn.setEnabled(current_index > 0)
        
        # Next/Finish-Button
        is_last_page = current_index == self.pages.count() - 1
        self.next_btn.setVisible(not is_last_page)
        self.finish_btn.setVisible(is_last_page)
    
    def on_tutorial_requested(self, start_tutorial: bool):
        """Handler wenn Tutorial requested wird."""
        print(f"=== on_tutorial_requested({start_tutorial}) ===")
        self.complete_page.start_tutorial = start_tutorial
        # Automatisch zum Finish-Button weiterleiten
        print("Rufe finish_wizard() in 300ms auf...")
        QTimer.singleShot(300, self.finish_wizard)
    
    def finish_wizard(self):
        """Schließt den Wizard ab und speichert Settings."""
        from PyQt6.QtWidgets import QMessageBox
        
        print("=== finish_wizard() aufgerufen ===")
        
        # Letzte Seite Daten sammeln
        self.collected_data.update(self.complete_page.get_data())
        
        print(f"Gesammelte Daten: {self.collected_data}")
        
        # HF-Token in Keychain speichern (nicht in History!)
        hf_token = self.collected_data.get("hf_token", "").strip()
        if hf_token:
            if is_mac():
                success = save_hf_token_to_keychain(hf_token)
                if not success:
                    QMessageBox.warning(
                        self,
                        "Token-Speicherung fehlgeschlagen",
                        "Der HuggingFace Token konnte nicht in der Keychain gespeichert werden.\n"
                        "Sie können ihn später manuell im Diarization-Panel eingeben."
                    )
            else:
                QMessageBox.information(
                    self,
                    "Keychain nicht verfügbar",
                    "Die Keychain-Speicherung ist nur auf macOS verfügbar.\n"
                    "Sie müssen den Token später manuell im Diarization-Panel eingeben."
                )
        
        # Bereite Konfiguration vor (ohne hf_token und start_tutorial)
        print("\n=== 💾 Speichere Wizard-Konfiguration ===")
        initial_config = {k: v for k, v in self.collected_data.items() 
                         if k not in ('hf_token', 'start_tutorial')}
        
        # Speichere als initial_config (wird beim ersten Start geladen)
        self.history_manager.save_initial_config(initial_config)
        print(f"  ✓ Initial-Config gespeichert: {list(initial_config.keys())}")
        
        # Speichere User-Preferences (unabhängig von Sessions)
        if 'ui_language' in initial_config:
            self.history_manager.save_user_preference('ui_language', initial_config['ui_language'])
        if 'preferred_theme' in initial_config:
            self.history_manager.save_user_preference('preferred_theme', initial_config['preferred_theme'])
        if 'check_model_updates' in initial_config:
            self.history_manager.save_user_preference('check_model_updates', initial_config['check_model_updates'])
        print("  ✓ User-Preferences gespeichert")
        
        # Wizard als abgeschlossen markieren
        print("\n🎉 Markiere Wizard als abgeschlossen...")
        self.history_manager.mark_wizard_completed(version="1.0")
        
        # Explizit nochmal speichern um sicherzustellen dass alles geschrieben wurde
        print("💾 Finales Speichern...")
        self.history_manager._save_history()
        
        print(f"\n📊 Finale History-Werte:")
        print(f"  - first_run: {self.history_manager.history_data.get('app_settings', {}).get('first_run')}")
        print(f"  - wizard_completed: {self.history_manager.history_data.get('app_settings', {}).get('wizard_completed')}")
        print(f"  - initial_config: {list(initial_config.keys())}")
        print("=== ✅ finish_wizard() abgeschlossen ===")
        
        # Signal emittieren
        self.wizard_completed.emit(self.collected_data)
        
        # Dialog schließen
        self.accept()
