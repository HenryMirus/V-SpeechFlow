"""
macOS-spezifische Funktionen (Keychain, native APIs)

Bereitgestellt nur auf macOS, fallback auf anderen Systemen.
"""

import sys
import subprocess
from typing import Optional


def get_hf_token_from_keychain(service_name: str = "HF_V-Speechflow") -> Optional[str]:
    """
    Liest HuggingFace Token aus macOS Keychain.
    
    Args:
        service_name: Keychain Service-Name (default: HF_V-Speechflow)
    
    Returns:
        Token als String oder None wenn nicht gefunden
    
    Beispiel Nutzung:
        # Token speichern (Terminal):
        security add-generic-password -s HF_V-Speechflow -a user -w "hf_xxx"
        
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
