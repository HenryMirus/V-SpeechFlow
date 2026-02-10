"""
Utility-Funktionen für Audio-Device Management und UI-Hilfsfunktionen.
"""

import re
from typing import List, Dict, Optional
from PyQt6.QtWidgets import QLabel, QPushButton
from PyQt6.QtGui import QFont
from .macos_utils import request_microphone_permission_message, is_mac
from .constants import SECTION_TITLE_FONT_SIZE, HINT_FONT_SIZE_PX, COLOR_GRAY


def list_audio_devices() -> List[Dict]:
    """
    Listet alle verfügbaren Audio-Eingabegeräte auf.
    
    Returns:
        Liste von Dicts mit 'id', 'name', 'channels', 'sample_rate'
    """
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        devices = []
        
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            
            # Nur Eingabegeräte
            if info['maxInputChannels'] > 0:
                devices.append({
                    'id': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        
        audio.terminate()
        return devices
    
    except ImportError:
        return [{
            'id': -1,
            'name': '❌ PyAudio nicht installiert',
            'channels': 0,
            'sample_rate': 0,
            'error': 'PyAudio nicht verfügbar. Installieren mit: pip install pyaudio'
        }]
    
    except OSError as e:
        # Häufig Permission-Fehler auf macOS
        error_msg = str(e)
        if "Permission denied" in error_msg or "Not authorized" in error_msg:
            if is_mac():
                return [{
                    'id': -1,
                    'name': '🔒 Mikrofonzugriff verweigert (Berechtigungen)',
                    'channels': 0,
                    'sample_rate': 0,
                    'error': request_microphone_permission_message(),
                    'is_permission_error': True
                }]
        
        return [{
            'id': -1,
            'name': f'❌ Fehler beim Konfigurieren von PyAudio: {error_msg}',
            'channels': 0,
            'sample_rate': 0,
            'error': error_msg
        }]
    
    except Exception as e:
        return [{
            'id': -1,
            'name': f'❌ Fehler: {str(e)}',
            'channels': 0,
            'sample_rate': 0,
            'error': str(e)
        }]


def get_default_device() -> Optional[int]:
    """
    Gibt den Standard-Audio-Input zurück.
    
    Returns:
        Device-Index oder None
    """
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        device = audio.get_default_input_device_info()
        audio.terminate()
        return device['index']
    except Exception:
        return None


# ===== UI-Hilfsfunktionen =====

def create_section_title(text: str) -> QLabel:
    """Erstellt ein einheitlich formatiertes Section-Titel-Label."""
    label = QLabel(text)
    title_font = QFont()
    title_font.setPointSize(SECTION_TITLE_FONT_SIZE)
    title_font.setBold(True)
    label.setFont(title_font)
    return label


def create_hint_label(text: str) -> QLabel:
    """Erstellt ein einheitlich formatiertes Hint-/Info-Label (grau, klein)."""
    label = QLabel(text)
    label.setStyleSheet(f"color: {COLOR_GRAY}; font-size: {HINT_FONT_SIZE_PX};")
    label.setWordWrap(True)
    return label


def create_action_button(text: str, color: str, bold: bool = True, padding: str = "8px") -> QPushButton:
    """Erstellt einen farbigen Action-Button (z.B. Start/Stop)."""
    btn = QPushButton(text)
    weight = "bold" if bold else "normal"
    btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: {weight}; padding: {padding};")
    return btn


def parse_timestamp(line: str) -> float:
    """
    Parst Timestamps aus Whisper Output-Zeilen.

    Sucht nach Patterns wie [00:01:23.456 --> 00:01:25.789].

    Args:
        line: Output-Zeile

    Returns:
        Timestamp in Sekunden oder 0.0
    """
    pattern = r'\[(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->'
    match = re.search(pattern, line)

    if match:
        hours, minutes, seconds, milliseconds = match.groups()
        total_seconds = (
            int(hours) * 3600 +
            int(minutes) * 60 +
            int(seconds) +
            int(milliseconds) / 1000.0
        )
        return total_seconds

    return 0.0


def validate_token_format(token: str) -> bool:
    """
    Validiert das Format eines HuggingFace Tokens.

    Returns:
        True wenn Format gültig (beginnt mit hf_ und hat min. 20 Zeichen)
    """
    return token.startswith("hf_") and len(token) >= 20
