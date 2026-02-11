"""
Modell-Management Utilities

Verwaltung von Whisper.cpp Modellen (Download, Validierung, Info).
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
import requests
from datetime import datetime, timedelta
import json


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


def get_models_dir() -> Path:
    """
    Gibt den Pfad zum models-Ordner im Projekt zurück.
    Erstellt den Ordner, falls er nicht existiert.
    """
    models_dir = Path(__file__).parent.parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_model_path_in_models_dir(filename: str) -> Path:
    """Gibt den vollständigen Pfad zu einem Modell im models-Ordner zurück."""
    return get_models_dir() / filename


def is_model_downloaded(filename: str) -> bool:
    """Prüft ob ein Modell bereits im models-Ordner vorhanden ist."""
    model_path = get_model_path_in_models_dir(filename)
    if not model_path.exists():
        return False
    # Mindestens 100MB für ein gültiges Modell
    return model_path.stat().st_size >= 100 * 1024 * 1024


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
            result['error'] = f"Datei zu groß ({size_mb:.1f}MB). Ist das ein gültiges Whisper-Modell?"
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


# ===== Model Update Checking =====

def get_model_hash(model_path: str) -> Optional[str]:
    """
    Berechnet SHA256-Hash eines Modells.
    
    Args:
        model_path: Pfad zur Modell-Datei
    
    Returns:
        Hash-String oder None bei Fehler
    """
    try:
        path = Path(model_path)
        if not path.exists():
            return None
        
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            # In Chunks lesen für große Dateien
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating hash: {e}")
        return None


def check_model_update_available(model_path: str, timeout: int = 5) -> Dict:
    """
    Prüft ob ein Update für das Modell verfügbar ist.
    
    Vergleicht die Größe der lokalen Datei mit der auf HuggingFace.
    
    Args:
        model_path: Pfad zur lokalen Modell-Datei
        timeout: Timeout für HTTP-Request in Sekunden
    
    Returns:
        Dict mit:
        - 'update_available': bool
        - 'local_size_mb': float
        - 'remote_size_mb': float oder None
        - 'model_name': str
        - 'error': str oder None
    """
    result = {
        'update_available': False,
        'local_size_mb': 0,
        'remote_size_mb': None,
        'model_name': None,
        'download_url': None,
        'error': None
    }
    
    try:
        path = Path(model_path)
        
        if not path.exists():
            result['error'] = "Model file not found"
            return result
        
        # Lokale Größe
        local_size = path.stat().st_size
        result['local_size_mb'] = round(local_size / (1024 * 1024), 1)
        
        # Model-Name extrahieren
        model_filename = path.name
        result['model_name'] = model_filename
        
        # Model-Info abrufen
        model_info = get_model_info(model_filename)
        if not model_info:
            result['error'] = "Unknown model (not in preset list)"
            return result
        
        # Remote-Größe via HTTP HEAD Request
        url = model_info['url']
        result['download_url'] = url
        
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Content-Length Header
            if 'Content-Length' in response.headers:
                remote_size = int(response.headers['Content-Length'])
                result['remote_size_mb'] = round(remote_size / (1024 * 1024), 1)
                
                # Vergleich mit 1% Toleranz
                size_diff = abs(remote_size - local_size)
                tolerance = local_size * 0.01  # 1%
                
                if size_diff > tolerance:
                    result['update_available'] = True
            else:
                result['error'] = "Could not determine remote file size"
        
        except requests.RequestException as e:
            result['error'] = f"Network error: {str(e)}"
        
        return result
    
    except Exception as e:
        result['error'] = f"Error checking for updates: {str(e)}"
        return result


def get_update_cache_path() -> Path:
    """Gibt den Pfad zur Update-Cache-Datei zurück."""
    cache_dir = Path.home() / ".vspeechflow" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "model_update_cache.json"


def load_update_cache() -> Dict:
    """Lädt den Update-Cache."""
    cache_path = get_update_cache_path()
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_update_cache(cache_data: Dict):
    """Speichert den Update-Cache."""
    cache_path = get_update_cache_path()
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error saving update cache: {e}")


def should_check_for_updates(model_path: str, check_interval_hours: int = 24) -> bool:
    """
    Prüft ob ein Update-Check durchgeführt werden sollte (basierend auf Cache).
    
    Args:
        model_path: Pfad zur Modell-Datei
        check_interval_hours: Stunden zwischen Checks
    
    Returns:
        True wenn Check durchgeführt werden sollte
    """
    cache = load_update_cache()
    model_key = str(Path(model_path).resolve())
    
    if model_key not in cache:
        return True
    
    last_check_str = cache[model_key].get('last_check')
    if not last_check_str:
        return True
    
    try:
        last_check = datetime.fromisoformat(last_check_str)
        time_since_check = datetime.now() - last_check
        
        return time_since_check > timedelta(hours=check_interval_hours)
    except Exception:
        return True


def mark_update_checked(model_path: str, update_available: bool):
    """
    Markiert dass ein Update-Check durchgeführt wurde.
    
    Args:
        model_path: Pfad zur Modell-Datei
        update_available: Ob ein Update verfügbar war
    """
    cache = load_update_cache()
    model_key = str(Path(model_path).resolve())
    
    cache[model_key] = {
        'last_check': datetime.now().isoformat(),
        'update_available': update_available
    }
    
    save_update_cache(cache)


def check_model_updates_with_cache(model_path: str, force: bool = False) -> Optional[Dict]:
    """
    Prüft auf Updates mit Caching-Mechanismus.
    
    Args:
        model_path: Pfad zur Modell-Datei
        force: Cache ignorieren und immer prüfen
    
    Returns:
        Update-Info Dict oder None wenn kein Check nötig
    """
    # Prüfen ob Check nötig
    if not force and not should_check_for_updates(model_path):
        return None
    
    # Update-Check durchführen
    result = check_model_update_available(model_path)
    
    # Cache aktualisieren
    if result.get('error') is None:
        mark_update_checked(model_path, result['update_available'])
    
    return result
