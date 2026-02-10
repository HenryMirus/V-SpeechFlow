#!/usr/bin/env python3
"""
V-SpeechFlow Development Runner mit Hot Reloading
Startet die GUI und lädt sie bei Änderungen automatisch neu
"""

import sys
import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AppReloader(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart_app()
        
    def restart_app(self):
        print("\n" + "="*60)
        print("🔄 Starte V-SpeechFlow...")
        print("="*60 + "\n")
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        self.process = subprocess.Popen(self.command)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Nur Python-Dateien beachten
        if not event.src_path.endswith('.py'):
            return
        
        # Ignoriere __pycache__ und versteckte Dateien
        if '__pycache__' in event.src_path or '/.venv/' in event.src_path:
            return
        
        print(f"\n📝 Änderung erkannt: {event.src_path}")
        print("⏳ Starte App neu...")
        time.sleep(0.5)  # Kurze Verzögerung für File-Save-Completion
        self.restart_app()


def main():
    # Python aus dem venv verwenden (Cross-platform)
    venv_dir = Path(__file__).parent / ".venv"
    
    # Windows vs Unix
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python3"
    
    if not venv_python.exists():
        print("❌ Fehler: .venv nicht gefunden oder Python nicht vorhanden!")
        print("Führe erst aus: python -m venv .venv")
        print(f"Erwartet: {venv_python}")
        return 1
    
    command = [str(venv_python), "-m", "src.gui.app"]
    
    # Watchdog installiert?
    try:
        import watchdog
    except ImportError:
        print("📦 Installiere watchdog für Hot Reloading...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "watchdog"])
        print("✅ watchdog installiert!\n")
    
    # Watcher starten
    event_handler = AppReloader(command)
    observer = Observer()
    
    # Überwache src/ Verzeichnis
    src_path = Path(__file__).parent / "src"
    observer.schedule(event_handler, str(src_path), recursive=True)
    observer.start()
    
    print("\n" + "="*60)
    print("👀 Hot Reloading aktiv!")
    print("   Überwache: src/")
    print("   Drücke Ctrl+C zum Beenden")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Beende Watcher...")
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    
    observer.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
