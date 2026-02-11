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


# ===== Fehler-Klassifikation für STT-Output =====

# Bekannte Fehlermuster aus stt_native, wav_reader, whisper.cpp und stt_cli.py
# Geordnet nach Spezifität (spezifischere Muster zuerst)
_ERROR_PATTERNS = [
    # WAV-Datei-Fehler (wav_reader.cpp)
    ("cannot open wav file", "error_wav_cannot_open"),
    ("not a valid wav file", "error_wav_invalid"),
    ("only pcm format supported", "error_wav_pcm_only"),
    ("only 16-bit samples supported", "error_wav_16bit_only"),
    ("failed to read audio data", "error_wav_read_failed"),

    # Model-Fehler (stt_engine.cpp, whisper.cpp)
    ("invalid model data", "error_model_invalid"),
    ("failed to load model", "error_model_load_failed"),
    ("engine not initialized", "error_engine_not_init"),

    # Transkriptions-Fehler (whisper.cpp intern)
    ("failed to compute vad", "error_vad_failed"),
    ("failed to compute log mel spectrogram", "error_mel_failed"),
    ("failed to auto-detect language", "error_lang_detect_failed"),
    ("too many decoders requested", "error_too_many_decoders"),
    ("audio_ctx is larger than the maximum allowed", "error_audio_ctx_too_large"),
    ("failed to encode", "error_encode_failed"),
    ("failed to decode", "error_decode_failed"),
    ("transcription failed with code", "error_transcription_code"),

    # Konvertierung (stt_cli.py)
    ("ffmpeg conversion failed", "error_ffmpeg_failed"),

    # Binary/Model nicht gefunden (stt_cli.py)
    ("stt binary not found", "error_binary_not_found"),
    ("stt_native binary not found", "error_binary_not_found"),
    ("model file not found", "error_model_not_found"),
    ("audio file not found", "error_audio_not_found"),

    # Diarization-Fehler (stt_cli.py)
    ("diarization module not available", "error_diarization_unavailable"),
    ("hf token required", "error_hf_token_required"),

    # Speicher-Fehler (whisper.cpp)
    ("failed to allocate memory", "error_out_of_memory"),
]

# Muster die in stdout vorkommen können (nicht stderr)
_STDOUT_WARNING_PATTERNS = [
    ("found 0 speaker(s)", "warning_no_speakers"),
]

# Warnmuster — Dinge die beachtenswert sind, aber kein harter Fehler
# (z.B. Datei wurde trotzdem erstellt, aber mit Einschränkungen)
_WARNING_PATTERNS = [
    ("no speakers detected", "warning_no_speakers"),
    ("could not parse transcript segments", "warning_no_segments"),
    ("sample rate is", "warning_sample_rate"),
    ("audio has", "warning_channels"),
]


def classify_stderr_error(stderr_lines: list) -> Optional[str]:
    """
    Analysiert stderr-Zeilen und gibt die spezifischste Fehlermeldung zurück.

    Durchsucht die stderr-Ausgabe nach bekannten Fehlermustern aus stt_native,
    wav_reader, whisper.cpp und stt_cli.py.

    Args:
        stderr_lines: Liste von stderr-Zeilen

    Returns:
        Die originale stderr-Zeile des ersten erkannten Fehlers, oder None
        wenn kein bekanntes Fehlermuster gefunden wurde.
    """
    if not stderr_lines:
        return None

    for line in stderr_lines:
        line_lower = line.strip().lower()
        for pattern, _key in _ERROR_PATTERNS:
            if pattern in line_lower:
                return line.strip()

    return None


def classify_process_error(stderr_lines: list, stdout_lines: list = None) -> Optional[str]:
    """
    Analysiert stderr UND stdout nach Fehlermustern.

    Prüft zuerst stderr (höhere Priorität), dann stdout auf bekannte
    Warnmuster (z.B. 'Found 0 speaker(s)').

    Args:
        stderr_lines: Liste von stderr-Zeilen
        stdout_lines: Liste von stdout-Zeilen (optional)

    Returns:
        Die originale Zeile des ersten erkannten Fehlers/Warnung, oder None.
    """
    # Zuerst stderr prüfen (höhere Priorität)
    result = classify_stderr_error(stderr_lines)
    if result:
        return result

    # Dann stdout auf bekannte Warnmuster prüfen
    if stdout_lines:
        for line in stdout_lines:
            line_lower = line.strip().lower()
            for pattern, _key in _STDOUT_WARNING_PATTERNS:
                if pattern in line_lower:
                    return line.strip()

    return None


def classify_process_warning(stderr_lines: list, stdout_lines: list = None) -> Optional[str]:
    """
    Analysiert stderr UND stdout nach Warnmustern.

    Warnings sind Hinweise auf Probleme, die aber nicht zum Abbruch führen
    (z.B. keine Sprecher erkannt, aber Transkript trotzdem erstellt).

    Args:
        stderr_lines: Liste von stderr-Zeilen
        stdout_lines: Liste von stdout-Zeilen (optional)

    Returns:
        Die originale Zeile der ersten erkannten Warnung, oder None.
    """
    all_lines = list(stderr_lines or [])
    if stdout_lines:
        all_lines.extend(stdout_lines)

    for line in all_lines:
        line_lower = line.strip().lower()
        for pattern, _key in _WARNING_PATTERNS:
            if pattern in line_lower:
                return line.strip()

    # Auch stdout-spezifische Warnmuster prüfen
    if stdout_lines:
        for line in stdout_lines:
            line_lower = line.strip().lower()
            for pattern, _key in _STDOUT_WARNING_PATTERNS:
                if pattern in line_lower:
                    return line.strip()

    return None


def is_whisper_debug_line(line: str) -> bool:
    """
    Prüft ob eine stderr-Zeile eine Debug-/Info-Meldung von whisper/ggml ist
    (und kein echter Fehler).

    Zeilen die mit whisper_/ggml_/etc. beginnen werden normalerweise als Debug
    betrachtet, AUSSER sie enthalten ein Error-Keyword wie 'failed', 'error', etc.

    Args:
        line: Eine einzelne stderr-Zeile

    Returns:
        True wenn die Zeile als Debug/Info klassifiziert wird (kein Fehler)
    """
    text_lower = line.strip().lower()

    debug_prefixes = (
        'whisper_', 'ggml_', 'metal_', 'backend_', 'compute_',
        'encoder_', 'decoder_', 'kv_cache_', 'model_'
    )

    if not any(text_lower.startswith(prefix) for prefix in debug_prefixes):
        return False

    # Zeile beginnt mit Debug-Prefix — prüfe ob sie trotzdem einen Fehler enthält
    error_indicators = (
        'failed', 'error', 'invalid', 'cannot', 'unable',
        'not found', 'not a valid', 'out of memory',
    )

    if any(indicator in text_lower for indicator in error_indicators):
        return False  # Ist ein echter Fehler, kein Debug

    return True


def is_stderr_error_line(line: str) -> bool:
    """
    Prüft ob eine stderr-Zeile ein Fehler ist (nicht Debug/Info).

    Args:
        line: Eine einzelne stderr-Zeile

    Returns:
        True wenn die Zeile als Fehler klassifiziert wird
    """
    text_lower = line.strip().lower()

    error_keywords = (
        'error:', 'failed:', 'exception:', 'traceback',
        'cannot', 'unable to', 'failed to', 'not found',
        'invalid', 'not a valid',
    )

    return any(keyword in text_lower for keyword in error_keywords)
