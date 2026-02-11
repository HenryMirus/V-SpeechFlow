"""
Profile-Controller für V-SpeechFlow

Extrahiert alle Profil-Operationen aus MainWindow:
Speichern, Löschen, Duplizieren, Export/Import, Favoriten.
"""

import logging

from PyQt6.QtWidgets import (
    QComboBox,
    QPushButton,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from pathlib import Path
from datetime import datetime
from .translations import tr

logger = logging.getLogger(__name__)


class ProfileController:
    """
    Verwaltet alle Profil-CRUD-Operationen.

    Args:
        main_window: Referenz auf das MainWindow
    """

    def __init__(self, main_window):
        self.mw = main_window

    @property
    def profile_manager(self):
        return self.mw.profile_manager

    @property
    def profile_combo(self) -> QComboBox:
        return self.mw.profile_combo

    def refresh_profile_list(self):
        """Aktualisiert die Profil-Liste in der ComboBox."""
        current_text = self.profile_combo.currentText()
        self.profile_combo.blockSignals(True)

        # Clear und neu befüllen
        self.profile_combo.clear()
        self.profile_combo.addItem(tr("profile_current_unsaved"))

        # Favoriten laden
        favorites = self.profile_manager.get_favorites()

        # Profile hinzufügen (Default zuerst, dann User-Profile)
        profile_names = self.profile_manager.get_profile_names()
        for name in profile_names:
            is_default = self.profile_manager.is_default_profile(name)
            is_favorite = name in favorites

            if is_default or is_favorite:
                display_name = f"⭐ {name}"
            else:
                display_name = name

            self.profile_combo.addItem(display_name, name)

        # Versuche vorherige Auswahl wiederherzustellen
        index = self.profile_combo.findText(current_text)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        else:
            self.profile_combo.setCurrentIndex(0)

        self.profile_combo.blockSignals(False)
        logger.debug(f"Profile list refreshed: {len(profile_names)} profiles")

    def on_profile_selected(self, text: str):
        """Wird aufgerufen wenn ein Profil ausgewählt wird."""
        if text.startswith("--") or not text:
            return

        # Entferne Stern von Default-Profilen
        profile_name = text.replace("⭐ ", "")

        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            logger.warning(f"Profile not found: {profile_name}")
            return

        # Model laden
        if 'model' in profile:
            self.mw.model_panel.set_settings(profile['model'])

        # Settings laden
        if 'settings' in profile:
            self.mw.settings_panel.set_settings(profile['settings'])

        if 'diarization' in profile:
            self.mw.diarization_panel.set_settings(profile['diarization'])

        if 'output' in profile:
            self.mw.output_panel.set_settings(profile['output'])

        self.mw.statusBar().showMessage(f"📁 Profil geladen: {profile_name}")
        logger.info(f"Profile loaded: {profile_name}")

    def save_current_profile(self):
        """Speichert das aktuelle Profil."""
        name, ok = QInputDialog.getText(
            self.mw,
            tr('main_profile_save_title'),
            tr('main_profile_save_prompt')
        )

        if not ok or not name:
            return

        # Prüfe ob Default-Profil (überschreiben verhindern)
        if self.profile_manager.is_default_profile(name):
            QMessageBox.warning(
                self.mw,
                tr('main_error'),
                tr('main_profile_reserved', name=name)
            )
            return

        # Sammle aktuelle Einstellungen
        profile = {
            "description": tr("profile_custom_desc").format(
                date=datetime.now().strftime('%d.%m.%Y %H:%M')
            ),
            "model": self.mw.model_panel.get_settings(),
            "settings": self.mw.settings_panel.get_settings(),
            "diarization": self.mw.diarization_panel.get_settings(),
            "output": self.mw.output_panel.get_settings(),
        }

        if self.profile_manager.save_profile(name, profile):
            self.refresh_profile_list()
            self.mw.menu_manager.update_profile_menus()

            # Wähle das neue Profil aus
            index = self.profile_combo.findData(name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)

            QMessageBox.information(
                self.mw,
                tr('main_success'),
                tr('main_profile_saved', name=name)
            )
            logger.info(f"Profile saved: {name}")
        else:
            QMessageBox.critical(
                self.mw,
                tr('main_error'),
                tr('main_profile_save_failed', name=name)
            )
            logger.error(f"Failed to save profile: {name}")

    def delete_selected_profile(self):
        """Löscht das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()

        if current_text.startswith("--"):
            QMessageBox.information(self.mw, tr('main_info'), tr('main_no_profile_selected'))
            return

        profile_name = current_text.replace("⭐ ", "")

        if self.profile_manager.is_default_profile(profile_name):
            QMessageBox.warning(
                self.mw,
                tr('main_error'),
                tr('msg_default_profile_no_delete')
            )
            return

        reply = QMessageBox.question(
            self.mw,
            tr('msg_delete_profile_title'),
            tr('msg_delete_profile', name=profile_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self.refresh_profile_list()
                self.mw.menu_manager.update_profile_menus()
                self.profile_combo.setCurrentIndex(0)
                QMessageBox.information(
                    self.mw,
                    tr('msg_profile_deleted_title'),
                    tr('msg_profile_deleted', name=profile_name)
                )
                logger.info(f"Profile deleted: {profile_name}")
            else:
                QMessageBox.critical(
                    self.mw,
                    tr('main_error'),
                    tr('msg_profile_delete_error', name=profile_name)
                )
                logger.error(f"Failed to delete profile: {profile_name}")

    def duplicate_selected_profile(self):
        """Dupliziert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()

        if current_text.startswith("--"):
            QMessageBox.information(self.mw, tr('main_info'), tr('msg_no_profile_selected'))
            return

        source_name = current_text.replace("⭐ ", "")

        new_name, ok = QInputDialog.getText(
            self.mw,
            tr('main_profile_duplicate_title'),
            tr('main_profile_duplicate_prompt', name=source_name),
            text=f"{source_name} (Kopie)"
        )

        if ok and new_name:
            if self.profile_manager.duplicate_profile(source_name, new_name):
                self.refresh_profile_list()
                self.mw.menu_manager.update_profile_menus()
                index = self.profile_combo.findText(
                    new_name, Qt.MatchFlag.MatchContains
                )
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(
                    self.mw,
                    tr('msg_profile_duplicated_title'),
                    tr('msg_profile_duplicated', name=new_name)
                )
                logger.info(f"Profile duplicated: {source_name} -> {new_name}")
            else:
                QMessageBox.critical(
                    self.mw,
                    tr('main_error'),
                    tr('msg_profile_duplicate_error')
                )

    def show_profile_menu(self):
        """Zeigt ein Kontextmenü für Profile-Optionen."""
        menu = QMenu(self.mw)

        current_text = self.profile_combo.currentText()
        if not current_text.startswith("--"):
            profile_name = current_text.replace("⭐ ", "")

            favorites = self.profile_manager.get_favorites()
            if profile_name in favorites:
                unfav_action = QAction("❌ " + tr("menu_unmark_favorite"), self.mw)
                unfav_action.triggered.connect(
                    lambda: self.toggle_favorite(profile_name, False)
                )
                menu.addAction(unfav_action)
            else:
                fav_action = QAction("⭐ " + tr("menu_mark_favorite"), self.mw)
                fav_action.triggered.connect(
                    lambda: self.toggle_favorite(profile_name, True)
                )
                menu.addAction(fav_action)

            menu.addSeparator()

        export_action = QAction("📤 " + tr("menu_profiles_export"), self.mw)
        export_action.triggered.connect(self.export_profile)
        menu.addAction(export_action)

        import_action = QAction("📥 " + tr("menu_profiles_import"), self.mw)
        import_action.triggered.connect(self.import_profile)
        menu.addAction(import_action)

        # Zeige Menü unter dem Sender-Button
        sender = self.mw.sender()
        if sender:
            menu.exec(sender.mapToGlobal(sender.rect().bottomLeft()))
        else:
            menu.exec()

    def toggle_favorite(self, profile_name: str, mark_as_favorite: bool):
        """Markiert/Entmarkiert Profil als Favorit."""
        if mark_as_favorite:
            if self.profile_manager.mark_as_favorite(profile_name):
                logger.info(f"Profile marked as favorite: {profile_name}")
            else:
                QMessageBox.warning(
                    self.mw, tr('main_error'), tr('msg_favorite_mark_error')
                )
        else:
            if self.profile_manager.unmark_as_favorite(profile_name):
                logger.info(f"Profile unmarked as favorite: {profile_name}")
            else:
                QMessageBox.warning(
                    self.mw, tr('main_error'), tr('msg_favorite_unmark_error')
                )

        self.refresh_profile_list()
        self.mw.menu_manager.update_favorites_menu()
        self.mw.menu_manager.update_all_profiles_menu()

    def export_profile(self):
        """Exportiert das aktuell ausgewählte Profil."""
        current_text = self.profile_combo.currentText()

        if current_text.startswith("--"):
            QMessageBox.information(
                self.mw, tr('main_info'), tr('msg_no_profile_to_export')
            )
            return

        profile_name = current_text.replace("⭐ ", "")

        file_path, _ = QFileDialog.getSaveFileName(
            self.mw,
            tr('menu_profiles_export'),
            f"{profile_name}.json",
            tr('main_json_files_filter')
        )

        if file_path:
            if self.profile_manager.export_profile(profile_name, Path(file_path)):
                QMessageBox.information(
                    self.mw,
                    tr('msg_profile_exported_title'),
                    tr('msg_profile_exported', path=file_path)
                )
                logger.info(f"Profile exported: {profile_name} -> {file_path}")
            else:
                QMessageBox.critical(
                    self.mw, tr('main_error'), tr('msg_profile_export_error')
                )

    def import_profile(self):
        """Importiert ein Profil aus einer JSON-Datei."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.mw,
            tr('menu_profiles_import'),
            "",
            tr('main_json_files_filter')
        )

        if file_path:
            success, profile_name = self.profile_manager.import_profile(Path(file_path))

            if success:
                self.refresh_profile_list()
                self.mw.menu_manager.update_profile_menus()
                index = self.profile_combo.findText(
                    profile_name, Qt.MatchFlag.MatchContains
                )
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(
                    self.mw,
                    tr('msg_profile_imported_title'),
                    tr('msg_profile_imported', name=profile_name)
                )
                logger.info(f"Profile imported: {file_path} -> {profile_name}")
            else:
                QMessageBox.critical(
                    self.mw, tr('main_error'), tr('msg_profile_import_error')
                )
