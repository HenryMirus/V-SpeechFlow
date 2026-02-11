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
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from .translations import tr
from .history import HistoryManager
from .system_utils import get_recommended_threads
from .macos_utils import save_hf_token_to_keychain, is_mac
from .model_utils import (
    AVAILABLE_MODELS,
    get_model_info,
    get_model_path_in_models_dir,
    is_model_downloaded,
)
from .workers import ModelDownloadWorker
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
    """Willkommensseite des Wizards mit Sprachauswahl."""
    
    def __init__(self, history_manager: HistoryManager = None, wizard=None):
        # Bilinguale Willkommensnachricht
        bilingual_title = "🌍 Willkommen / Welcome"
        bilingual_description = (
            "<div style='line-height: 1.6;'>"
            "<p><b>🇩🇪 Deutsch:</b><br>"
            "Willkommen bei V-SpeechFlow!<br>"
            "Dieser Assistent hilft Ihnen bei der Ersteinrichtung.<br>"
            "Bitte wählen Sie zunächst Ihre bevorzugte Sprache.</p>"
            "<hr>"
            "<p><b>🇺🇸 English:</b><br>"
            "Welcome to V-SpeechFlow!<br>"
            "This wizard will help you with the initial setup.<br>"
            "Please select your preferred language first.</p>"
            "</div>"
        )
        
        super().__init__(bilingual_title, bilingual_description)
        
        # Speichere Referenzen für späteren Zugriff
        self.history_manager = history_manager
        self._wizard = wizard
        
        # Lade bereits gespeicherte Sprache aus user_preferences
        saved_language = None
        if history_manager:
            saved_language = history_manager.get_user_preference("ui_language")
        
        # Sprachauswahl
        from .translations import set_language
        
        language_group = QGroupBox("🌍 Language / Sprache")
        language_layout = QHBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇩🇪 Deutsch", "de")
        self.language_combo.addItem("🇺🇸 English", "en")
        
        # Setze gespeicherte Sprache, falls vorhanden
        if saved_language == "en":
            self.language_combo.setCurrentIndex(1)
        else:
            self.language_combo.setCurrentIndex(0)
        
        # Bei Sprachwechsel: Sprache sofort ändern
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        language_layout.addWidget(self.language_combo)
        language_group.setLayout(language_layout)
        
        self.content_layout.addWidget(language_group)
        
        # Info-Text
        info_label = QLabel(
            "<i>Die Sprache kann später jederzeit in den Einstellungen geändert werden.</i><br>"
            "<i>The language can be changed later at any time in the settings.</i>"
        )
        info_label.setWordWrap(True)
        self.content_layout.addWidget(info_label)
    
    def on_language_changed(self, index: int):
        """Wird aufgerufen wenn die Sprache geändert wird."""
        from .translations import set_language
        language = self.language_combo.itemData(index)
        set_language(language)
        
        # Speichere Sprache sofort in user_preferences (nicht in initial_config)
        if self.history_manager:
            self.history_manager.save_user_preference('ui_language', language)
            print(f"✓ Language '{language}' saved to user_preferences")
        
        # Informiere den Wizard über die Sprachänderung
        if self._wizard is not None:
            self._wizard.on_language_changed()
    
    def get_data(self) -> dict:
        """Gibt die gewählte Sprache zurück."""
        return {"ui_language": self.language_combo.currentData()}


