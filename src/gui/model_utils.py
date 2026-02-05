"""
Modell-Management Utilities

Verwaltung von Whisper.cpp Modellen (Download, Validierung, Info).
"""

from pathlib import Path
from typing import Dict, List, Optional


# Vordefinierte Modelle für V-SpeechFlow
AVAILABLE_MODELS = {
    "ggml-base.bin": {
        "name": "Base (schnell)",
        "size_mb": 150,
        "size_bytes": 150 * 1024 * 1024,
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        "description": "Schnell, gutes Preis-Leistungs-Verhältnis für deutsches Audio"
    },
    "ggml-small.bin": {
        "name": "Small (empfohlen)",
        "size_mb": 500,
        "size_bytes": 500 * 1024 * 1024,
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        "description": "Beste Balance für deutsche Sprache (EMPFOHLEN)"
    },
    "ggml-medium.bin": {
        "name": "Medium (höhere Genauigkeit)",
        "size_mb": 1500,
        "size_bytes": 1500 * 1024 * 1024,
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
        "description": "Höhere Genauigkeit, benötigt mehr RAM (~2-3GB)"
    },
    "ggml-large-v3.bin": {
        "name": "Large v3 (beste Qualität)",
        "size_mb": 3000,
        "size_bytes": 3000 * 1024 * 1024,
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
        "description": "Beste Genauigkeit, benötigt viel RAM (~4-6GB)"
    }
}


def validate_model_file(model_path: str) -> Dict:
    """
    Validiert eine Modell-Datei (existiert, Größe).
    
    Returns:
        Dict mit 'valid', 'exists', 'size_mb', 'error'
    """
    result = {
        'valid': False,
        'exists': False,
        'size_mb': 0,
        'size_bytes': 0,
        'error': None
    }
    
    try:
        path = Path(model_path)
        
        if not path.exists():
            result['error'] = f"Datei nicht gefunden: {model_path}"
            return result
        
        if not path.is_file():
            result['error'] = f"Ist keine Datei: {model_path}"
            return result
        
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        # Grundlegende Größen-Validierung
        # Modelle sollten zwischen 100MB und 4GB sein
        if size_bytes < 100 * 1024 * 1024:
            result['error'] = f"Datei zu klein ({size_mb:.1f}MB). Gültiges Modell? ({model_path})"
            return result
        
        if size_bytes > 4 * 1024 * 1024 * 1024:
            result['error'] = f"Datei zu groß ({size_mb:.1f}MB). Zu large für diesen Code-Pfad?"
            return result
        
        result['exists'] = True
        result['valid'] = True
        result['size_mb'] = round(size_mb, 1)
        result['size_bytes'] = size_bytes
        
        return result
    
    except Exception as e:
        result['error'] = f"Fehler bei Validierung: {str(e)}"
        return result


def get_model_info(filename: str) -> Optional[Dict]:
    """
    Gibt Informationen über ein vordefiniertes Modell.
    
    Args:
        filename: z.B. 'ggml-small.bin'
    
    Returns:
        Dict oder None
    """
    return AVAILABLE_MODELS.get(filename)


def get_all_models() -> Dict:
    """Gibt alle verfügbaren Modelle zurück."""
    return AVAILABLE_MODELS


def format_size_mb(size_bytes: int) -> str:
    """Formatiert Bytes zu lesbarer Größe."""
    mb = size_bytes / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.1f} MB"
    else:
        gb = mb / 1024
        return f"{gb:.2f} GB"
