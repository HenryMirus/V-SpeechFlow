"""
Worker Threads und Subprocess-Management

Verwaltet die CLI-Prozesse und deren Output.
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from .utils import parse_timestamp


class CLIWorker(QThread):
    """Worker-Thread für die Ausführung der CLI."""
    
    output_received = pyqtSignal(str)  # Signal für stdout
    error_received = pyqtSignal(str)   # Signal für stderr
    process_finished = pyqtSignal(int) # Signal für Prozessende (Return-Code)
    progress_updated = pyqtSignal(float, float)  # Signal für Progress (percentage, current_timestamp)
    
    def __init__(self, arguments: list):
        """
        Initialisiert den CLI-Worker.
        
        Args:
            arguments: Liste der CLI-Argumente
        """
        super().__init__()
        self.arguments = arguments
        self.process = None
        self.last_timestamp = 0.0
        self.stderr_lines = []  # Sammelt alle stderr-Zeilen für Fehleranalyse
        self.stdout_lines = []  # Sammelt alle stdout-Zeilen für Fehleranalyse
    
    def parse_timestamp_from_output(self, line: str) -> float:
        """Parst Timestamps aus Whisper Output."""
        return parse_timestamp(line)
    
    def run(self):
        """Führt die CLI mit den übergebenen Argumenten aus."""
        try:
            # Path zur CLI finden
            project_root = Path(__file__).parent.parent
            cli_script = project_root / "python" / "stt_cli.py"
            
            # Check if CLI script exists
            if not cli_script.exists():
                self.error_received.emit(f"CLI script not found: {cli_script}")
                self.process_finished.emit(1)
                return
            
            # Kommando zusammenstellen
            cmd = [sys.executable, str(cli_script)] + self.arguments
            
            # Subprocess starten
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Output in Echtzeit lesen mit Threading
            import threading
            
            def read_stdout():
                """Liest stdout in Echtzeit und parst Timestamps."""
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        line_stripped = line.rstrip()
                        self.stdout_lines.append(line_stripped)
                        self.output_received.emit(line_stripped)
                        
                        # Versuche Timestamp zu parsen
                        timestamp = self.parse_timestamp_from_output(line_stripped)
                        if timestamp > 0 and timestamp > self.last_timestamp:
                            self.last_timestamp = timestamp
                            # Emittiere Progress-Update (percentage wird später berechnet)
                            self.progress_updated.emit(0.0, timestamp)
                
                self.process.stdout.close()
            
            def read_stderr():
                """Liest stderr in separatem Thread."""
                for line in iter(self.process.stderr.readline, ''):
                    if line:
                        stripped = line.rstrip()
                        self.stderr_lines.append(stripped)
                        self.error_received.emit(stripped)
                self.process.stderr.close()
            
            # Threads für stdout und stderr starten
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Warten bis Prozess beendet
            return_code = self.process.wait()
            
            # Warten bis alle Output-Threads fertig sind
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            
            self.process_finished.emit(return_code)
            
        except Exception as e:
            self.error_received.emit(f"Error starting CLI: {str(e)}")
            self.process_finished.emit(1)
    
    def stop(self):
        """Beendet den laufenden Prozess."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Falls Prozess nicht terminiert, erzwinge Kill
                self.process.kill()
                self.process.wait()


class RecordingWorker(QThread):
    """Worker-Thread für Live-Recording."""
    
    volume_updated = pyqtSignal(float)  # Signal für Volume-Updates (0-100)
    duration_updated = pyqtSignal(float)  # Signal für Dauer-Updates (Sekunden)
    recording_error = pyqtSignal(str)  # Signal für Fehler
    recording_finished = pyqtSignal(str)  # Signal für Ende (WAV-Pfad)
    
    def __init__(self, device_index: int, output_path: Path):
        """
        Initialisiert den Recording-Worker.
        
        Args:
            device_index: Index des Audio-Eingabegeräts
            output_path: Pfad zur Ausgabe-WAV-Datei
        """
        super().__init__()
        self.device_index = device_index
        self.output_path = output_path
        self.should_stop = False
        self.recorder = None
    
    def run(self):
        """Führt die Aufnahme aus."""
        try:
            # LiveRecorder aus dem python-Modul importieren
            from ..python.live_recorder import LiveRecorder
            import numpy as np
            
            self.recorder = LiveRecorder()
            
            # Aufnahme starten
            self.recorder.start_recording(device_index=self.device_index)
            
            # Recording-Loop
            while not self.should_stop:
                try:
                    # Chunk aufnehmen
                    data = self.recorder.record_chunk()
                    
                    # Volume berechnen (0-100 Skala)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()
                    
                    # Skalierung auf 0-100 (max. 16-bit ist 32768)
                    volume_percent = min(100, (volume / 32768.0) * 100 * 3)  # 3x Verstärkung für bessere Anzeige
                    self.volume_updated.emit(volume_percent)
                    
                    # Dauer updaten
                    duration = self.recorder.get_duration()
                    self.duration_updated.emit(duration)
                    
                except Exception as e:
                    if not self.should_stop:
                        self.recording_error.emit(f"Recording error: {str(e)}")
                        break
            
            # Aufnahme beenden und speichern
            self.recorder.stop_recording()
            
            # WAV-Datei speichern
            self.recorder.save_wav(self.output_path)
            
            # Erfolg signalisieren
            self.recording_finished.emit(str(self.output_path))
            
        except Exception as e:
            self.recording_error.emit(f"Recording error: {str(e)}")
        
        finally:
            if self.recorder:
                self.recorder.cleanup()
    
    def stop(self):
        """Stoppt die Aufnahme."""
        self.should_stop = True


class ModelDownloadWorker(QThread):
    """Worker-Thread für den Download von Whisper-Modellen."""

    progress_updated = pyqtSignal(float, float)  # (bytes_downloaded, total_bytes) – float wegen >2GB Dateien
    download_finished = pyqtSignal(str)              # Pfad zur heruntergeladenen Datei
    download_error = pyqtSignal(str)                 # Fehlermeldung

    def __init__(self, url: str, dest_path: Path):
        """
        Args:
            url: Download-URL des Modells
            dest_path: Ziel-Pfad für die Datei
        """
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.should_stop = False

    def run(self):
        """Führt den Download aus."""
        import requests

        try:
            # Zielverzeichnis erstellen
            self.dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Temporärer Dateiname während des Downloads
            tmp_path = Path(str(self.dest_path) + '.part')

            response = requests.get(
                self.url,
                stream=True,
                timeout=(15, 300),  # (connect_timeout, read_timeout) – großzügig für große Dateien
                headers={"User-Agent": "V-SpeechFlow/1.0"},
            )
            response.raise_for_status()

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB Chunks

            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.should_stop:
                        f.close()
                        tmp_path.unlink(missing_ok=True)
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress_updated.emit(float(downloaded), float(total_size))

            # Download abgeschlossen – umbenennen
            tmp_path.rename(self.dest_path)
            self.download_finished.emit(str(self.dest_path))

        except Exception as e:
            # Aufräumen bei Fehler
            tmp_path = Path(str(self.dest_path) + '.part')
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            self.download_error.emit(str(e))

    def stop(self):
        """Bricht den Download ab."""
        self.should_stop = True
