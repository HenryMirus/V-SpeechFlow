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
from .macos_utils import get_hf_token_from_keychain, is_mac


class DiarizationPanel(QWidget):
    """Panel für Speaker Diarization Einstellungen."""
    
    # Signals
    diarization_changed = pyqtSignal(dict)  # Emitted wenn sich Settings ändern
    
    def __init__(self):
        super().__init__()
        self.is_expanded = False
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
        
        # Titel mit Toggle-Button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 5, 0, 5)
        
        # Toggle-Button
        self.toggle_button = QPushButton("▶")
        self.toggle_button.setFixedWidth(25)
        self.toggle_button.setToolTip("Bereich ein-/ausblenden")
        self.toggle_button.clicked.connect(self.toggle_content)
        title_layout.addWidget(self.toggle_button)
        
        # Titel-Label
        title = QLabel("👥 " + tr("diarization_title"))
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # Content Container
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)  # Standardmäßig eingeklappt
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(10, 5, 0, 5)
        
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
        
        # Keychain Hint (nur auf macOS)
        if is_mac():
            keychain_hint = QLabel(tr("diarization_keychain_hint"))
            keychain_hint.setStyleSheet("color: black; font-size: 9px; background-color: #f5f5f5; padding: 5px; border-radius: 3px;")
            keychain_hint.setWordWrap(True)
            settings_layout.addWidget(keychain_hint)
        
        settings_layout.addStretch()
        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)
        
        layout.addStretch()
        
        # Content-Widget zum Main-Layout hinzufügen
        main_layout.addWidget(self.content_widget)
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
        elif self.validate_token_format(token):
            self.token_status.setText(tr("diarization_token_status_valid"))
            self.token_status.setStyleSheet("color: green; font-size: 10px;")
        else:
            self.token_status.setText("⚠ Ungültiges Token Format (erwartet: hf_xxx)")
            self.token_status.setStyleSheet("color: orange; font-size: 10px;")
        
        self.emit_settings_changed()
    
    def validate_token_format(self, token: str) -> bool:
        """
        Validiert das Format des HuggingFace Tokens.
        
        Returns:
            True wenn Format gültig (beginnt mit hf_ und hat min. 20 Zeichen)
        """
        return token.startswith("hf_") and len(token) >= 20
    
    def toggle_token_visibility(self, show: bool):
        """Zeigt/versteckt den Token."""
        if show:
            self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.hf_token_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_token_from_keychain(self):
        """Lädt HuggingFace Token aus macOS Keychain."""
        token = get_hf_token_from_keychain()
        
        if token:
            self.hf_token_input.setText(token)
            QMessageBox.information(
                self,
                tr("diarization_token_loaded_title"),
                tr("diarization_token_loaded_msg")
            )
        else:
            if is_mac():
                QMessageBox.warning(
                    self,
                    tr("diarization_keychain_unavailable_title"),
                    tr("diarization_keychain_hint")
                )
            else:
                QMessageBox.information(
                    self,
                    tr("diarization_keychain_unavailable_title"),
                    tr("diarization_keychain_unavailable_msg")
                )
    
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
                    return False, (
                        "HuggingFace Token ist erforderlich für Speaker Diarization.\n\n"
                        "Der Token wurde nicht in der macOS Keychain gefunden.\n"
                        "Entweder ist keiner gespeichert oder er wurde falsch gespeichert.\n\n"
                        "Bitte speichern Sie den Token mit:\n"
                        "security add-generic-password -s HF_V-Speechflow -a user -w \"hf_xxx\"\n\n"
                        "Oder geben Sie ihn manuell im Diarization-Panel ein."
                    )
            else:
                return False, (
                    "HuggingFace Token ist erforderlich für Speaker Diarization.\n\n"
                    "Bitte geben Sie den Token im Diarization-Panel ein."
                )
        
        if not self.validate_token_format(token):
            return False, "HuggingFace Token hat ungültiges Format (muss mit 'hf_' beginnen)."
        
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
    
    def toggle_content(self):
        """Toggle zwischen expanded/collapsed."""
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.toggle_button.setText("▼" if self.is_expanded else "▶")
