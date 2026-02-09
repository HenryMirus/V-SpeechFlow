"""
Onboarding-System für V-SpeechFlow

Führt neue Benutzer durch die wichtigsten Funktionen der App.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from .translations import tr
from .history import HistoryManager


class OnboardingOverlay(QWidget):
    """
    Overlay-Widget das UI-Elemente hervorhebt und Erklärungen zeigt.
    """
    
    def __init__(self, parent=None):
        super().__init__()  # Kein Parent! Wird als Top-Level-Widget erstellt
        self.main_window = parent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint  # Overlay bleibt über main_window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Overlay muss transparent für Maus-Events sein, damit Dialog nutzbar bleibt
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.highlight_rect = None
        self.highlight_widget = None
    
    def set_highlight(self, widget: QWidget):
        """Setzt das hervorzuhebende Widget."""
        self.highlight_widget = widget
        if widget and self.main_window:
            # Position relativ zum Overlay (das jetzt über dem main_window liegt)
            global_pos = widget.mapToGlobal(QPoint(0, 0))
            overlay_local_pos = self.mapFromGlobal(global_pos)
            self.highlight_rect = QRect(overlay_local_pos, widget.size())
        else:
            self.highlight_rect = None
        self.update()
    
    def clear_highlight(self):
        """Entfernt das Highlight."""
        self.highlight_rect = None
        self.highlight_widget = None
        self.update()
    
    def paintEvent(self, event):
        """Zeichnet das Overlay mit Ausschnitt für Highlight."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dunkler Overlay
        overlay_color = QColor(0, 0, 0, 180)
        painter.fillRect(self.rect(), overlay_color)
        
        # Ausschnitt für highlighted Element
        if self.highlight_rect:
            # Klarer Bereich mit leichtem Glow
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.highlight_rect, Qt.GlobalColor.transparent)
            
            # Border um Highlight
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(76, 175, 80), 3)  # Grüner Rand
            painter.setPen(pen)
            painter.drawRect(self.highlight_rect)


class OnboardingStep:
    """Repräsentiert einen einzelnen Onboarding-Schritt."""
    
    def __init__(self, title: str, text: str, target_widget: QWidget = None):
        self.title = title
        self.text = text
        self.target_widget = target_widget


