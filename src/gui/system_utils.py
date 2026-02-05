"""
System-Utilities für Hardware-Erkennung

Bestimmt Mac-Modell und empfiehlt Thread-Anzahl.
"""

import sys
import subprocess
from typing import Optional, Dict


def get_mac_model() -> Optional[str]:
    """
    Ermittelt das Mac-Modell (M1, M2, M3, Intel, etc.).
    
    Returns:
        z.B. "MacBook Pro (16-inch, 2021)" oder None
    """
    if sys.platform != "darwin":
        return None # Nur auf macOS verfügbar
    
    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.model"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return None


def get_cpu_count() -> int:
    """Gibt die Anzahl der verfügbaren CPU-Kerne zurück."""
    import os
    return os.cpu_count() or 4


def get_cpu_brand() -> Optional[str]:
    """
    Gibt die CPU-Marke zurück (Apple Silicon vs Intel).
    
    Returns:
        "Apple", "Intel", "ARM", oder None
    """
    if sys.platform != "darwin":
        return None # Nur auf macOS verfügbar
    
    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            brand_str = result.stdout.strip()
            if "Apple" in brand_str:
                return "Apple"
            elif "Intel" in brand_str:
                return "Intel"
    except Exception:
        pass
    
    # Fallback
    try:
        # Apple Silicon nutzt ARM
        result = subprocess.run(
            ["uname", "-m"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "arm" in result.stdout.lower():
            return "Apple"
        elif "x86" in result.stdout.lower():
            return "Intel"
    except Exception:
        pass
    
    return None


def get_recommended_threads() -> int:
    """
    Gibt die empfohlene Thread-Anzahl basierend auf CPU zurück.
    
    Returns:
        Empfohlene Thread-Anzahl (4-16)
    """
    cpu_count = get_cpu_count()
    
    # Apple Silicon: Performance + Efficiency Cores
    # M1: 8 cores (4P + 4E) → 6-8 threads optimal
    # M2: 8 cores (4P + 4E) → 6-8 threads optimal
    # M3: 8 cores (4P + 4E) → 6-8 threads optimal
    # M3 Pro: 12 cores (6P + 6E) → 8-10 threads optimal
    # M3 Max: 16 cores (12P + 4E) → 10-12 threads optimal
    
    if sys.platform == "darwin":
        cpu_brand = get_cpu_brand() 
        
        if cpu_brand == "Apple":
            # Apple Silicon Empfehlungen
            if cpu_count <= 8:
                return 6  # M1/M2/M3
            elif cpu_count <= 12:
                return 8  # M3 Pro
            else:
                return 10  # M3 Max
        elif cpu_brand == "Intel":
            # Intel Empfehlungen
            if cpu_count <= 4:
                return 4
            elif cpu_count <= 8:
                return 6
            else:
                return 8
    
    # Fallback für andere Systeme
    if cpu_count <= 4:
        return 4
    elif cpu_count <= 8:
        return 6
    else:
        return min(cpu_count - 2, 12)  # Max 12 threads


def get_system_info() -> Dict:
    """
    Gibt umfassende System-Informationen zurück.
    
    Returns:
        Dict mit 'model', 'cpu_brand', 'cpu_count', 'recommended_threads'
    """
    return {
        'model': get_mac_model(),
        'cpu_brand': get_cpu_brand(),
        'cpu_count': get_cpu_count(),
        'recommended_threads': get_recommended_threads(),
        'platform': sys.platform
    }
