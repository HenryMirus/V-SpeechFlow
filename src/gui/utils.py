"""
Utility-Funktionen für Audio-Device Management
"""

from typing import List, Dict, Optional
from .macos_utils import request_microphone_permission_message, is_mac


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
    except:
        return None
