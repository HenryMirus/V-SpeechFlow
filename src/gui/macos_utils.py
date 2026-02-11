"""
macOS-spezifische Funktionen (Keychain, native APIs)

Bereitgestellt nur auf macOS, fallback auf anderen Systemen.

**HuggingFace Token Management:**
- Token wird NICHT in History/JSON gespeichert
- Token wird ausschließlich in macOS Keychain gespeichert
- Auto-Load beim Start des Diarization-Panels
- Service-Name in Keychain: "HF_V-Speechflow"
- Manuelle Speicherung via Terminal: 
  `security add-generic-password -s HF_V-Speechflow -a user -w "hf_xxx"`
"""

import sys
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def save_hf_token_to_keychain(token: str, service_name: str = "HF_V-Speechflow") -> bool:
    """
    Speichert HuggingFace Token in macOS Keychain.
    
    Args:
        token: Der zu speichernde Token
        service_name: Keychain Service-Name (default: HF_V-Speechflow)
    
    Returns:
        True wenn erfolgreich gespeichert, False bei Fehler
    """
    if sys.platform != "darwin":
        return False  # Nur auf macOS verfügbar
    
    if not token or not token.strip():
        return False
    
    try:
        # Erst versuchen zu löschen (falls bereits vorhanden)
        subprocess.run(
            ["security", "delete-generic-password", "-s", service_name],
            capture_output=True,
            timeout=5
        )
        
        # Dann neu hinzufügen
        result = subprocess.run(
            ["security", "add-generic-password", "-s", service_name, "-a", "user", "-w", token.strip()],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return result.returncode == 0
    
    except Exception as e:
        logger.error(f"Error saving token to keychain: {e}")
        return False


def get_hf_token_from_keychain(service_name: str = "HF_V-Speechflow") -> Optional[str]:
    """
    Liest HuggingFace Token aus macOS Keychain.
    
    Args:
        service_name: Keychain Service-Name (default: HF_V-Speechflow)
    
    Returns:
        Token als String oder None wenn nicht gefunden
    
    Beispiel Nutzung:
        # Token speichern (Python):
        save_hf_token_to_keychain("hf_xxx")
        
        # Token auslesen (Python):
        token = get_hf_token_from_keychain()
    """
    if sys.platform != "darwin":
        return None # Nur auf macOS verfügbar
    
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service_name, "-w"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    
    except Exception as e:
        # Token nicht im Keychain oder Fehler
        return None


def request_microphone_permission_message() -> str:
    """
    Gibt eine hilfreiche Nachricht für macOS Mikrofon-Berechtigungen zurück.
    
    Returns:
        Fehlermeldung mit Anleitung
    """
    return (
        "🔒 Mikrofonzugriff erforderlich!\n\n"
        "Bitte geben Sie der Anwendung Zugriff auf das Mikrofon:\n\n"
        "1. Öffnen Sie: System Einstellungen\n"
        "2. Gehen Sie zu: Datenschutz & Sicherheit → Mikrofon\n"
        "3. Fügen Sie diese Anwendung zur Liste hinzu\n"
        "4. Starten Sie die Anwendung neu"
    )


def is_mac() -> bool:
    """Gibt True zurück wenn auf macOS."""
    return sys.platform == "darwin"
