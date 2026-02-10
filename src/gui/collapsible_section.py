"""
Kollapsierbare Section für GUI-Panels

Bietet eine wiederverwendbare Komponente für ein- und ausklappbare Bereiche.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CollapsibleSection(QWidget):
    """Ein kollapsierbar/expandierbar Bereich mit Titel."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        """
        Initialisiert einen kollapsiblen Bereich.
        
        Args:
            title: Titel des Bereichs
            icon: Optional: Emoji oder Icon für den Titel
            parent: Parent-Widget
        """
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.is_expanded = True
        
        # Haupt-Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Titel mit Toggle-Button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 5, 0, 5)
        
        # Toggle-Button
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedWidth(25)
        self.toggle_button.setToolTip("Bereich ein-/ausblenden")
        self.toggle_button.clicked.connect(self.toggle)
        self.update_toggle_button()
        title_layout.addWidget(self.toggle_button)
        
        # Titel-Label
        title_label = QLabel(f"{icon} {title}" if icon else title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # Content Container
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 0, 5)
        main_layout.addWidget(self.content_widget)
        
        self.setLayout(main_layout)
    
    def update_toggle_button(self):
        """Aktualisiert das Toggle-Button Aussehen."""
        text = "▼" if self.is_expanded else "▶"
        self.toggle_button.setText(text)
    
    def toggle(self):
        """Toggle zwischen expanded/collapsed."""
        self.set_expanded(not self.is_expanded)
    
    def set_expanded(self, expanded: bool):
        """
        Setzt den Expanded-Status.
        
        Args:
            expanded: True wenn expandiert, False wenn kollapsiert
        """
        self.is_expanded = expanded
        self.content_widget.setVisible(expanded)
        self.update_toggle_button()
    
    def add_widget(self, widget: QWidget):
        """
        Fügt ein Widget zum Content hinzu.
        
        Args:
            widget: Das hinzuzufügende Widget
        """
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """
        Fügt ein Layout zum Content hinzu.
        
        Args:
            layout: Das hinzuzufügende Layout
        """
        self.content_layout.addLayout(layout)
    
    def add_stretch(self):
        """Fügt Stretch zum Content hinzu."""
        self.content_layout.addStretch()
