"""
Theme Management für V-SpeechFlow GUI

Stellt Light und Dark Mode Themes bereit.
"""

class ThemeManager:
    """Verwaltet Themes für die GUI.

    Persistenz erfolgt über HistoryManager.user_preferences['preferred_theme'].
    ThemeManager kümmert sich nur um Stylesheet-Logik.
    """
    
    def __init__(self):
        """Initialisiert den Theme-Manager."""
        from .history import HistoryManager
        self._history = HistoryManager.get_instance()
        self.current_theme = self._history.get_user_preference('preferred_theme', 'light')
    
    def save_theme_preference(self, theme: str):
        """Speichert die Theme-Präferenz über den HistoryManager."""
        self._history.save_user_preference('preferred_theme', theme)
        self.current_theme = theme
    
    def get_current_theme(self) -> str:
        """Gibt das aktuelle Theme zurück."""
        return self.current_theme
    
    def get_stylesheet(self, theme: str = None) -> str:
        """Gibt das Stylesheet für das gewählte Theme zurück."""
        if theme is None:
            theme = self.current_theme
        
        if theme == 'dark':
            return self.get_dark_theme()
        else:
            return self.get_light_theme()
    
    def get_light_theme(self) -> str:
        """Gibt das Light Theme Stylesheet zurück."""
        return """
            QMainWindow, QDialog, QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                background-color: #fafafa;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 5px 10px;
                color: #333333;
            }
            
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999999;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 5px;
                color: #333333;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
            
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 5px;
                color: #333333;
            }
            
            QComboBox:hover {
                border: 1px solid #4CAF50;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                color: #333333;
            }
            
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #e8f5e9;
            }
            
            QCheckBox, QRadioButton {
                color: #333333;
                spacing: 8px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
                background-color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 3px;
            }
            
            QCheckBox::indicator:hover, QRadioButton::indicator:hover {
                background-color: #f0f8f0;
                border: 2px solid #45a049;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                image: url(:/icons/check.png);
            }
            
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
            }
            
            QProgressBar {
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                text-align: center;
                background-color: #f0f0f0;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            
            QSlider::groove:horizontal {
                height: 6px;
                background: #d0d0d0;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            QMenuBar {
                background-color: #f5f5f5;
                color: #333333;
            }
            
            QMenuBar::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                color: #333333;
            }
            
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            QStatusBar {
                background-color: #f5f5f5;
                color: #333333;
            }
            
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                color: #333333;
            }
            
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
            }
            
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """
    
    def get_dark_theme(self) -> str:
        """Gibt das Dark Theme Stylesheet zurück."""
        return """
            QMainWindow, QDialog, QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            
            QGroupBox {
                border: 1px solid #404040;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                background-color: #323232;
                color: #e0e0e0;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                color: #e0e0e0;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            
            QPushButton:pressed {
                background-color: #555555;
            }
            
            QPushButton:disabled {
                background-color: #353535;
                color: #666666;
            }
            
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #66BB6A;
            }
            
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }
            
            QComboBox:hover {
                border: 1px solid #66BB6A;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                selection-background-color: #66BB6A;
                selection-color: #ffffff;
                color: #e0e0e0;
            }
            
            QListWidget {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 3px;
                color: #e0e0e0;
            }
            
            QListWidget::item:selected {
                background-color: #66BB6A;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #404040;
            }
            
            QCheckBox, QRadioButton {
                color: #e0e0e0;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
                background-color: #3a3a3a;
                border: 1px solid #555555;
            }
            
            QCheckBox::indicator:checked {
                background-color: #66BB6A;
            }
            
            QRadioButton::indicator:checked {
                background-color: #66BB6A;
            }
            
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                background-color: #3a3a3a;
                color: #e0e0e0;
            }
            
            QProgressBar::chunk {
                background-color: #66BB6A;
            }
            
            QSlider::groove:horizontal {
                height: 6px;
                background: #454545;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #66BB6A;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            QMenuBar {
                background-color: #323232;
                color: #e0e0e0;
            }
            
            QMenuBar::item:selected {
                background-color: #66BB6A;
                color: white;
            }
            
            QMenu {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                color: #e0e0e0;
            }
            
            QMenu::item:selected {
                background-color: #66BB6A;
                color: white;
            }
            
            QStatusBar {
                background-color: #323232;
                color: #e0e0e0;
            }
            
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3a3a3a;
            }
            
            QTabBar::tab {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                padding: 8px 16px;
                color: #e0e0e0;
            }
            
            QTabBar::tab:selected {
                background-color: #66BB6A;
                color: white;
            }
            
            QScrollBar:vertical {
                background: #3a3a3a;
                width: 12px;
            }
            
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #666666;
            }
            
            QLabel {
                color: #e0e0e0;
            }
        """
