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
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPalette
from .translations import tr
from .history import HistoryManager


class OnboardingStep:
    """Repräsentiert einen einzelnen Onboarding-Schritt."""
    
    def __init__(self, title: str, text: str, target_widget: QWidget = None, tab_index: int = None):
        self.title = title
        self.text = text
        self.target_widget = target_widget
        self.tab_index = tab_index  # Optionaler Tab-Index für Input-Panel


class OnboardingDialog(QDialog):
    """Dialog für Onboarding-Erklärungen."""
    
    next_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()
    finish_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        # WICHTIG: Kein Parent setzen, um Blocking zu vermeiden!
        super().__init__(None)
        self.main_window_ref = parent  # Nur als Referenz speichern
        self.setWindowTitle(tr("onboarding_title"))
        # Als normales Window statt Dialog, um Blocking zu vermeiden
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        # Explizit nicht-modal
        self.setModal(False)
        self.setMinimumSize(450, 350)
        
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
        self.dialog = None
        self.steps = []
        self.current_step_index = 0
        self.highlighted_widget = None
        self.highlight_overlay = None  # Overlay-Frame für Highlighting
        
        if not self.history_manager.is_onboarding_completed():
            print("OnboardingManager: Onboarding wird gestartet...")
            self.create_steps()
        print("OnboardingManager: Fertig initialisiert")
    
    def create_steps(self):
        """Erstellt die Onboarding-Schritte."""
        # Schritt 0: Willkommen
        self.steps.append(OnboardingStep(
            "🎉 Willkommen bei V-SpeechFlow!",
            "<p>Dieses Tutorial führt Sie durch die wichtigsten Funktionen der App.</p>"
            "<p><b>Tipp:</b> Sie können jederzeit im Hauptfenster scrollen und mit der App interagieren!</p>"
            "<p>Klicken Sie auf 'Weiter' um zu beginnen.</p>",
            None
        ))
        
        # Schritt 1: Input Panel - File Tab
        self.steps.append(OnboardingStep(
            "📁 Audio-Datei auswählen",
            "<p>Im <b>Datei-Tab</b> können Sie eine Audio-Datei auswählen:</p>"
            "<ul>"
            "<li>Per Drag & Drop</li>"
            "<li>Über den Durchsuchen-Button</li>"
            "</ul>"
            "<p>Unterstützte Formate: MP3, M4A, WAV, FLAC, OGG</p>",
            self.main_window.input_panel if hasattr(self.main_window, 'input_panel') else None,
            tab_index=0  # File Tab
        ))
        
        # Schritt 2: Batch-Processing
        self.steps.append(OnboardingStep(
            "📦 Batch-Processing",
            "<p>Im <b>Batch-Tab</b> können Sie mehrere Dateien gleichzeitig verarbeiten:</p>"
            "<ul>"
            "<li>Fügen Sie beliebig viele Dateien hinzu</li>"
            "<li>Alle werden mit den aktuellen Einstellungen verarbeitet</li>"
            "<li>Der Fortschritt wird für jede Datei angezeigt</li>"
            "</ul>",
            self.main_window.input_panel if hasattr(self.main_window, 'input_panel') else None,
            tab_index=1  # Batch Tab
        ))
        
        # Schritt 3: Live-Recording
        self.steps.append(OnboardingStep(
            "🎤 Live-Aufnahme",
            "<p>Im <b>Live-Tab</b> können Sie direkt vom Mikrofon aufnehmen:</p>"
            "<ul>"
            "<li>Wählen Sie Ihr Mikrofon aus</li>"
            "<li>Starten Sie die Aufnahme</li>"
            "<li>Die Datei wird automatisch als Input verwendet</li>"
            "</ul>",
            self.main_window.input_panel if hasattr(self.main_window, 'input_panel') else None,
            tab_index=2  # Live Tab
        ))
        
        # Schritt 4: Model Panel
        self.steps.append(OnboardingStep(
            "🤖 Modell auswählen",
            "<p>Wählen Sie ein Whisper-Modell aus:</p>"
            "<ul>"
            "<li><b>Base:</b> Schnell, weniger genau (~150 MB)</li>"
            "<li><b>Small:</b> Ausgewogen (~500 MB)</li>"
            "<li><b>Medium:</b> Höhere Qualität (~1.5 GB)</li>"
            "<li><b>Large-v3:</b> Beste Qualität (~3 GB)</li>"
            "</ul>"
            "<p>Modelle können über die Info-Box heruntergeladen werden.</p>",
            self.main_window.model_panel if hasattr(self.main_window, 'model_panel') else None
        ))
        
        # Schritt 5: Settings Panel
        self.steps.append(OnboardingStep(
            "⚙️ Einstellungen",
            "<p>Passen Sie die Verarbeitung an:</p>"
            "<ul>"
            "<li><b>Threads:</b> CPU-Kerne für Verarbeitung</li>"
            "<li><b>Sprache:</b> Ausgangssprache der Audio-Datei</li>"
            "<li><b>Übersetzen:</b> Automatisch ins Englische übersetzen</li>"
            "</ul>",
            self.main_window.settings_panel if hasattr(self.main_window, 'settings_panel') else None
        ))
        
        # Schritt 6: Diarization Panel
        self.steps.append(OnboardingStep(
            "👥 Speaker Diarization",
            "<p>Erkennen Sie verschiedene Sprecher:</p>"
            "<ul>"
            "<li>Aktivieren Sie Diarization</li>"
            "<li>Wählen Sie zwischen exakter Anzahl oder Auto-Erkennung</li>"
            "<li>Benötigt einen HuggingFace Token (kostenlos)</li>"
            "</ul>"
            "<p><b>Tipp:</b> Token kann in macOS Keychain gespeichert werden!</p>",
            self.main_window.diarization_panel if hasattr(self.main_window, 'diarization_panel') else None
        ))
        
        # Schritt 7: Output Panel
        self.steps.append(OnboardingStep(
            "📄 Ausgabe-Einstellungen",
            "<p>Konfigurieren Sie die Ausgabe:</p>"
            "<ul>"
            "<li><b>Ausgabe-Pfad:</b> Wo soll das Transkript gespeichert werden?</li>"
            "<li><b>Timestamps:</b> Zeitstempel für jedes Segment</li>"
            "<li><b>Format:</b> Plain Text oder strukturiert</li>"
            "</ul>",
            self.main_window.output_panel if hasattr(self.main_window, 'output_panel') else None
        ))
        
        # Schritt 8: Profile
        self.steps.append(OnboardingStep(
            "📋 Profile",
            "<p>Speichern Sie häufig verwendete Einstellungen als Profile:</p>"
            "<ul>"
            "<li>Klicken Sie auf 💾 um aktuelle Einstellungen zu speichern</li>"
            "<li>Wählen Sie ein Profil aus der Dropdown-Liste</li>"
            "<li>Markieren Sie Favoriten mit ⭐</li>"
            "<li>Exportieren/Importieren Sie Profile</li>"
            "</ul>",
            self.main_window.profile_combo if hasattr(self.main_window, 'profile_combo') else None
        ))
        
        # Schritt 9: Start Button
        self.steps.append(OnboardingStep(
            "▶️ Transkription starten",
            "<p>Sie sind bereit!</p>"
            "<ul>"
            "<li>Klicken Sie auf <b>▶️ Start Transkription</b></li>"
            "<li>Der Fortschritt wird rechts angezeigt</li>"
            "<li>Das Transkript erscheint in Echtzeit</li>"
            "</ul>"
            "<p><b>Tastenkürzel:</b></p>"
            "<ul>"
            "<li><b>Strg+Enter:</b> Transkription starten</li>"
            "<li><b>Escape:</b> Abbrechen</li>"
            "<li><b>Strg+B:</b> Batch-Modus aktivieren</li>"
            "<li><b>Strg+S:</b> Profil speichern</li>"
            "</ul>",
            self.main_window.btn_start if hasattr(self.main_window, 'btn_start') else None
        ))
    
    def start(self):
        """Startet das Onboarding."""
        # Dialog erstellen - OHNE Parent um Blocking zu vermeiden!
        self.dialog = OnboardingDialog(self.main_window)  # Parent nur als Referenz
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
        
        # Dialog nach vorne bringen aber Hauptfenster nicht blockieren
        self.dialog.raise_()
    
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
        
        print(f"\\n=== Showing step {index + 1}/{len(self.steps)} ===")
        print(f"Title: {step.title}")
        print(f"Target widget: {step.target_widget.__class__.__name__ if step.target_widget else 'None'}")
        print(f"Tab index: {step.tab_index}")
        
        # Dialog aktualisieren
        self.dialog.set_step(
            index + 1,
            len(self.steps),
            step.title,
            step.text
        )
        
        # Vorheriges Highlight entfernen
        self._clear_widget_highlight()
        
        # Neues Highlight setzen
        if step.target_widget:
            # Wenn ein Tab-Index angegeben ist (für InputPanel), wechsle zum Tab
            if step.tab_index is not None and hasattr(step.target_widget, 'tabs'):
                step.target_widget.tabs.setCurrentIndex(step.tab_index)
                print(f"Switched to tab {step.tab_index}")
            
            # Widget highlighten
            if step.target_widget.isVisible():
                print(f"Widget is visible, highlighting...")
                self._highlight_widget(step.target_widget)
            else:
                print(f"Warning: Widget is not visible!")
                
            # Auto-Scroll zum Widget
            self._scroll_to_widget(step.target_widget)
        
        # Dialog neu positionieren und nach vorne bringen
        QTimer.singleShot(100, self._reposition_and_raise)
    
    def _highlight_widget(self, widget: QWidget):
        """Fügt einem Widget einen temporären Highlight-Border hinzu."""
        if not widget:
            return
        
        # Widget speichern
        self.highlighted_widget = widget
        
        # Finde das richtige Parent-Widget für das Overlay
        # Falls das Widget in einem ScrollArea ist, verwende dessen viewport
        parent = widget.parent()
        if hasattr(self.main_window, 'left_scroll'):
            # Prüfe ob Widget in der linken ScrollArea ist
            scroll_area = self.main_window.left_scroll
            if self._is_child_of(widget, scroll_area):
                parent = scroll_area.viewport()
        
        # Overlay-Frame erstellen, der über dem Widget liegt
        self.highlight_overlay = QFrame(parent)
        self.highlight_overlay.setObjectName("onboarding_highlight_overlay")
        
        # Position im Parent-Koordinatensystem berechnen
        widget_pos_in_parent = widget.mapTo(parent, QPoint(0, 0))
        self.highlight_overlay.setGeometry(
            widget_pos_in_parent.x(),
            widget_pos_in_parent.y(),
            widget.width(),
            widget.height()
        )
        
        # Overlay-Style: Transparenter Hintergrund mit grünem Border
        self.highlight_overlay.setStyleSheet("""
            QFrame#onboarding_highlight_overlay {
                background-color: rgba(76, 175, 80, 0.08);
                border: 3px solid #4CAF50;
                border-radius: 6px;
            }
        """)
        
        # Overlay soll Mausevents durchlassen (nicht blockieren)
        self.highlight_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Overlay sichtbar machen und nach vorne bringen
        self.highlight_overlay.raise_()
        self.highlight_overlay.show()
        
        # Timer für regelmäßige Positions-Updates (falls gescrollt wird)
        if not hasattr(self, 'highlight_update_timer'):
            self.highlight_update_timer = QTimer()
            self.highlight_update_timer.timeout.connect(self._update_highlight_position)
        self.highlight_update_timer.start(100)  # Alle 100ms Position aktualisieren
        
        print(f"Highlighting widget: {widget.__class__.__name__} at {widget.geometry()}")
        print(f"Overlay created at: {self.highlight_overlay.geometry()}")
    
    def _is_child_of(self, widget: QWidget, potential_parent: QWidget) -> bool:
        """Prüft ob widget ein Kind von potential_parent ist."""
        parent = widget.parent()
        while parent:
            if parent == potential_parent:
                return True
            parent = parent.parent()
        return False
    
    def _update_highlight_position(self):
        """Aktualisiert die Position des Highlight-Overlays (z.B. beim Scrollen)."""
        if not self.highlight_overlay or not self.highlighted_widget:
            return
        
        # Position neu berechnen
        parent = self.highlight_overlay.parent()
        widget_pos_in_parent = self.highlighted_widget.mapTo(parent, QPoint(0, 0))
        
        self.highlight_overlay.setGeometry(
            widget_pos_in_parent.x(),
            widget_pos_in_parent.y(),
            self.highlighted_widget.width(),
            self.highlighted_widget.height()
        )
        self.highlight_overlay.raise_()
    
    def _clear_widget_highlight(self):
        """Entfernt den Highlight-Border vom Widget."""
        # Timer stoppen
        if hasattr(self, 'highlight_update_timer'):
            self.highlight_update_timer.stop()
        
        if self.highlight_overlay:
            # Overlay entfernen und löschen
            self.highlight_overlay.hide()
            self.highlight_overlay.deleteLater()
            self.highlight_overlay = None
        
        self.highlighted_widget = None
    
    def _scroll_to_widget(self, widget: QWidget):
        """Scrollt zum angegebenen Widget im Hauptfenster."""
        if not widget or not hasattr(self.main_window, 'left_scroll'):
            return
        
        try:
            scroll_area = self.main_window.left_scroll
            
            # Position des Widgets im scroll_area-Koordinatensystem
            widget_pos = widget.mapTo(scroll_area.widget(), QPoint(0, 0))
            
            # Zentriere das Widget im sichtbaren Bereich
            scroll_bar = scroll_area.verticalScrollBar()
            viewport_height = scroll_area.viewport().height()
            widget_center = widget_pos.y() + widget.height() // 2
            target_scroll = widget_center - viewport_height // 2
            
            # Sanftes Scrollen mit Animation
            current_value = scroll_bar.value()
            
            # Kleine Schritte für sanftes Scrolling
            steps = 10
            step_size = (target_scroll - current_value) / steps
            
            def animate_scroll(step=0):
                if step < steps:
                    new_value = int(current_value + step_size * step)
                    scroll_bar.setValue(new_value)
                    QTimer.singleShot(20, lambda: animate_scroll(step + 1))
                else:
                    scroll_bar.setValue(target_scroll)
            
            animate_scroll()
            
        except Exception as e:
            print(f"Fehler beim Scrollen: {e}")
            # Fallback: Direktes Scrollen ohne Animation
            try:
                scroll_area.ensureWidgetVisible(widget, 50, 50)
            except:
                pass
    
    def _reposition_and_raise(self):
        """Positioniert Dialog und bringt ihn nach vorne."""
        self.position_dialog()
        if self.dialog:
            self.dialog.raise_()
            # NICHT activateWindow() - blockiert unter macOS!
    
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
        
        # MessageBox ohne Parent um Blocking zu vermeiden
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Tutorial überspringen?")
        msg_box.setText("Möchten Sie das Tutorial wirklich überspringen?\n\n"
                       "Sie können es jederzeit über das Hilfe-Menü erneut starten.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.finish_onboarding()
    
    def finish_onboarding(self):
        """Beendet das Onboarding."""
        # Highlight entfernen
        self._clear_widget_highlight()
        
        # Dialog aufräumen
        if self.dialog:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
        
        # Als abgeschlossen markieren
        self.history_manager.mark_onboarding_completed()
        
        # Erfolgs-Message ohne Parent um Blocking zu vermeiden
        from PyQt6.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle(tr("onboarding_title"))
        msg_box.setText(tr("onboarding_complete"))
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        msg_box.exec()
