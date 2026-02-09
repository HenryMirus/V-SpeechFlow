"""
Faktenbasierter Progress Tracker

Parst die tatsächliche CLI-Ausgabe und aktualisiert die Progressbar basierend auf
konkreten Schritten, nicht auf Zeitschätzungen.
"""

import re
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class ProgressTracker:
    """Trackt den Fortschritt basierend auf tatsächlichen CLI-Output-Meldungen."""
    
    # Definiere Phasen und ihre Gewichtung am Gesamtfortschritt
    PHASES = {
        'init': {'weight': 5, 'name': 'Initialisierung'},
        'model_load': {'weight': 10, 'name': 'Modell laden'},
        'audio_convert': {'weight': 15, 'name': 'Audio-Konvertierung'},
        'diarization': {'weight': 20, 'name': 'Speaker-Erkennung'},
        'transcription': {'weight': 45, 'name': 'Transkription'},
        'save': {'weight': 5, 'name': 'Speichern'}
    }
    
    def __init__(self, has_diarization: bool = False):
        """
        Initialisiert den Progress Tracker.
        
        Args:
            has_diarization: Ob Diarization aktiviert ist
        """
        self.has_diarization = has_diarization
        self.current_phase = None
        self.phase_progress = {}  # Fortschritt pro Phase (0-100)
        
        # Audio-Länge für Transkriptions-Fortschritt
        self.audio_duration = 0.0  # Sekunden
        self.last_timestamp = 0.0  # Letzter geparseter Timestamp
        
        # Timer für elapsed time
        self.start_time = None
        self.elapsed_time = 0.0
        
        # Berechne tatsächliche Gewichtung (ohne Diarization wenn nicht aktiviert)
        self._calculate_weights()
        
        self.reset()
    
    def _calculate_weights(self):
        """Berechnet die tatsächlichen Gewichtungen basierend auf aktiven Phasen."""
        self.active_phases = ['init', 'model_load', 'audio_convert', 'transcription', 'save']
        
        if self.has_diarization:
            # Füge Diarization hinzu (zwischen audio_convert und transcription)
            self.active_phases.insert(3, 'diarization')
        
        # Berechne Gesamtgewicht
        self.total_weight = sum(
            self.PHASES[phase]['weight'] 
            for phase in self.active_phases
        )
        
        # Berechne kumulative Gewichte (für Fortschrittsberechnung)
        self.cumulative_weights = {}
        cumulative = 0
        for phase in self.active_phases:
            self.cumulative_weights[phase] = cumulative
            cumulative += self.PHASES[phase]['weight']
    
    def reset(self):
        """Setzt den Tracker zurück."""
        self.current_phase = None
        self.phase_progress = {phase: 0 for phase in self.active_phases}
        self.audio_duration = 0.0
        self.last_timestamp = 0.0
        self.start_time = None
        self.elapsed_time = 0.0
    
    def start(self):
        """Startet den Timer für elapsed time."""
        self.start_time = time.time()
        self.elapsed_time = 0.0
    
    def update_elapsed_time(self):
        """Aktualisiert die verstrichene Zeit."""
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
    
    def get_elapsed_time_str(self) -> str:
        """Gibt die verstrichene Zeit als String zurück."""
        self.update_elapsed_time()
        return self._format_time(self.elapsed_time)
    
    def parse_output_line(self, line: str) -> bool:
        """
        Parst eine Output-Zeile und aktualisiert den Fortschritt.
        
        Args:
            line: Ausgabezeile von der CLI
            
        Returns:
            True wenn Fortschritt aktualisiert wurde
        """
        line_stripped = line.strip()
        if not line_stripped:
            return False
        
        # Timer starten falls noch nicht gestartet
        if not self.start_time:
            self.start_time = time.time()
        
        updated = False
        
        # Phase 1: Initialisierung
        if "V-SpeechFlow STT Native" in line:
            self.current_phase = 'init'
            self.phase_progress['init'] = 100
            updated = True
        
        # Phase 2: Modell laden (graduell)
        elif "Model loaded successfully" in line:
            self.current_phase = 'model_load'
            self.phase_progress['model_load'] = 30
            updated = True
        elif "Language:" in line:
            self.current_phase = 'model_load'
            self.phase_progress['model_load'] = max(self.phase_progress['model_load'], 60)
            updated = True
        elif "Threads:" in line:
            self.current_phase = 'model_load'
            self.phase_progress['model_load'] = max(self.phase_progress['model_load'], 90)
            updated = True
        
        # Phase 3: Audio-Konvertierung
        elif "Converting audio to 16kHz mono WAV" in line:
            # Modell-Phase abschließen
            if self.current_phase == 'model_load':
                self.phase_progress['model_load'] = 100
            self.current_phase = 'audio_convert'
            self.phase_progress['audio_convert'] = 20
            updated = True
        elif "Converted to:" in line:
            self.current_phase = 'audio_convert'
            self.phase_progress['audio_convert'] = 100
            updated = True
        elif "Using WAV file directly" in line:
            # Keine Konvertierung nötig
            if self.current_phase == 'model_load':
                self.phase_progress['model_load'] = 100
            self.current_phase = 'audio_convert'
            self.phase_progress['audio_convert'] = 100
            updated = True
        
        # Phase 4: Diarization (optional)
        elif "=== Speaker Diarization ===" in line:
            if self.has_diarization:
                # Audio-Convert abschließen
                if self.current_phase == 'audio_convert':
                    self.phase_progress['audio_convert'] = 100
                self.current_phase = 'diarization'
                self.phase_progress['diarization'] = 10
                updated = True
        elif "=== Speaker Timeline ===" in line:
            if self.has_diarization:
                self.phase_progress['diarization'] = 100
                updated = True
        
        # Phase 5: Transkription
        elif "=== Transcription ===" in line:
            # Vorherige Phase abschließen
            if self.current_phase == 'audio_convert':
                self.phase_progress['audio_convert'] = 100
            elif self.current_phase == 'diarization':
                self.phase_progress['diarization'] = 100
            self.current_phase = 'transcription'
            self.phase_progress['transcription'] = 5
            updated = True
        elif "Starting transcription" in line:
            self.current_phase = 'transcription'
            self.phase_progress['transcription'] = max(self.phase_progress['transcription'], 10)
            updated = True
        elif "Processing" in line and "samples" in line:
            # "Processing X samples..."
            self.current_phase = 'transcription'
            self.phase_progress['transcription'] = max(self.phase_progress['transcription'], 15)
            updated = True
        
        # Timestamps aus Transkript parsen (während Transkription)
        if self.current_phase == 'transcription':
            timestamp = self._parse_timestamp(line)
            if timestamp > 0 and timestamp > self.last_timestamp:
                self.last_timestamp = timestamp
                # Wenn wir Audio-Länge kennen, berechne Fortschritt
                if self.audio_duration > 0:
                    audio_progress_pct = (timestamp / self.audio_duration) * 100
                    # Transkription: 15% Start, dann 15-95% basierend auf Timestamps
                    transcription_progress = 15 + (audio_progress_pct * 0.80)  # max 95%
                    self.phase_progress['transcription'] = max(
                        self.phase_progress['transcription'],
                        min(95, transcription_progress)
                    )
                else:
                    # Ohne Audio-Länge: langsam hochzählen (max 1% pro Timestamp)
                    self.phase_progress['transcription'] = min(
                        90,
                        self.phase_progress['transcription'] + 0.5
                    )
                updated = True
        
        # Phase 6: Speichern
        if "=== Transcript ===" in line and "with timestamps" not in line:
            # Transkription abgeschlossen, Ausgabe beginnt
            self.phase_progress['transcription'] = 100
            self.current_phase = 'save'
            self.phase_progress['save'] = 20
            updated = True
        elif "Transcript saved to:" in line:
            self.phase_progress['transcription'] = 100
            self.current_phase = 'save'
            self.phase_progress['save'] = 80
            updated = True
        elif "Done." in line:
            # Nur Save-Phase abschließen, nicht alle Phasen
            self.current_phase = 'save'
            self.phase_progress['save'] = 100
            updated = True
        
        return updated
    
    def _parse_timestamp(self, line: str) -> float:
        """
        Parst Timestamps aus Output-Zeilen.
        
        Format: [HH:MM:SS.mmm --> HH:MM:SS.mmm] text
        
        Args:
            line: Output-Zeile
            
        Returns:
            Timestamp in Sekunden oder 0.0
        """
        # Pattern für Timestamps
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
    
    def set_audio_duration(self, duration_seconds: float):
        """
        Setzt die Audio-Länge für präzisere Fortschrittsberechnung.
        
        Args:
            duration_seconds: Länge der Audio-Datei in Sekunden
        """
        self.audio_duration = duration_seconds
    
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
    
    def get_progress_percentage(self) -> float:
        """
        Berechnet den Gesamtfortschritt in Prozent.
        
        Returns:
            Fortschritt von 0-100
        """
        if not self.current_phase:
            return 0.0
        
        # Summiere abgeschlossene Phasen
        total_progress = 0.0
        
        for phase in self.active_phases:
            phase_weight = self.PHASES[phase]['weight']
            phase_pct = self.phase_progress.get(phase, 0) / 100.0
            
            # Beitrag dieser Phase zum Gesamtfortschritt
            contribution = (phase_weight / self.total_weight) * phase_pct * 100
            total_progress += contribution
        
        return min(100.0, total_progress)
    
    def get_current_phase_name(self) -> str:
        """
        Gibt den Namen der aktuellen Phase zurück.
        
        Returns:
            Name der aktuellen Phase oder "Bereit"
        """
        if not self.current_phase:
            return "Bereit"
        
        return self.PHASES[self.current_phase]['name']
    
    def get_status_text(self) -> str:
        """
        Gibt einen Status-Text für die UI zurück.
        
        Returns:
            Formatierter Status-Text
        """
        if not self.current_phase:
            return "Bereit"
        
        phase_name = self.get_current_phase_name()
        progress_pct = self.get_progress_percentage()
        
        # Spezielle Infos für Transkription
        if self.current_phase == 'transcription' and self.last_timestamp > 0:
            if self.audio_duration > 0:
                return f"{phase_name}: {self._format_time(self.last_timestamp)} / {self._format_time(self.audio_duration)}"
            else:
                return f"{phase_name}: {self._format_time(self.last_timestamp)}"
        
        return f"{phase_name}"
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formatiert Sekunden als lesbaren String."""
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