class ModelPage(WizardPage):
    """Seite zur Modell-Auswahl mit direktem Download."""
    
    def __init__(self, history_manager: HistoryManager = None):
        super().__init__(
            tr("wizard_model_title"),
            tr("wizard_model_text")
        )
        self._download_worker = None
        
        # Lade bereits gespeichertes Modell aus der History
        saved_model = None
        if history_manager:
            saved_model = history_manager.get_app_setting("default_model")
        
        # Modell-Schnellauswahl
        select_group = QGroupBox(tr("model_quick_select"))
        select_layout = QVBoxLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.addItem(tr("model_quick_select") + "...", None)
        for filename, info in AVAILABLE_MODELS.items():
            marker = " ✓" if is_model_downloaded(filename) else ""
            display_text = f"{info['name']} - {filename}{marker}"
            self.model_combo.addItem(display_text, filename)
        self.model_combo.currentIndexChanged.connect(self._on_combo_changed)
        select_layout.addWidget(self.model_combo)
        
        # Detail-Label
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: gray; font-size: 11px;")
        select_layout.addWidget(self.detail_label)
        
        select_group.setLayout(select_layout)
        self.content_layout.addWidget(select_group)
        
        # Download-Bereich
        dl_layout = QHBoxLayout()
        self.download_btn = QPushButton("⬇️ " + tr("model_download_btn"))
        self.download_btn.clicked.connect(self._start_download)
        self.download_btn.setVisible(False)
        dl_layout.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton(tr("cancel"))
        self.cancel_btn.clicked.connect(self._cancel_download)
        self.cancel_btn.setVisible(False)
        dl_layout.addWidget(self.cancel_btn)
        self.content_layout.addLayout(dl_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.content_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet("font-size: 11px;")
        self.content_layout.addWidget(self.status_label)
        
        # Modell-Pfad Eingabe (manuell)
        model_group = QGroupBox(tr("wizard_model_path"))
        model_layout = QHBoxLayout()
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(tr("wizard_model_placeholder"))
        if saved_model:
            self.model_input.setText(saved_model)
        model_layout.addWidget(self.model_input)
        
        browse_btn = QPushButton(tr("browse"))
        browse_btn.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_btn)
        
        model_group.setLayout(model_layout)
        self.content_layout.addWidget(model_group)
        
        # Empfohlene Modelle
        recommendations = QLabel(tr("wizard_model_recommendations"))
        self.content_layout.addWidget(recommendations)
    
    def _on_combo_changed(self, index: int):
        """Aktualisiert UI wenn Modell in ComboBox gewählt wird."""
        filename = self.model_combo.currentData()
        if not filename:
            self.detail_label.setText("")
            self.download_btn.setVisible(False)
            return
        
        info = get_model_info(filename)
        if not info:
            return
        
        model_path = get_model_path_in_models_dir(filename)
        self.model_input.setText(str(model_path))
        self.detail_label.setText(
            f"<b>{info['name']}</b> — {info['size_mb']} MB<br>{info['description']}"
        )
        
        if is_model_downloaded(filename):
            self.download_btn.setVisible(False)
            self.status_label.setVisible(True)
            self.status_label.setText("✅ " + tr("model_download_complete"))
            self.status_label.setStyleSheet("font-size: 11px; color: green;")
        else:
            self.download_btn.setVisible(True)
            self.download_btn.setEnabled(True)
            self.download_btn.setText("⬇️ " + tr("model_download_btn"))
            self.status_label.setVisible(False)
    
    def _start_download(self):
        """Startet den Modell-Download."""
        filename = self.model_combo.currentData()
        if not filename:
            return
        info = get_model_info(filename)
        if not info:
            return
        
        dest_path = get_model_path_in_models_dir(filename)
        
        self.download_btn.setEnabled(False)
        self.download_btn.setText(tr("model_download_in_progress"))
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText(tr("model_download_starting"))
        self.status_label.setStyleSheet("font-size: 11px; color: gray;")
        
        self._download_worker = ModelDownloadWorker(info['url'], dest_path)
        self._download_worker.progress_updated.connect(self._on_progress)
        self._download_worker.download_finished.connect(self._on_finished)
        self._download_worker.download_error.connect(self._on_error)
        self._download_worker.start()
    
    def _cancel_download(self):
        """Bricht den Download ab."""
        if self._download_worker:
            self._download_worker.stop()
            self._download_worker.wait(3000)
            self._download_worker = None
        self._reset_dl_ui()
        self.status_label.setVisible(True)
        self.status_label.setText(tr("model_download_cancelled"))
        self.status_label.setStyleSheet("font-size: 11px; color: orange;")
    
    def _on_progress(self, downloaded: float, total: float):
        dl_mb = downloaded / (1024 * 1024)
        if total > 0:
            percent = int(downloaded / total * 100)
            self.progress_bar.setValue(percent)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(f"{dl_mb:.1f} / {total_mb:.1f} MB ({percent}%)")
        else:
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(f"{dl_mb:.1f} MB heruntergeladen...")
    
    def _on_finished(self, path: str):
        self._download_worker = None
        self._reset_dl_ui()
        self.status_label.setVisible(True)
        self.status_label.setText("✅ " + tr("model_download_complete"))
        self.status_label.setStyleSheet("font-size: 11px; color: green;")
        self.model_input.setText(path)
    
    def _on_error(self, error: str):
        self._download_worker = None
        self._reset_dl_ui()
        self.status_label.setVisible(True)
        self.status_label.setText("❌ " + tr("model_download_error", error=error))
        self.status_label.setStyleSheet("font-size: 11px; color: red;")
    
    def _reset_dl_ui(self):
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇️ " + tr("model_download_btn"))
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        filename = self.model_combo.currentData()
        if filename and is_model_downloaded(filename):
            self.download_btn.setVisible(False)
    
    def browse_model(self):
        """Öffnet Datei-Dialog für Modell-Auswahl."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("wizard_model_browse_title"),
            str(Path.home()),
            tr("wizard_model_filter")
        )
        if file_path:
            self.model_input.setText(file_path)
    
    def get_data(self) -> dict:
        """Gibt Modell-Pfad zurück."""
        return {"default_model": self.model_input.text()}
    
    def is_valid(self) -> bool:
        """Prüft ob Modell-Pfad optional valid ist."""
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
        self.token_input.setPlaceholderText(tr("wizard_token_placeholder"))
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout.addWidget(self.token_input)
        
        # Show/Hide Button
        show_btn = QCheckBox(tr("wizard_token_show"))
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
        keychain_info = tr("wizard_token_keychain_info_mac") if is_mac() else tr("wizard_token_keychain_info_other")
        info_label = QLabel(tr("wizard_token_keychain_hint", location=keychain_info))
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
        saved_theme = None
        saved_threads = None
        saved_auto_open = False
        saved_check_updates = True
        
        if history_manager:
            saved_theme = history_manager.get_user_preference("preferred_theme")
            saved_threads = history_manager.get_app_setting("default_threads")
            saved_auto_open = history_manager.get_user_preference("auto_open_transcript", False)
            saved_check_updates = history_manager.get_user_preference("check_model_updates", True)
        
        # Theme
        theme_group = QGroupBox(tr("wizard_theme"))
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([tr("wizard_theme_light"), tr("wizard_theme_dark")])
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
        recommended_label = QLabel(tr("wizard_threads_recommended", threads=get_recommended_threads()))
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
        info_label = QLabel(tr("wizard_tutorial_prompt"))
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
            print("✓ Wizard using provided HistoryManager")
            self.history_manager = history_manager
        else:
            print("✓ Wizard using singleton HistoryManager")
            self.history_manager = HistoryManager.get_instance()
        
        # Stelle sicher, dass History-Datei und Verzeichnis existieren
        self.history_manager.history_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 History file: {self.history_manager.history_file}")
        print(f"📊 Before wizard - first_run: {self.history_manager.is_first_run()}, wizard_completed: {self.history_manager.is_wizard_completed()}")
        
        self.collected_data = {}
        self.wizard_is_first_run = self.history_manager.is_first_run()
        
        # Sobald der Wizard startet, ist es kein erster Start mehr
        if self.wizard_is_first_run:
            print("=== Wizard starting for first time - setting first_run to False ===")
            self.history_manager.save_app_setting("first_run", False)
            print(f"📊 After first_run=False - Status: {self.history_manager.is_first_run()}")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI des Wizards."""
        layout = QVBoxLayout()
        
        # Stacked Widget für Seiten
        self.pages = QStackedWidget()
        
        # Seiten hinzufügen (mit History-Manager für gespeicherte Werte)
        self.welcome_page = WelcomePage(self.history_manager, wizard=self)
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
        
        print(f"=== go_next() - Page {current_index} ===")
        
        # Validierung
        if not current_page.is_valid():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                tr("wizard_invalid_input"),
                tr("wizard_check_inputs")
            )
            return
        
        # Daten sammeln
        page_data = current_page.get_data()
        print(f"Page data: {page_data}")
        self.collected_data.update(page_data)
        
        print(f"Collected data so far: {self.collected_data}")
        
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
        """Aktualisiert die Button-Zustände und Texte."""
        current_index = self.pages.currentIndex()
        
        # Back-Button
        self.back_btn.setEnabled(current_index > 0)
        self.back_btn.setText(tr("back"))
        
        # Next/Finish-Button
        is_last_page = current_index == self.pages.count() - 1
        self.next_btn.setVisible(not is_last_page)
        self.next_btn.setText(tr("next"))
        self.finish_btn.setVisible(is_last_page)
        self.finish_btn.setText(tr("finish"))
    
    def refresh_wizard_ui(self):
        """Aktualisiert alle UI-Texte nach Sprachwechsel."""
        # Window Title
        self.setWindowTitle(tr("wizard_title"))
        
        # Button-Texte
        self.update_buttons()
    
    def on_language_changed(self):
        """Wird von WelcomePage aufgerufen wenn die Sprache geändert wird."""
        # Speichere die Daten der aktuellen Seiten
        saved_data = {}
        
        # ModelPage Daten
        if hasattr(self.model_page, 'model_input'):
            saved_data['model_path'] = self.model_page.model_input.text()
        
        # TokenPage Daten
        if hasattr(self.token_page, 'token_input'):
            saved_data['token'] = self.token_page.token_input.text()
        
        # PreferencesPage Daten
        if hasattr(self.preferences_page, 'theme_combo'):
            saved_data['theme_index'] = self.preferences_page.theme_combo.currentIndex()
        if hasattr(self.preferences_page, 'threads_spin'):
            saved_data['threads'] = self.preferences_page.threads_spin.value()
        if hasattr(self.preferences_page, 'auto_open_check'):
            saved_data['auto_open'] = self.preferences_page.auto_open_check.isChecked()
        if hasattr(self.preferences_page, 'check_updates_check'):
            saved_data['check_updates'] = self.preferences_page.check_updates_check.isChecked()
        
        # Seiten neu erstellen (außer WelcomePage)
        # ModelPage
        model_page_index = self.pages.indexOf(self.model_page)
        self.pages.removeWidget(self.model_page)
        self.model_page.deleteLater()
        self.model_page = ModelPage(self.history_manager)
        if 'model_path' in saved_data:
            self.model_page.model_input.setText(saved_data['model_path'])
        self.pages.insertWidget(model_page_index, self.model_page)
        
        # TokenPage
        token_page_index = self.pages.indexOf(self.token_page)
        self.pages.removeWidget(self.token_page)
        self.token_page.deleteLater()
        self.token_page = TokenPage()
        if 'token' in saved_data:
            self.token_page.token_input.setText(saved_data['token'])
        self.pages.insertWidget(token_page_index, self.token_page)
        
        # PreferencesPage
        prefs_page_index = self.pages.indexOf(self.preferences_page)
        self.pages.removeWidget(self.preferences_page)
        self.preferences_page.deleteLater()
        self.preferences_page = PreferencesPage(self.history_manager)
        if 'theme_index' in saved_data:
            self.preferences_page.theme_combo.setCurrentIndex(saved_data['theme_index'])
        if 'threads' in saved_data:
            self.preferences_page.threads_spin.setValue(saved_data['threads'])
        if 'auto_open' in saved_data:
            self.preferences_page.auto_open_check.setChecked(saved_data['auto_open'])
        if 'check_updates' in saved_data:
            self.preferences_page.check_updates_check.setChecked(saved_data['check_updates'])
        self.pages.insertWidget(prefs_page_index, self.preferences_page)
        
        # CompletePage
        complete_page_index = self.pages.indexOf(self.complete_page)
        self.pages.removeWidget(self.complete_page)
        self.complete_page.deleteLater()
        self.complete_page = CompletePage()
        self.complete_page.tutorial_requested.connect(self.on_tutorial_requested)
        self.pages.insertWidget(complete_page_index, self.complete_page)
        
        # UI aktualisieren
        self.refresh_wizard_ui()
    def on_tutorial_requested(self, start_tutorial: bool):
        """Handler wenn Tutorial requested wird."""
        print(f"=== on_tutorial_requested({start_tutorial}) ===")
        self.complete_page.start_tutorial = start_tutorial
        # Automatisch zum Finish-Button weiterleiten
        print("Calling finish_wizard() in 300ms...")
        QTimer.singleShot(300, self.finish_wizard)
    
    def finish_wizard(self):
        """Schließt den Wizard ab und speichert Settings."""
        from PyQt6.QtWidgets import QMessageBox
        
        print("=== finish_wizard() aufgerufen ===")
        
        # Letzte Seite Daten sammeln
        self.collected_data.update(self.complete_page.get_data())
        
        print(f"Collected data: {self.collected_data}")
        
        # HF-Token in Keychain speichern (nicht in History!)
        hf_token = self.collected_data.get("hf_token", "").strip()
        if hf_token:
            if is_mac():
                success = save_hf_token_to_keychain(hf_token)
                if not success:
                    QMessageBox.warning(
                        self,
                        tr("wizard_token_save_failed_title"),
                        tr("wizard_token_save_failed_text")
                    )
            else:
                QMessageBox.information(
                    self,
                    tr("wizard_keychain_not_available_title"),
                    tr("wizard_keychain_not_available_text")
                )
        
        # Bereite Konfiguration vor (ohne hf_token, start_tutorial und ui_language)
        # ui_language wird separat in user_preferences gespeichert (bereits in WelcomePage erledigt)
        print("\n=== 💾 Saving wizard configuration ===")
        initial_config = {k: v for k, v in self.collected_data.items() 
                         if k not in ('hf_token', 'start_tutorial', 'ui_language')}
        
        # Speichere als initial_config (wird beim ersten Start geladen)
        self.history_manager.save_initial_config(initial_config)
        print(f"  ✓ Initial config saved: {list(initial_config.keys())}")
        
        # Speichere User-Preferences (unabhängig von Sessions)
        # ui_language wurde bereits in WelcomePage gespeichert
        if 'preferred_theme' in initial_config:
            self.history_manager.save_user_preference('preferred_theme', initial_config['preferred_theme'])
        if 'check_model_updates' in initial_config:
            self.history_manager.save_user_preference('check_model_updates', initial_config['check_model_updates'])
        print("  ✓ User preferences saved")
        
        # Wizard als abgeschlossen markieren
        print("\n🎉 Marking wizard as completed...")
        self.history_manager.mark_wizard_completed(version="1.0")
        
        # Explizit nochmal speichern um sicherzustellen dass alles geschrieben wurde
        print("💾 Final save...")
        self.history_manager._save_history()
        
        print(f"\n📊 Final history values:")
        print(f"  - first_run: {self.history_manager.history_data.get('app_settings', {}).get('first_run')}")
        print(f"  - wizard_completed: {self.history_manager.history_data.get('app_settings', {}).get('wizard_completed')}")
        print(f"  - initial_config: {list(initial_config.keys())}")
        print("=== ✅ finish_wizard() completed ===")
        
        # Signal emittieren
        self.wizard_completed.emit(self.collected_data)
        
        # Dialog schließen
        self.accept()
