"""
Menu-Manager für V-SpeechFlow

Extrahiert die gesamte Menüleisten-Logik aus MainWindow.
Erstellt und verwaltet die Menübar, Recent-Menüs, Sprach-Dropdown,
Theme-Toggle und Hilfe-Dialoge.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QComboBox,
    QMessageBox,
    QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QAction
from pathlib import Path
from .translations import tr, get_translation_manager
from .theme_toggle_switch import ThemeToggleSwitch


class MenuManager:
    """
    Verwaltet die komplette Menüleiste des Hauptfensters.

    Args:
        main_window: Referenz auf das MainWindow
    """

    def __init__(self, main_window):
        self.mw = main_window
        self.file_menu = None
        self.recent_files_menu = None
        self.recent_models_menu = None
        self.profile_menu = None
        self.favorites_menu = None
        self.all_profiles_menu = None
        self.help_menu = None
        self.language_combo = None
        self.theme_toggle_switch = None

    def create_menu_bar(self):
        """Erstellt die Menu-Bar mit History und anderen Optionen."""
        menubar = self.mw.menuBar()

        # Menüleiste explizit sichtbar machen
        menubar.setVisible(True)

        # Auf macOS: Menüleiste im Fenster anzeigen statt in System-Menüleiste
        menubar.setNativeMenuBar(False)

        # Theme-Toggle-Switch (wird am Ende der Menubar hinzugefügt)
        self.theme_toggle_switch = ThemeToggleSwitch()
        self.theme_toggle_switch.clicked = self.toggle_theme
        self.update_theme_switch()

        # Datei-Menü
        self.file_menu = menubar.addMenu("📁 " + tr("menu_file"))

        # Recent Files Submenu
        self.recent_files_menu = QMenu("🕒 " + tr("menu_recent_files"), self.mw)
        self.file_menu.addMenu(self.recent_files_menu)
        self.update_recent_files_menu()

        self.file_menu.addSeparator()

        # Recent Models Submenu
        self.recent_models_menu = QMenu("🤖 " + tr("menu_recent_models"), self.mw)
        self.file_menu.addMenu(self.recent_models_menu)
        self.update_recent_models_menu()

        self.file_menu.addSeparator()

        # Batch-Processing
        batch_action = QAction("📦 " + tr("menu_batch"), self.mw)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self.open_batch_window)
        self.file_menu.addAction(batch_action)

        self.file_menu.addSeparator()

        # History löschen
        clear_history_action = QAction("🗑️ " + tr("menu_clear_history"), self.mw)
        clear_history_action.triggered.connect(self.clear_history)
        self.file_menu.addAction(clear_history_action)

        self.file_menu.addSeparator()

        # Beenden
        quit_action = QAction("❌ " + tr("menu_quit"), self.mw)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.mw.close)
        self.file_menu.addAction(quit_action)

        # Profile-Menü
        self.profile_menu = menubar.addMenu("📋 " + tr("menu_profiles_title"))

        # Favoriten & Standard-Profile Submenu
        self.favorites_menu = QMenu("⭐ " + tr("menu_profiles_favorites"), self.mw)
        self.profile_menu.addMenu(self.favorites_menu)
        self.update_favorites_menu()

        # Alle anderen Profile Submenu
        self.all_profiles_menu = QMenu("📋 " + tr("menu_profiles_all"), self.mw)
        self.profile_menu.addMenu(self.all_profiles_menu)
        self.update_all_profiles_menu()

        self.profile_menu.addSeparator()

        # Export Profil
        export_profile_action = QAction("📤 " + tr("menu_profiles_export"), self.mw)
        export_profile_action.triggered.connect(
            lambda: self.mw.profile_controller.export_profile()
        )
        self.profile_menu.addAction(export_profile_action)

        # Import Profil
        import_profile_action = QAction("📥 " + tr("menu_profiles_import"), self.mw)
        import_profile_action.triggered.connect(
            lambda: self.mw.profile_controller.import_profile()
        )
        self.profile_menu.addAction(import_profile_action)

        # Sprach-Dropdown (wird als Corner Widget hinzugefügt)
        self.language_combo = QComboBox()
        self.language_combo.addItem("🇩🇪", "de")  # userData = language code
        self.language_combo.addItem("🇺🇸", "en")
        self.language_combo.setToolTip(tr("menu_language"))
        self.language_combo.setFixedWidth(70)
        self.language_combo.setFixedHeight(32)
        self.language_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.language_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(150, 150, 150, 0.3);
                border-radius: 6px;
                padding: 4px 10px;
                background: rgba(255, 255, 255, 0.05);
                font-size: 20px;
                color: inherit;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(150, 150, 150, 0.5);
            }
            QComboBox:focus {
                border: 1px solid rgba(100, 150, 255, 0.6);
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
                padding-right: 4px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid rgba(150, 150, 150, 0.3);
                border-radius: 6px;
                padding: 4px;
                background-color: rgba(255, 255, 255, 0.95);
                selection-background-color: rgba(100, 150, 255, 0.2);
                selection-color: inherit;
                font-size: 18px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(100, 150, 255, 0.15);
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(100, 150, 255, 0.25);
            }
        """)

        # Aktuelle Sprache auswählen
        current_language = get_translation_manager().get_current_language()
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        # Signal verbinden
        self.language_combo.currentIndexChanged.connect(self.on_language_combo_changed)

        # Hilfe-Menü
        self.help_menu = menubar.addMenu("❓ " + tr("menu_help"))

        # Tutorial/Onboarding
        tutorial_action = QAction("🎓 " + tr("menu_start_onboarding"), self.mw)
        tutorial_action.triggered.connect(self.mw.start_onboarding)
        self.help_menu.addAction(tutorial_action)

        self.help_menu.addSeparator()

        shortcuts_action = QAction("⌨️ " + tr("menu_shortcuts"), self.mw)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        self.help_menu.addAction(shortcuts_action)

        self.help_menu.addSeparator()

        about_action = QAction("ℹ️ " + tr("menu_about"), self.mw)
        about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(about_action)

        # Corner Widget mit Sprach-Dropdown und Theme-Toggle-Switch
        corner_container = QWidget()
        corner_container.setContentsMargins(0, 0, 15, 0)
        corner_container.setStyleSheet("background: transparent;")
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(12)
        corner_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        corner_layout.addWidget(self.language_combo)
        corner_layout.addWidget(self.theme_toggle_switch)
        menubar.setCornerWidget(corner_container, Qt.Corner.TopRightCorner)

        self.mw.log_info("Menu-Bar erstellt")

    # ===== Recent-Menü Helfer =====

    def _update_recent_menu(self, menu, items, empty_text: str, format_func, callback):
        """
        Generische Methode zum Aktualisieren eines Recent-Menüs.

        Args:
            menu: Das QMenu-Objekt
            items: Liste der Einträge
            empty_text: Text wenn keine Einträge vorhanden
            format_func: Funktion (entry) -> (display_text, tooltip)
            callback: Funktion (path) -> None
        """
        menu.clear()

        if not items:
            no_items_action = QAction(empty_text, self.mw)
            no_items_action.setEnabled(False)
            menu.addAction(no_items_action)
            return

        for entry in items:
            display_text, tooltip = format_func(entry)
            action = QAction(display_text, self.mw)
            action.setToolTip(tooltip)
            path = entry["path"]
            action.triggered.connect(lambda checked, p=path: callback(p))
            menu.addAction(action)

    def update_recent_files_menu(self):
        """Aktualisiert das Recent Files Menü."""
        recent_files = self.mw.history_manager.get_recent_input_files(limit=10)
        self._update_recent_menu(
            self.recent_files_menu,
            recent_files,
            tr("menu_no_recent_files"),
            lambda e: (f"{e['name']} ({e.get('size_mb', 0):.1f} MB)", e["path"]),
            self.load_recent_file,
        )

    def update_recent_models_menu(self):
        """Aktualisiert das Recent Models Menü."""
        recent_models = self.mw.history_manager.get_recent_models(limit=5)
        self._update_recent_menu(
            self.recent_models_menu,
            recent_models,
            tr("menu_no_recent_models"),
            lambda e: (f"{e['name']} ({e.get('size_mb', 0):.0f} MB)", e["path"]),
            self.load_recent_model,
        )

    def load_recent_file(self, file_path: str):
        """Lädt eine zuletzt verwendete Datei."""
        if Path(file_path).exists():
            self.mw.input_panel.set_file_path(file_path)
            self.mw.log_info(f"File loaded from history: {file_path}")
        else:
            QMessageBox.warning(
                self.mw,
                tr('main_file_not_found_title'),
                f"{tr('main_file_not_exist')}\n{file_path}"
            )
            self.mw.history_manager.remove_input_file(file_path)
            self.update_recent_files_menu()

    def load_recent_model(self, model_path: str):
        """Lädt ein zuletzt verwendetes Modell."""
        if Path(model_path).exists():
            self.mw.model_panel.set_model_path(model_path)
            self.mw.log_info(f"Model loaded from history: {model_path}")
        else:
            QMessageBox.warning(
                self.mw,
                tr('main_model_not_found_title'),
                f"{tr('main_model_not_exist')}\n{model_path}"
            )
            self.mw.history_manager.remove_model(model_path)
            self.update_recent_models_menu()

    def clear_history(self):
        """Löscht die komplette History."""
        reply = QMessageBox.question(
            self.mw,
            tr('main_clear_history_title'),
            tr('main_clear_history_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.mw.history_manager.clear_history()
            self.update_recent_files_menu()
            self.update_recent_models_menu()
            self.mw.log_info("History cleared")
            QMessageBox.information(self.mw, tr('main_done'), tr('main_history_cleared'))

    # ===== Theme =====

    def toggle_theme(self):
        """Wechselt zwischen Light und Dark Mode."""
        current = self.mw.theme_manager.get_current_theme()
        new_theme = 'dark' if current == 'light' else 'light'

        self.mw.apply_theme(new_theme)
        self.mw.theme_manager.save_theme_preference(new_theme)

        # Update Theme-Switch
        self.update_theme_switch()

        self.mw.log_info(f"Theme changed to: {new_theme}")

    def update_theme_switch(self):
        """Aktualisiert den Theme-Toggle-Switch basierend auf dem aktuellen Theme."""
        current_theme = self.mw.theme_manager.get_current_theme()
        is_dark = (current_theme == 'dark')
        self.theme_toggle_switch.set_dark_mode(is_dark, animate=True)

        if is_dark:
            self.theme_toggle_switch.setToolTip(tr("theme_switch_to_light"))
        else:
            self.theme_toggle_switch.setToolTip(tr("theme_switch_to_dark"))

    # ===== Batch =====

    def open_batch_window(self):
        """Aktiviert den Batch-Tab im Input-Panel."""
        # Wechsle zum Batch-Tab (Index 2: Live=0, File=1, Batch=2)
        self.mw.input_panel.tabs.setCurrentIndex(2)
        self.mw.log_info("Batch-Tab aktiviert")
        self.mw.statusBar().showMessage("📦 Batch-Modus aktiviert", 2000)

    # ===== Sprache =====

    def on_language_combo_changed(self, index: int):
        """Wird aufgerufen wenn die Sprache im Dropdown geändert wird."""
        language = self.language_combo.itemData(index)
        if language:
            self.mw.change_language(language)

    def update_language_combo(self):
        """Aktualisiert die Auswahl im Sprach-Dropdown."""
        current_language = get_translation_manager().get_current_language()
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

    # ===== Profile-Menüs =====

    def update_profile_menus(self):
        """Aktualisiert alle Profil-Menüs (Favoriten+Standard und Alle)."""
        self.update_favorites_menu()
        self.update_all_profiles_menu()

    def update_favorites_menu(self):
        """Aktualisiert das Favoriten & Standard-Profile Menü."""
        self.favorites_menu.clear()

        favorites = self.mw.profile_manager.get_favorites()
        all_profiles = self.mw.profile_manager.get_profile_names()
        standard_profiles = [
            name for name in all_profiles
            if self.mw.profile_manager.is_default_profile(name)
        ]

        # Kombiniere Favoriten und Standard (ohne Duplikate)
        combined = list(favorites)
        for std_name in standard_profiles:
            if std_name not in combined:
                combined.append(std_name)

        if not combined:
            no_items_action = QAction(tr("menu_no_favorites"), self.mw)
            no_items_action.setEnabled(False)
            self.favorites_menu.addAction(no_items_action)
            return

        # Favoriten zuerst
        if favorites:
            for fav_name in favorites:
                is_standard = self.mw.profile_manager.is_default_profile(fav_name)
                icon = "⭐🔧" if is_standard else "⭐"
                action = QAction(f"{icon} {fav_name}", self.mw)
                action.triggered.connect(
                    lambda checked, name=fav_name: self.load_profile_by_name(name)
                )
                self.favorites_menu.addAction(action)

        # Separator wenn sowohl Favoriten als auch Standard-Profile existieren
        non_favorited_standards = [
            name for name in standard_profiles if name not in favorites
        ]
        if favorites and non_favorited_standards:
            self.favorites_menu.addSeparator()

        # Standard-Profile (die nicht favorisiert sind)
        for std_name in non_favorited_standards:
            action = QAction(f"🔧 {std_name}", self.mw)
            action.triggered.connect(
                lambda checked, name=std_name: self.load_profile_by_name(name)
            )
            self.favorites_menu.addAction(action)

    def update_all_profiles_menu(self):
        """Aktualisiert das Alle-Profile Menü (ohne Favoriten und Standard)."""
        self.all_profiles_menu.clear()

        all_profiles = self.mw.profile_manager.get_profile_names()
        favorites = self.mw.profile_manager.get_favorites()

        other_profiles = [
            name for name in all_profiles
            if name not in favorites
            and not self.mw.profile_manager.is_default_profile(name)
        ]

        if not other_profiles:
            no_profiles_action = QAction(tr("menu_no_other_profiles"), self.mw)
            no_profiles_action.setEnabled(False)
            self.all_profiles_menu.addAction(no_profiles_action)
            return

        for profile_name in sorted(other_profiles):
            action = QAction(f"📄 {profile_name}", self.mw)
            action.triggered.connect(
                lambda checked, name=profile_name: self.load_profile_by_name(name)
            )
            self.all_profiles_menu.addAction(action)

    def load_profile_by_name(self, profile_name: str):
        """Lädt ein Profil anhand des Namens."""
        index = self.mw.profile_combo.findText(
            profile_name, Qt.MatchFlag.MatchContains
        )
        if index >= 0:
            self.mw.profile_combo.setCurrentIndex(index)

    # ===== Hilfe-Dialoge =====

    def show_about(self):
        """Zeigt About-Dialog."""
        QMessageBox.about(
            self.mw,
            tr("about_title"),
            "<h2>V-SpeechFlow</h2>"
            "<p><b>Version:</b> 1.0.0</p>"
            f"<p><b>{tr('about_subtitle')}</b></p>"
            f"<p>{tr('about_powered_by')}</p>"
            "<p>© 2026 V-SpeechFlow Team</p>"
        )

    def show_shortcuts(self):
        """Zeigt Dialog mit allen Tastenkürzel und deren Funktionen."""
        shortcuts_text = f"""
        <h2>{tr("shortcuts_title")}</h2>
        <table border="1" cellpadding="8" cellspacing="0" width="100%">
            <tr style="background-color: rgba(100, 150, 255, 0.2);">
                <th align="left"><b>Tastenkombination</b></th>
                <th align="left"><b>Funktion</b></th>
            </tr>
            <tr>
                <td><code>Ctrl+Return</code></td>
                <td>{tr("shortcuts_start_transcription")}</td>
            </tr>
            <tr>
                <td><code>Escape</code></td>
                <td>{tr("shortcuts_stop_transcription")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+S</code></td>
                <td>{tr("shortcuts_save_profile")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+L</code></td>
                <td>{tr("shortcuts_clear_output")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+B</code></td>
                <td>{tr("shortcuts_batch_processing")}</td>
            </tr>
            <tr>
                <td><code>Ctrl+Q</code></td>
                <td>{tr("shortcuts_quit")}</td>
            </tr>
        </table>
        """

        msg = QMessageBox(self.mw)
        msg.setWindowTitle(f"⌨️ {tr('shortcuts_title')}")
        msg.setText(shortcuts_text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgba(240, 240, 240, 0.95);
            }
            QMessageBox QLabel {
                color: inherit;
            }
            QMessageBox QMessageBox {
                min-width: 400px;
            }
        """)
        msg.exec()

    # ===== Übersetzungen aktualisieren =====

    def refresh_translations(self):
        """Aktualisiert alle Menü-Texte nach einem Sprachwechsel."""
        # File-Menü
        self.file_menu.setTitle("📁 " + tr("menu_file"))
        self.recent_files_menu.setTitle("🕒 " + tr("menu_recent_files"))
        self.recent_models_menu.setTitle("🤖 " + tr("menu_recent_models"))

        for action in self.file_menu.actions():
            text = action.text()
            if '📦' in text:
                action.setText("📦 " + tr("menu_batch"))
            elif '🗑️' in text and ('History' in text or 'Verlauf' in text):
                action.setText("🗑️ " + tr("menu_clear_history"))
            elif '❌' in text:
                action.setText("❌ " + tr("menu_quit"))

        # Profile-Menü
        self.profile_menu.setTitle("📋 " + tr("menu_profiles_title"))
        self.favorites_menu.setTitle("⭐ " + tr("menu_profiles_favorites"))
        self.all_profiles_menu.setTitle("📋 " + tr("menu_profiles_all"))

        for action in self.profile_menu.actions():
            text = action.text()
            if '📤' in text:
                action.setText("📤 " + tr("menu_profiles_export"))
            elif '📥' in text:
                action.setText("📥 " + tr("menu_profiles_import"))

        # Help-Menü
        self.help_menu.setTitle("❓ " + tr("menu_help"))

        for action in self.help_menu.actions():
            text = action.text()
            if '🎓' in text:
                action.setText("🎓 " + tr("menu_start_onboarding"))
            elif '⌨️' in text:
                action.setText("⌨️ " + tr("menu_shortcuts"))
            elif 'ℹ️' in text:
                action.setText("ℹ️ " + tr("menu_about"))

        # Theme-Switch Tooltip
        self.update_theme_switch()

        # Sprach-Dropdown Tooltip
        self.language_combo.setToolTip(tr("menu_language"))

        # Menü-Inhalte aktualisieren
        self.update_recent_files_menu()
        self.update_recent_models_menu()
        self.update_favorites_menu()
        self.update_all_profiles_menu()
