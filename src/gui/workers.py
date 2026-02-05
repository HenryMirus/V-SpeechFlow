"""
Worker Threads und Subprocess-Management

Verwaltet die CLI-Prozesse und deren Output.
"""

import subprocess
import sys
import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal


class CLIWorker(QThread):
    """Worker-Thread für die Ausführung der CLI."""
    
    output_received = pyqtSignal(str)  # Signal für stdout
    error_received = pyqtSignal(str)   # Signal für stderr
    process_finished = pyqtSignal(int) # Signal für Prozessende (Return-Code)
    
    def __init__(self, arguments: list):
        """
        Initialisiert den CLI-Worker.
        
        Args:
            arguments: Liste der CLI-Argumente
        """
        super().__init__()
        self.arguments = arguments
        self.process = None
    
    def run(self):
        """Führt die CLI mit den übergebenen Argumenten aus."""
        try:
            # Path zur CLI finden
            project_root = Path(__file__).parent.parent
            cli_script = project_root / "python" / "stt_cli.py"
            
            # Prüfen ob CLI-Script existiert
            if not cli_script.exists():
                self.error_received.emit(f"CLI-Script nicht gefunden: {cli_script}")
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
                """Liest stdout in separatem Thread."""
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.output_received.emit(line.rstrip())
                self.process.stdout.close()
            
            def read_stderr():
                """Liest stderr in separatem Thread."""
                for line in iter(self.process.stderr.readline, ''):
                    if line:
                        self.error_received.emit(line.rstrip())
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
            self.error_received.emit(f"Fehler beim Starten der CLI: {str(e)}")
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
            # LiveRecorder importieren - sys.path muss zuerst gesetzt werden
            import sys
            from pathlib import Path as PathLib
            project_root = PathLib(__file__).parent.parent
            python_path = str(project_root / "python")
            
            if python_path not in sys.path:
                sys.path.insert(0, python_path)
            
            # Jetzt importieren (wird zur Laufzeit über den angepassten sys.path gefunden)
            from live_recorder import LiveRecorder  # type: ignore
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
                        self.recording_error.emit(f"Fehler beim Aufnehmen: {str(e)}")
                        break
            
            # Aufnahme beenden und speichern
            self.recorder.stop_recording()
            
            # WAV-Datei speichern
            self.recorder.save_wav(self.output_path)
            
            # Erfolg signalisieren
            self.recording_finished.emit(str(self.output_path))
            
        except Exception as e:
            self.recording_error.emit(f"Recording-Fehler: {str(e)}")
        
        finally:
            if self.recorder:
                self.recorder.cleanup()
    
    def stop(self):
        """Stoppt die Aufnahme."""
        self.should_stop = True
