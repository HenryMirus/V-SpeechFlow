"""
History-Management für V-SpeechFlow

Speichert und verwaltet zuletzt verwendete Dateien und Einstellungen.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class HistoryManager:
    """Verwaltet History für zuletzt verwendete Dateien und Einstellungen."""
    
    MAX_HISTORY_ITEMS = 20  # Maximale Anzahl Historie-Einträge
    
    def __init__(self):
        """Initialisiert den History-Manager."""
        self.history_dir = Path.home() / ".vspeechflow" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "history.json"
        self.history_data = self._load_history()
    
    def _load_history(self) -> dict:
        """Lädt History aus Datei."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._create_empty_history()
        return self._create_empty_history()
    
    def _create_empty_history(self) -> dict:
        """Erstellt leere History-Struktur."""
        return {
            "input_files": [],
            "models": [],
            "output_paths": [],
            "last_settings": None,
            "last_session": None,
        }
    
    def _save_history(self):
        """Speichert History in Datei."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save history: {e}")
    
    def add_input_file(self, file_path: str):
        """Fügt Input-Datei zur History hinzu."""
        if not file_path or not Path(file_path).exists():
            return
        
        # Entry mit Timestamp und Metadaten
        entry = {
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "name": Path(file_path).name,
            "size_mb": round(Path(file_path).stat().st_size / 1024 / 1024, 2)
        }
        
        # Duplikate entfernen
        self.history_data["input_files"] = [
            e for e in self.history_data["input_files"] 
            if e.get("path") != file_path
        ]
        
        # Am Anfang hinzufügen
        self.history_data["input_files"].insert(0, entry)
        
        # Limit auf MAX_HISTORY_ITEMS
        self.history_data["input_files"] = \
            self.history_data["input_files"][:self.MAX_HISTORY_ITEMS]
        
        self._save_history()
    
    def add_model(self, model_path: str):
        """Fügt Modell zur History hinzu."""
        if not model_path or not Path(model_path).exists():
            return
        
        entry = {
            "path": model_path,
            "timestamp": datetime.now().isoformat(),
            "name": Path(model_path).name,
            "size_mb": round(Path(model_path).stat().st_size / 1024 / 1024, 2)
        }
        
        # Duplikate entfernen
        self.history_data["models"] = [
            e for e in self.history_data["models"]
            if e.get("path") != model_path
        ]
        
        self.history_data["models"].insert(0, entry)
        self.history_data["models"] = \
            self.history_data["models"][:self.MAX_HISTORY_ITEMS]
        
        self._save_history()
    
    def add_output_path(self, output_path: str):
        """Fügt Output-Pfad zur History hinzu."""
        if not output_path:
            return
        
        entry = {
            "path": output_path,
            "timestamp": datetime.now().isoformat(),
            "directory": str(Path(output_path).parent),
            "name": Path(output_path).name
        }
        
        # Duplikate entfernen
        self.history_data["output_paths"] = [
            e for e in self.history_data["output_paths"]
            if e.get("path") != output_path
        ]
        
        self.history_data["output_paths"].insert(0, entry)
        self.history_data["output_paths"] = \
            self.history_data["output_paths"][:self.MAX_HISTORY_ITEMS]
        
        self._save_history()
    
    def save_last_settings(self, settings: dict):
        """Speichert die letzten verwendeten Einstellungen."""
        self.history_data["last_settings"] = {
            "timestamp": datetime.now().isoformat(),
            "settings": settings
        }
        self._save_history()
    
    def save_last_session(self, session_data: dict):
        """Speichert komplette Session-Daten."""
        self.history_data["last_session"] = {
            "timestamp": datetime.now().isoformat(),
            "data": session_data
        }
        self._save_history()
    
    def get_recent_input_files(self, limit: int = 10) -> List[dict]:
        """Gibt zuletzt verwendete Input-Dateien zurück."""
        files = self.history_data.get("input_files", [])
        # Filter: Nur existierende Dateien
        return [f for f in files if Path(f["path"]).exists()][:limit]
    
    def get_recent_models(self, limit: int = 5) -> List[dict]:
        """Gibt zuletzt verwendete Modelle zurück."""
        models = self.history_data.get("models", [])
        return [m for m in models if Path(m["path"]).exists()][:limit]
    
    def get_recent_output_directories(self, limit: int = 5) -> List[str]:
        """Gibt zuletzt verwendete Output-Verzeichnisse zurück."""
        paths = self.history_data.get("output_paths", [])
        directories = list(set([p["directory"] for p in paths]))
        return [d for d in directories if Path(d).exists()][:limit]
    
    def get_last_settings(self) -> Optional[dict]:
        """Gibt die zuletzt verwendeten Einstellungen zurück."""
        last = self.history_data.get("last_settings")
        if last:
            return last.get("settings")
        return None
    
    def get_last_session(self) -> Optional[dict]:
        """Gibt die letzte Session zurück."""
        last = self.history_data.get("last_session")
        if last:
            return last.get("data")
        return None
    
    def clear_history(self):
        """Löscht komplette History."""
        self.history_data = self._create_empty_history()
        self._save_history()
    
    def remove_input_file(self, file_path: str):
        """Entfernt spezifische Datei aus History."""
        self.history_data["input_files"] = [
            e for e in self.history_data["input_files"]
            if e.get("path") != file_path
        ]
        self._save_history()
    
    def remove_model(self, model_path: str):
        """Entfernt spezifisches Modell aus History."""
        self.history_data["models"] = [
            e for e in self.history_data["models"]
            if e.get("path") != model_path
        ]
        self._save_history()
