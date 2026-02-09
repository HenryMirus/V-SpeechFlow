"""
iOS-artiger Theme Toggle Switch

Ein animierter Toggle-Switch für das Umschalten zwischen Light und Dark Mode.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath


class ThemeToggleSwitch(QWidget):
    """
    iOS-ähnlicher Toggle Switch für Theme-Wechsel.
    
    Links (☀️): Light Mode
    Rechts (🌙): Dark Mode
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Transparenter Hintergrund für nahtlose Integration in Menubar
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # State
        self._is_dark = False
        self._handle_position = 0.0  # 0.0 = links (light), 1.0 = rechts (dark)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
        
        # Hover state
        self._is_hovered = False
    
    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position
    
    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()
    
    def set_dark_mode(self, is_dark: bool, animate: bool = True):
        """
        Setzt den Dark Mode Status.
        
        Args:
            is_dark: True für Dark Mode, False für Light Mode
            animate: Ob die Änderung animiert werden soll
        """
        if self._is_dark == is_dark:
            return
        
        self._is_dark = is_dark
        target_position = 1.0 if is_dark else 0.0
        
        if animate:
            self.animation.stop()
            self.animation.setStartValue(self._handle_position)
            self.animation.setEndValue(target_position)
            self.animation.start()
        else:
            self._handle_position = target_position
            self.update()
    
    def is_dark_mode(self) -> bool:
        """Returns True wenn Dark Mode aktiv ist."""
        return self._is_dark
    
    def toggle(self):
        """Wechselt zwischen Light und Dark Mode."""
        self.set_dark_mode(not self._is_dark)
    
    def mousePressEvent(self, event):
        """Toggle bei Klick."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            self.clicked()
    
    def clicked(self):
        """Wird aufgerufen wenn der Switch geklickt wurde."""
        # Kann von Parent überschrieben oder connected werden
        pass
    
    def enterEvent(self, event):
        """Maus betritt Widget."""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Maus verlässt Widget."""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Zeichnet den Toggle Switch."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background Track
        track_rect = QRectF(2, 2, width - 4, height - 4)
        
        # Hintergrundfarbe je nach State (passend zur Menubar)
        if self._is_dark:
            # Dark Mode: Helleres Grau als Menubar (#323232), kein Blau
            bg_color = QColor(80, 80, 80) if not self._is_hovered else QColor(90, 90, 90)
        else:
            # Light Mode: Heller Hintergrund (passend zu #f5f5f5)
            bg_color = QColor(220, 220, 220) if not self._is_hovered else QColor(200, 200, 200)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track_rect, height / 2, height / 2)
        
        font = painter.font()
        font.setPointSize(14)
        
        # Handle (Slider)
        handle_width = height - 8
        handle_height = height - 8
        handle_x = 4 + self._handle_position * (width - handle_width - 8)
        handle_y = 4
        
        handle_rect = QRectF(handle_x, handle_y, handle_width, handle_height)
        
        # Handle Schatten (optional, für 3D-Effekt)
        shadow_color = QColor(0, 0, 0, 40)
        shadow_rect = QRectF(handle_x + 1, handle_y + 2, handle_width, handle_height)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(shadow_rect)
        
        # Handle
        handle_color = QColor(255, 255, 255)
        painter.setBrush(QBrush(handle_color))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(handle_rect)
        
        # Icon auf dem Handle (zeigt aktuellen Modus)
        icon_color = QColor(100, 100, 100)
        painter.setPen(QPen(icon_color))
        font.setPointSize(12)
        painter.setFont(font)
        
        # Zeige das Icon des AKTUELLEN Modus auf dem Handle
        icon = "🌙" if self._is_dark else "☀"
        icon_x = handle_x + handle_width // 2 - 6
        icon_y = handle_y + handle_height // 2 + 5
        painter.drawText(int(icon_x), int(icon_y), icon)
