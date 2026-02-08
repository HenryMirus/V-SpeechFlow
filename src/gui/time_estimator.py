"""
Time Estimator für Transkriptions-Fortschritt

Schätzt Verarbeitungszeit und Restzeit basierend auf Audio-Länge und Verarbeitungsgeschwindigkeit.
"""

import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class TimeEstimator:
    """Schätzt Verarbeitungszeit und Restzeit für Audio-Transkription."""
    
    def __init__(self):
        self.audio_duration = 0.0  # Sekunden
        self.start_time = None
        self.elapsed_time = 0.0
        self.last_progress_time = None
        self.processing_speed = 1.0  # Realtime-Faktor (1.0 = Echtzeit)
        self.estimated_total_time = 0.0
    
    def get_audio_duration(self, audio_file: str) -> Optional[float]:
        """
        Ermittelt die Länge der Audio-Datei in Sekunden.
        
        Args:
            audio_file: Pfad zur Audio-Datei
            
        Returns:
            Länge in Sekunden oder None bei Fehler
        """
        try:
            # Versuche mit ffprobe (präzise)
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    audio_file
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                return duration
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        # Fallback: Schätze basierend auf Dateigröße
        # Grobe Schätzung: ~1MB pro Minute für komprimiertes Audio
        try:
            file_size_mb = Path(audio_file).stat().st_size / 1024 / 1024
            estimated_minutes = file_size_mb  # Sehr grobe Schätzung
            return estimated_minutes * 60
        except:
            return None
    
    def start(self, audio_file: str):
        """
        Startet die Zeitschätzung.
        
        Args:
            audio_file: Pfad zur Audio-Datei
        """
        self.audio_duration = self.get_audio_duration(audio_file) or 0.0
        self.start_time = time.time()
        self.last_progress_time = self.start_time
        self.elapsed_time = 0.0
        
        # Initiale Schätzung basierend auf Modell/Threads
        # Whisper verarbeitet typischerweise 0.1x - 1.0x Realtime
        # (10 Minuten Audio = 1-10 Minuten Verarbeitung)
        self.processing_speed = 0.3  # Standardwert: ~30% Realtime
        self.estimated_total_time = self.audio_duration / self.processing_speed if self.processing_speed > 0 else 0
    
    def update(self, current_timestamp: Optional[float] = None):
        """
        Aktualisiert die Schätzung.
        
        Args:
            current_timestamp: Aktueller Timestamp aus dem Transkript (in Sekunden)
        """
        now = time.time()
        self.elapsed_time = now - self.start_time if self.start_time else 0
        
        # Wenn wir einen Timestamp haben, können wir die Geschwindigkeit berechnen
        if current_timestamp and current_timestamp > 0 and self.elapsed_time > 0:
            # Verarbeitungsgeschwindigkeit: Audio-Sekunden pro echte Sekunde
            self.processing_speed = current_timestamp / self.elapsed_time
            
            # Verbleibende Audio-Zeit
            remaining_audio = max(0, self.audio_duration - current_timestamp)
            
            # Geschätzte verbleibende Verarbeitungszeit
            if self.processing_speed > 0:
                self.estimated_total_time = self.elapsed_time + (remaining_audio / self.processing_speed)
    
    def get_progress_percentage(self, current_timestamp: Optional[float] = None) -> float:
        """
        Gibt den Fortschritt in Prozent zurück.
        
        Args:
            current_timestamp: Aktueller Timestamp aus dem Transkript
            
        Returns:
            Fortschritt in Prozent (0-100)
        """
        if not self.audio_duration or self.audio_duration <= 0:
            # Keine Audio-Länge bekannt, zeige zeitbasierte Schätzung
            if self.estimated_total_time > 0:
                progress = (self.elapsed_time / self.estimated_total_time) * 100
                return min(99, progress)  # Max 99% ohne echte Info
            return 0
        
        if current_timestamp and current_timestamp > 0:
            # Basierend auf Timestamp
            progress = (current_timestamp / self.audio_duration) * 100
            return min(100, progress)
        
        # Fallback: zeitbasierte Schätzung
        if self.estimated_total_time > 0:
            progress = (self.elapsed_time / self.estimated_total_time) * 100
            return min(99, progress)
        
        return 0
    
    def get_elapsed_time_str(self) -> str:
        """Gibt die verstrichene Zeit als String zurück."""
        return self.format_time(self.elapsed_time)
    
    def get_remaining_time_str(self, current_timestamp: Optional[float] = None) -> str:
        """
        Gibt die geschätzte verbleibende Zeit als String zurück.
        
        Args:
            current_timestamp: Aktueller Timestamp aus dem Transkript
            
        Returns:
            Formatierte Restzeit (z.B. "2m 30s")
        """
        if current_timestamp and self.audio_duration > 0:
            remaining_audio = max(0, self.audio_duration - current_timestamp)
            if self.processing_speed > 0:
                remaining_time = remaining_audio / self.processing_speed
                return self.format_time(remaining_time)
        
        # Fallback
        if self.estimated_total_time > 0:
            remaining = max(0, self.estimated_total_time - self.elapsed_time)
            return self.format_time(remaining)
        
        return "Berechnung läuft..."
    
    def get_eta_str(self, current_timestamp: Optional[float] = None) -> str:
        """
        Gibt die geschätzte Fertigstellungszeit zurück.
        
        Returns:
            Formatierte ETA (z.B. "in 2m 30s")
        """
        remaining = self.get_remaining_time_str(current_timestamp)
        if remaining == "Berechnung läuft...":
            return remaining
        return f"in {remaining}"
    
    def get_speed_info(self) -> str:
        """Gibt Info über Verarbeitungsgeschwindigkeit zurück."""
        if self.processing_speed > 0:
            speed_percent = self.processing_speed * 100
            return f"{speed_percent:.1f}% Realtime"
        return "Berechnung läuft..."
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """
        Formatiert Sekunden als lesbaren String.
        
        Args:
            seconds: Zeit in Sekunden
            
        Returns:
            Formatierte Zeit (z.B. "2m 30s" oder "1h 15m")
        """
        if seconds < 0:
            return "0s"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def reset(self):
        """Setzt den Estimator zurück."""
        self.audio_duration = 0.0
        self.start_time = None
        self.elapsed_time = 0.0
        self.last_progress_time = None
        self.processing_speed = 1.0
        self.estimated_total_time = 0.0
