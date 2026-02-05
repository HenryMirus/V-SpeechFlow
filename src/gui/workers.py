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
                bufsize=1
            )
            
            # Output in Echtzeit lesen
            while True:
                output = self.process.stdout.readline()
                if output:
                    self.output_received.emit(output.rstrip())
                else:
                    break
            
            # Fehler auslesen
            for line in self.process.stderr:
                self.error_received.emit(line.rstrip())
            
            # Warten bis Prozess beendet
            return_code = self.process.wait()
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
