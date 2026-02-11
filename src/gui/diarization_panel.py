"""
Diarization Panel für Speaker Diarization

Ermöglicht Konfiguration von Speaker Diarization mit verschiedenen Modi.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .translations import tr
from .collapsible_section import CollapsibleSection
from .macos_utils import get_hf_token_from_keychain, save_hf_token_to_keychain, is_mac
from .utils import validate_token_format


class DiarizationPanel(QWidget):
    """Panel für Speaker Diarization Einstellungen."""
    
    # Signals
    diarization_changed = pyqtSignal(dict)  # Emitted wenn sich Settings ändern
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Auto-Load Token aus Keychain beim Start
        self.auto_load_token_from_keychain()
    
    def auto_load_token_from_keychain(self):
        """Versucht automatisch den Token aus der Keychain zu laden beim Start."""
        if is_mac():
            token = get_hf_token_from_keychain()
            if token:
                self.hf_token_input.setText(token)
                # Stille Ladung - keine Meldung beim Auto-Load
    
    def init_ui(self):
        """Initialisiert die UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Collapsible Section
        self.section = CollapsibleSection("👥 " + tr("diarization_title"))
        layout = self.section.content_layout
        
        # Aktivierungs-Checkbox
        self.enable_checkbox = QCheckBox(tr("diarization_enable"))
        self.enable_checkbox.setChecked(False)
        self.enable_checkbox.stateChanged.connect(self.on_enable_changed)
        self.enable_checkbox.setToolTip(tr("tooltip_diarization"))
        layout.addWidget(self.enable_checkbox)
        
        info = QLabel("💡 " + tr("diarization_info"))
        info.setStyleSheet("color: gray; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # === Diarization Settings Group (nur aktiv wenn enabled) ===
        self.settings_group = QGroupBox(tr("diarization_settings"))
        self.settings_group.setEnabled(False)
        self.settings_group.setVisible(False)  # Standardmäßig eingeklappt
        settings_layout = QVBoxLayout()
        
        # === Modus-Auswahl ===
        mode_label = QLabel(tr("diarization_mode"))
        mode_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(mode_label)
        
        # Radio Buttons für Modus
        self.mode_group = QButtonGroup(self)
        
        self.exact_radio = QRadioButton(tr("diarization_mode_exact"))
        self.exact_radio.setChecked(True)
        self.exact_radio.toggled.connect(self.on_mode_changed)
        self.exact_radio.setToolTip(tr("diarization_mode_exact_tooltip"))
        self.mode_group.addButton(self.exact_radio, 1)
        settings_layout.addWidget(self.exact_radio)
        
        # Exakte Anzahl Input
        exact_layout = QHBoxLayout()
        exact_layout.addSpacing(30)
        exact_layout.addWidget(QLabel(tr("diarization_num_speakers")))
        
        self.num_speakers_spinbox = QSpinBox()
        self.num_speakers_spinbox.setMinimum(2)
        self.num_speakers_spinbox.setMaximum(50)
        self.num_speakers_spinbox.setValue(2)
        self.num_speakers_spinbox.valueChanged.connect(self.emit_settings_changed)
        self.num_speakers_spinbox.setToolTip(tr("diarization_num_speakers_tooltip"))
        exact_layout.addWidget(self.num_speakers_spinbox)
        exact_layout.addStretch()
        
        settings_layout.addLayout(exact_layout)
        
        settings_layout.addSpacing(10)
        
        self.auto_radio = QRadioButton(tr("diarization_mode_auto"))
        self.auto_radio.toggled.connect(self.on_mode_changed)
        self.auto_radio.setToolTip(tr("diarization_mode_auto_tooltip"))
        self.mode_group.addButton(self.auto_radio, 2)
        settings_layout.addWidget(self.auto_radio)
        
        # Min/Max Input
        minmax_layout = QHBoxLayout()
        minmax_layout.addSpacing(30)
        
        minmax_layout.addWidget(QLabel(tr("diarization_min")))
        self.min_speakers_spinbox = QSpinBox()
        self.min_speakers_spinbox.setMinimum(1)
        self.min_speakers_spinbox.setMaximum(50)
        self.min_speakers_spinbox.setValue(1)
        self.min_speakers_spinbox.setEnabled(False)
        self.min_speakers_spinbox.valueChanged.connect(self.on_min_changed)
        self.min_speakers_spinbox.setToolTip(tr("diarization_min_tooltip"))
        minmax_layout.addWidget(self.min_speakers_spinbox)
        
        minmax_layout.addWidget(QLabel(tr("diarization_max")))
        self.max_speakers_spinbox = QSpinBox()
        self.max_speakers_spinbox.setMinimum(1)
        self.max_speakers_spinbox.setMaximum(50)
        self.max_speakers_spinbox.setValue(5)
        self.max_speakers_spinbox.setEnabled(False)
        self.max_speakers_spinbox.valueChanged.connect(self.on_max_changed)
        self.max_speakers_spinbox.setToolTip(tr("diarization_max_tooltip"))
        minmax_layout.addWidget(self.max_speakers_spinbox)
        
        minmax_layout.addStretch()
        settings_layout.addLayout(minmax_layout)
        
        hint_minmax = QLabel("💡 " + tr("diarization_auto_hint"))
        hint_minmax.setStyleSheet("color: gray; font-size: 10px; margin-left: 30px;")
        hint_minmax.setWordWrap(True)
        settings_layout.addWidget(hint_minmax)
        
        settings_layout.addSpacing(10)
        
        # === HuggingFace Token ===
        token_label = QLabel(tr("diarization_token_label"))
        token_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(token_label)
        
        token_hint = QLabel(tr("diarization_token_hint"))
        token_hint.setStyleSheet("color: #f57c00; font-size: 10px;")
        token_hint.setWordWrap(True)
        settings_layout.addWidget(token_hint)
        
        token_layout = QHBoxLayout()
        self.hf_token_input = QLineEdit()
        self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token_input.setPlaceholderText(tr("diarization_token_placeholder"))
        self.hf_token_input.textChanged.connect(self.on_token_changed)
        self.hf_token_input.setToolTip(tr("tooltip_hf_token"))
        token_layout.addWidget(self.hf_token_input)
        
        btn_show_token = QPushButton("👁️")
        btn_show_token.setFixedWidth(40)
        btn_show_token.setCheckable(True)
        btn_show_token.toggled.connect(self.toggle_token_visibility)
        btn_show_token.setToolTip(tr("diarization_token_show_tooltip"))
        token_layout.addWidget(btn_show_token)
        
        btn_load_keychain = QPushButton("🔑 " + tr("diarization_btn_keychain"))
        btn_load_keychain.clicked.connect(self.load_token_from_keychain)
        btn_load_keychain.setToolTip(tr("diarization_keychain_tooltip"))
        token_layout.addWidget(btn_load_keychain)
        
        settings_layout.addLayout(token_layout)
        
        # Token Status
        self.token_status = QLabel(tr("diarization_token_status_empty"))
        self.token_status.setStyleSheet("color: gray; font-size: 10px;")
        settings_layout.addWidget(self.token_status)
        
        # Keychain speichern Checkbox (nur auf macOS)
        if is_mac():
            self.save_to_keychain_checkbox = QCheckBox(tr("diarization_keychain_save_checkbox"))
            self.save_to_keychain_checkbox.setChecked(False)
            self.save_to_keychain_checkbox.toggled.connect(self.on_save_to_keychain_toggled)
            self.save_to_keychain_checkbox.setToolTip(tr("diarization_keychain_save_tooltip"))
            settings_layout.addWidget(self.save_to_keychain_checkbox)
        
        settings_layout.addStretch()
        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)
        
        layout.addStretch()
        
        # Collapsible Section zum Main-Layout hinzufügen
        main_layout.addWidget(self.section)
        self.setLayout(main_layout)
    
    def on_enable_changed(self, state: int):
        """Wird aufgerufen wenn Diarization aktiviert/deaktiviert wird."""
        enabled = state == Qt.CheckState.Checked.value
        self.settings_group.setEnabled(enabled)
        self.settings_group.setVisible(enabled)  # Aufklappen wenn aktiviert
        self.emit_settings_changed()
    
    def on_mode_changed(self):
        """Wird aufgerufen wenn sich der Modus ändert."""
        is_exact = self.exact_radio.isChecked()
        
        # Exact mode: num_speakers aktiv, min/max deaktiviert
        self.num_speakers_spinbox.setEnabled(is_exact)
        self.min_speakers_spinbox.setEnabled(not is_exact)
        self.max_speakers_spinbox.setEnabled(not is_exact)
        
        self.emit_settings_changed()
    
    def on_min_changed(self, value: int):
        """Stellt sicher dass Min <= Max."""
        if value > self.max_speakers_spinbox.value():
            self.max_speakers_spinbox.setValue(value)
        self.emit_settings_changed()
    
    def on_max_changed(self, value: int):
        """Stellt sicher dass Max >= Min."""
        if value < self.min_speakers_spinbox.value():
            self.min_speakers_spinbox.setValue(value)
        self.emit_settings_changed()
    
    def on_token_changed(self):
        """Wird aufgerufen wenn sich der Token ändert."""
        token = self.hf_token_input.text().strip()
        
        if not token:
            self.token_status.setText(tr("diarization_token_status_empty"))
            self.token_status.setStyleSheet("color: gray; font-size: 10px;")
        elif validate_token_format(token):
            self.token_status.setText(tr("diarization_token_status_valid"))
            self.token_status.setStyleSheet("color: green; font-size: 10px;")
        else:
            self.token_status.setText(tr("diarization_token_invalid_format"))
            self.token_status.setStyleSheet("color: orange; font-size: 10px;")
        
        self.emit_settings_changed()
    
    def toggle_token_visibility(self, show: bool):
        """Zeigt/versteckt den Token."""
        if show:
            self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_token_from_keychain(self):
        """Lädt HuggingFace Token aus macOS Keychain oder bietet Eingabe-Dialog an."""
        if not is_mac():
            QMessageBox.information(
                self,
                tr("diarization_keychain_unavailable_title"),
                tr("diarization_keychain_unavailable_msg")
            )
            return

        token = get_hf_token_from_keychain()

        if token:
            self.hf_token_input.setText(token)
            QMessageBox.information(
                self,
                tr("diarization_token_loaded_title"),
                tr("diarization_token_loaded_msg")
            )
        else:
            self._show_token_input_dialog()

    def _show_token_input_dialog(self):
        """Zeigt einen Dialog zum Eingeben eines HF-Tokens, der in der Keychain gespeichert wird."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("diarization_keychain_no_token_title"))
        dialog.setMinimumWidth(420)

        dlg_layout = QVBoxLayout(dialog)

        info_label = QLabel(tr("diarization_keychain_no_token_msg"))
        info_label.setWordWrap(True)
        dlg_layout.addWidget(info_label)

        token_input = QLineEdit()
        token_input.setPlaceholderText(tr("diarization_token_placeholder"))
        token_input.setEchoMode(QLineEdit.EchoMode.Password)
        dlg_layout.addWidget(token_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dlg_layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_token = token_input.text().strip()
            if not new_token:
                return

            self.hf_token_input.setText(new_token)

            success = save_hf_token_to_keychain(new_token)
            if success:
                QMessageBox.information(
                    self,
                    tr("diarization_token_saved_title"),
                    tr("diarization_token_saved_msg")
                )
            else:
                QMessageBox.warning(
                    self,
                    tr("diarization_keychain_save_error_title"),
                    tr("diarization_keychain_save_error_msg")
                )

    def on_save_to_keychain_toggled(self, checked: bool):
        """Speichert den aktuellen Token in der Keychain wenn die Checkbox aktiviert wird."""
        if not checked:
            return

        token = self.hf_token_input.text().strip()
        if not token:
            QMessageBox.warning(
                self,
                tr("diarization_keychain_save_error_title"),
                tr("diarization_keychain_no_token_to_save")
            )
            self.save_to_keychain_checkbox.setChecked(False)
            return

        success = save_hf_token_to_keychain(token)
        if success:
            QMessageBox.information(
                self,
                tr("diarization_token_saved_title"),
                tr("diarization_token_saved_msg")
            )
        else:
            QMessageBox.warning(
                self,
                tr("diarization_keychain_save_error_title"),
                tr("diarization_keychain_save_error_msg")
            )
            self.save_to_keychain_checkbox.setChecked(False)
    
    def emit_settings_changed(self):
        """Emittiert Signal mit aktuellen Diarization-Settings."""
        settings = self.get_settings()
        self.diarization_changed.emit(settings)
    
    def get_settings(self) -> dict:
        """
        Gibt alle aktuellen Diarization-Einstellungen zurück.
        
        Returns:
            Dict mit allen Einstellungen
        """
        enabled = self.enable_checkbox.isChecked()
        
        if not enabled:
            return {
                'enabled': False,
                'mode': None,
                'num_speakers': None,
                'min_speakers': None,
                'max_speakers': None,
                'hf_token': None,
            }
        
        is_exact_mode = self.exact_radio.isChecked()
        
        return {
            'enabled': True,
            'mode': 'exact' if is_exact_mode else 'auto',
            'num_speakers': self.num_speakers_spinbox.value() if is_exact_mode else None,
            'min_speakers': self.min_speakers_spinbox.value() if not is_exact_mode else None,
            'max_speakers': self.max_speakers_spinbox.value() if not is_exact_mode else None,
            'hf_token': self.hf_token_input.text().strip() or None,
        }
    
    def validate_settings(self) -> tuple[bool, Optional[str]]:
        """
        Validiert die Diarization-Einstellungen.
        
        Returns:
            Tuple (is_valid, error_message)
        """
        settings = self.get_settings()
        
        if not settings['enabled']:
            return True, None  # Wenn deaktiviert, keine Validierung nötig
        
        # Token prüfen  
        token = settings['hf_token']
        if not token:
            # Versuche automatisch aus Keychain zu laden
            if is_mac():
                keychain_token = get_hf_token_from_keychain()
                if keychain_token:
                    # Auto-Load erfolgreich
                    self.hf_token_input.setText(keychain_token)
                    token = keychain_token
                else:
                    # Kein Token in Keychain
                    return False, tr("diarization_token_required_mac")
            else:
                return False, tr("diarization_token_required")
        
        if not validate_token_format(token):
            return False, tr("diarization_token_invalid")
        
        # Sprecher-Anzahl prüfen
        if settings['mode'] == 'exact':
            if settings['num_speakers'] < 2:
                return False, "Mindestens 2 Sprecher erforderlich."
        else:  # auto mode
            if settings['min_speakers'] < 1:
                return False, "Minimale Sprecheranzahl muss mindestens 1 sein."
            if settings['max_speakers'] < settings['min_speakers']:
                return False, "Maximale Sprecheranzahl muss größer oder gleich minimaler Anzahl sein."
        
        return True, None
    
    def set_settings(self, settings: dict):
        """
        Setzt Diarization-Einstellungen (z.B. aus gespeicherten Profilen).
        
        Args:
            settings: Dict mit Einstellungen
        """
        if 'enabled' in settings:
            self.enable_checkbox.setChecked(settings['enabled'])
        
        if 'mode' in settings and settings['mode']:
            if settings['mode'] == 'exact':
                self.exact_radio.setChecked(True)
            else:
                self.auto_radio.setChecked(True)
        
        if 'num_speakers' in settings and settings['num_speakers']:
            self.num_speakers_spinbox.setValue(settings['num_speakers'])
        
        if 'min_speakers' in settings and settings['min_speakers']:
            self.min_speakers_spinbox.setValue(settings['min_speakers'])
        
        if 'max_speakers' in settings and settings['max_speakers']:
            self.max_speakers_spinbox.setValue(settings['max_speakers'])
        
        if 'hf_token' in settings and settings['hf_token']:
            self.hf_token_input.setText(settings['hf_token'])
    
    def set_hf_token(self, token: str):
        """
        Setzt den HuggingFace Token im Token-Eingabefeld.
        
        Args:
            token: Der HuggingFace Token
        """
        self.hf_token_input.setText(token)

    def refresh_translations(self):
        """Aktualisiert alle übersetzbaren Texte nach einem Sprachwechsel."""
        from .translations import tr

        self.section.set_title(tr("diarization_title"), icon="👥")
        self.enable_checkbox.setText(tr("diarization_enable"))
        self.enable_checkbox.setToolTip(tr("tooltip_diarization"))
        self.settings_group.setTitle(tr("diarization_settings"))
        self.exact_radio.setText(tr("diarization_mode_exact"))
        self.exact_radio.setToolTip(tr("diarization_mode_exact_tooltip"))
        self.auto_radio.setText(tr("diarization_mode_auto"))
        self.auto_radio.setToolTip(tr("diarization_mode_auto_tooltip"))
        self.num_speakers_spinbox.setToolTip(tr("diarization_num_speakers_tooltip"))
        self.min_speakers_spinbox.setToolTip(tr("diarization_min_tooltip"))
        self.max_speakers_spinbox.setToolTip(tr("diarization_max_tooltip"))
        self.hf_token_input.setPlaceholderText(tr("diarization_token_placeholder"))
        self.hf_token_input.setToolTip(tr("tooltip_hf_token"))
    