class OnboardingDialog(QDialog):
    """Dialog für Onboarding-Erklärungen."""
    
    next_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()
    finish_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("onboarding_title"))
        # Dialog mit höchster Priorität
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(False)  # Nicht modal, damit User interagieren kann
        self.setMinimumSize(400, 300)
        
        self.current_step = 0
        self.total_steps = 0
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout()
        
        # Step-Indikator
        self.step_label = QLabel()
        step_font = QFont()
        step_font.setPointSize(11)
        self.step_label.setFont(step_font)
        layout.addWidget(self.step_label)
        
        # Titel
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Text
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setMinimumHeight(150)
        layout.addWidget(self.text_browser)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.skip_btn = QPushButton(tr("skip"))
        self.skip_btn.clicked.connect(self.skip_clicked.emit)
        button_layout.addWidget(self.skip_btn)
        
        button_layout.addStretch()
        
        self.back_btn = QPushButton(tr("back"))
        self.back_btn.clicked.connect(self.back_clicked.emit)
        button_layout.addWidget(self.back_btn)
        
        self.next_btn = QPushButton(tr("next"))
        self.next_btn.clicked.connect(self.next_clicked.emit)
        button_layout.addWidget(self.next_btn)
        
        self.finish_btn = QPushButton(tr("finish"))
        self.finish_btn.clicked.connect(self.finish_clicked.emit)
        self.finish_btn.setVisible(False)
        button_layout.addWidget(self.finish_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def set_step(self, current: int, total: int, title: str, text: str):
        """Setzt den aktuellen Schritt."""
        self.current_step = current
        self.total_steps = total
        
        self.step_label.setText(tr("onboarding_step", current=current, total=total))
        self.title_label.setText(title)
        self.text_browser.setHtml(text.replace("\n", "<br>"))
        
        # Button-Zustände
        self.back_btn.setEnabled(current > 1)
        
        is_last = current == total
        self.next_btn.setVisible(not is_last)
        self.finish_btn.setVisible(is_last)


class OnboardingManager:
    """
    Verwaltet das Onboarding-Tutorial.
    
    Führt durch:
    1. Input (File/Live)
    2. Modell-Auswahl
    3. Speaker Diarization
    4. Profile
    5. Transkription starten
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.history_manager = HistoryManager()
        print ("OnboardingManager: Initialisiert")
        self.overlay = None
        self.dialog = None
        self.steps = []
        self.current_step_index = 0
        
        if not self.history_manager.is_onboarding_completed():
            print("OnboardingManager: Onboarding wird gestartet...")
            self.create_steps()
        print("OnboardingManager: Fertig initialisiert")
    
    def create_steps(self):
        """Erstellt die Onboarding-Schritte."""
        # Schritt 0: Willkommen
        self.steps.append(OnboardingStep(
            tr("onboarding_welcome"),
            tr("onboarding_welcome"),
            None
        ))
        
        # Schritt 1: Input Panel
        self.steps.append(OnboardingStep(
            tr("onboarding_input_title"),
            tr("onboarding_input_text"),
            self.main_window.input_panel if hasattr(self.main_window, 'input_panel') else None
        ))
        
        # Schritt 2: Model Panel
        self.steps.append(OnboardingStep(
            tr("onboarding_model_title"),
            tr("onboarding_model_text"),
            self.main_window.model_panel if hasattr(self.main_window, 'model_panel') else None
        ))
        
        # Schritt 3: Diarization Panel
        self.steps.append(OnboardingStep(
            tr("onboarding_diarization_title"),
            tr("onboarding_diarization_text"),
            self.main_window.diarization_panel if hasattr(self.main_window, 'diarization_panel') else None
        ))
        
        # Schritt 4: Profiles
        self.steps.append(OnboardingStep(
            tr("onboarding_profiles_title"),
            tr("onboarding_profiles_text"),
            None  # Kein spezifisches Widget, ist im Menu
        ))
        
        # Schritt 5: Transkription
        self.steps.append(OnboardingStep(
            tr("onboarding_transcription_title"),
            tr("onboarding_transcription_text"),
            None  # Start-Button wird in show_step gesucht
        ))
    
    def start(self):
        """Startet das Onboarding."""
        # Overlay erstellen (Top-Level-Widget)
        self.overlay = OnboardingOverlay(self.main_window)
        # Overlay über das main_window positionieren
        main_window_geometry = self.main_window.geometry()
        self.overlay.setGeometry(main_window_geometry)
        self.overlay.show()
        
        # Dialog erstellen
        self.dialog = OnboardingDialog(self.main_window)
        self.dialog.next_clicked.connect(self.next_step)
        self.dialog.back_clicked.connect(self.previous_step)
        self.dialog.skip_clicked.connect(self.skip_onboarding)
        self.dialog.finish_clicked.connect(self.finish_onboarding)
        
        # Ersten Schritt zeigen
        self.current_step_index = 0
        self.show_step(self.current_step_index)
        
        # Dialog positionieren (rechts unten vom main_window)
        self.position_dialog()
        self.dialog.show()
        
        # Dialog explizit nach vorne bringen
        self.dialog.raise_()
        self.dialog.activateWindow()
    
    def position_dialog(self):
        """Positioniert den Dialog in der rechten unteren Ecke des main_window."""
        if not self.dialog or not self.main_window:
            return
        
        # Position relativ zum main_window in globalen Koordinaten
        main_window_geometry = self.main_window.geometry()
        dialog_size = self.dialog.size()
        
        # Rechts unten positionieren
        x = main_window_geometry.x() + main_window_geometry.width() - dialog_size.width() - 50
        y = main_window_geometry.y() + main_window_geometry.height() - dialog_size.height() - 50
        
        self.dialog.move(x, y)
    
    def show_step(self, index: int):
        """Zeigt einen bestimmten Schritt an."""
        if index < 0 or index >= len(self.steps):
            return
        
        step = self.steps[index]
        
        # Dialog aktualisieren
        self.dialog.set_step(
            index + 1,
            len(self.steps),
            step.title,
            step.text
        )
        
        # Highlight setzen
        if step.target_widget and step.target_widget.isVisible():
            self.overlay.set_highlight(step.target_widget)
            
            # Scroll zum Widget wenn möglich
            if hasattr(self.main_window, 'scroll_area'):
                self.main_window.scroll_area.ensureWidgetVisible(step.target_widget)
        else:
            self.overlay.clear_highlight()
        
        # Dialog neu positionieren und nach vorne bringen
        QTimer.singleShot(100, self._reposition_and_raise)
    
    def _reposition_and_raise(self):
        """Positioniert Dialog und bringt ihn nach vorne."""
        self.position_dialog()
        if self.dialog:
            self.dialog.raise_()
            self.dialog.activateWindow()
    
    def next_step(self):
        """Geht zum nächsten Schritt."""
        self.current_step_index += 1
        if self.current_step_index < len(self.steps):
            self.show_step(self.current_step_index)
        else:
            self.finish_onboarding()
    
    def previous_step(self):
        """Geht zum vorherigen Schritt."""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.show_step(self.current_step_index)
    
    def skip_onboarding(self):
        """Überspringt das Onboarding."""
        from PyQt6.QtWidgets import QMessageBox
        
        # Overlay temporär verstecken, damit MessageBox sichtbar ist
        if self.overlay:
            self.overlay.hide()
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle("Tutorial überspringen?")
        msg_box.setText("Möchten Sie das Tutorial wirklich überspringen?\n\n"
                       "Sie können es jederzeit über das Hilfe-Menü erneut starten.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        reply = msg_box.exec()
        
        # Overlay wieder anzeigen, wenn nicht abgebrochen
        if reply != QMessageBox.StandardButton.Yes and self.overlay:
            self.overlay.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.finish_onboarding()
    
    def finish_onboarding(self):
        """Beendet das Onboarding."""
        # Aufräumen
        if self.overlay:
            self.overlay.close()
            self.overlay.deleteLater()
            self.overlay = None
        
        if self.dialog:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
        
        # Als abgeschlossen markieren
        self.history_manager.mark_onboarding_completed()
        
        # Erfolgs-Message
        from PyQt6.QtWidgets import QMessageBox
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle(tr("onboarding_title"))
        msg_box.setText(tr("onboarding_complete"))
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.exec()
