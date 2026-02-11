"""
History-Management für V-SpeechFlow

Speichert und verwaltet zuletzt verwendete Dateien und Einstellungen.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HistoryManager:
    """Verwaltet History für zuletzt verwendete Dateien und Einstellungen."""
    
    MAX_HISTORY_ITEMS = 20  # Maximale Anzahl Historie-Einträge
    _instance = None

    @classmethod
    def get_instance(cls) -> "HistoryManager":
        """Gibt die Singleton-Instanz des HistoryManagers zurück."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialisiert den History-Manager."""
        # History im Projekt-Ordner speichern (neben models/)
        # Pfad: V-Speech/history/history.json
        project_root = Path(__file__).parent.parent.parent
        self.history_dir = project_root / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "history.json"
        logger.info(f"History manager initialized. File: {self.history_file}")
        self.history_data = self._load_history()
    
    def _load_history(self) -> dict:
        """Lädt History aus Datei."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Datei existiert aber ist korrupt - erstelle neu
                history = self._create_empty_history()
                self._save_history_internal(history)
                return history
        # Datei existiert nicht - erstelle sie
        history = self._create_empty_history()
        self._save_history_internal(history)
        return history
    
    def _create_empty_history(self) -> dict:
        """Erstellt leere History-Struktur."""
        return {
            "input_files": [],
            "models": [],
            "output_paths": [],
            "last_session": None,  # Enthält komplette Session inkl. Profil
            "initial_config": None,  # Nur beim ersten Start nach Wizard
            "app_settings": {
                "first_run": True,
                "wizard_completed": False,
                "onboarding_completed": False,
                "last_wizard_version": None,
            },
            "user_preferences": {
                "ui_language": "de",
                "preferred_theme": "light",
                "show_tooltips": True,
                "check_model_updates": True,
            }
        }
    
    def _save_history(self):
        """Speichert History in Datei."""
        self._save_history_internal(self.history_data)
    
    def _save_history_internal(self, data: dict):
        """Interne Methode zum Speichern von History-Daten."""
        import os
        try:
            # Stelle sicher dass das Verzeichnis existiert
            self.history_dir.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()  # Puffer leeren
                os.fsync(f.fileno())  # Sofort auf Festplatte schreiben
            logger.debug(f"History saved to: {self.history_file}")
        except IOError as e:
            logger.error(f"Could not save history: {e}")
    
    def _add_to_list(self, list_key: str, entry: dict, match_key: str = "path"):
        """
        Generische Methode um einen Eintrag zu einer History-Liste hinzuzufügen.
        
        Args:
            list_key: Schlüssel in history_data (z.B. 'input_files')
            entry: Dict mit den Eintrags-Daten
            match_key: Schlüssel zum Duplikat-Abgleich
        """
        match_value = entry.get(match_key)
        
        # Duplikate entfernen
        self.history_data[list_key] = [
            e for e in self.history_data[list_key]
            if e.get(match_key) != match_value
        ]
        
        # Am Anfang hinzufügen
        self.history_data[list_key].insert(0, entry)
        
        # Limit auf MAX_HISTORY_ITEMS
        self.history_data[list_key] = \
            self.history_data[list_key][:self.MAX_HISTORY_ITEMS]
        
        self._save_history()
    
    def add_input_file(self, file_path: str):
        """Fügt Input-Datei zur History hinzu."""
        if not file_path or not Path(file_path).exists():
            return
        
        entry = {
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "name": Path(file_path).name,
            "size_mb": round(Path(file_path).stat().st_size / 1024 / 1024, 2)
        }
        self._add_to_list("input_files", entry)
    
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
        self._add_to_list("models", entry)
    
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
        self._add_to_list("output_paths", entry)
    
    def save_last_session(self, session_data: dict, profile_name: Optional[str] = None):
        """
        Speichert komplette Session-Daten inkl. aktivem Profil.
        
        Args:
            session_data: Dictionary mit allen Session-Daten
            profile_name: Name des aktiven Profils (None = kein Profil)
        """
        self.history_data["last_session"] = {
            "timestamp": datetime.now().isoformat(),
            "profile_name": profile_name,
            "data": session_data
        }
        self._save_history()
        logger.info(f"Last session saved (Profile: {profile_name or 'None'})")
    
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
    
    def get_last_session(self) -> Optional[dict]:
        """
        Gibt die letzte Session zurück.
        
        Returns:
            Dictionary mit 'data' und 'profile_name'
        """
        return self.history_data.get("last_session")
    
    def get_last_session_data(self) -> Optional[dict]:
        """Gibt nur die Session-Daten zurück (ohne Metadaten)."""
        last = self.history_data.get("last_session")
        if last:
            return last.get("data")
        return None
    
    def get_last_session_profile(self) -> Optional[str]:
        """Gibt den Namen des zuletzt aktiven Profils zurück."""
        last = self.history_data.get("last_session")
        if last:
            return last.get("profile_name")
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
    
    # ===== App Settings Management =====
    
    def is_first_run(self) -> bool:
        """Prüft ob die App zum ersten Mal gestartet wird."""
        return self.history_data.get("app_settings", {}).get("first_run", True)
    
    def is_wizard_completed(self) -> bool:
        """Prüft ob der Setup-Wizard abgeschlossen wurde."""
        return self.history_data.get("app_settings", {}).get("wizard_completed", False)
    
    def is_onboarding_completed(self) -> bool:
        """Prüft ob das Onboarding abgeschlossen wurde."""
        return self.history_data.get("app_settings", {}).get("onboarding_completed", False)
    
    def mark_wizard_completed(self, version: str = "1.0"):
        """Markiert den Setup-Wizard als abgeschlossen."""
        if "app_settings" not in self.history_data:
            self.history_data["app_settings"] = {}
        self.history_data["app_settings"]["first_run"] = False
        self.history_data["app_settings"]["wizard_completed"] = True
        self.history_data["app_settings"]["last_wizard_version"] = version
        self._save_history()
    
    def mark_onboarding_completed(self, complete: bool = True):
        """Markiert das Onboarding als abgeschlossen."""
        if "app_settings" not in self.history_data:
            self.history_data["app_settings"] = {}
        self.history_data["app_settings"]["onboarding_completed"] = complete
        self._save_history()
    
    def save_app_setting(self, key: str, value):
        """Speichert eine beliebige App-Einstellung."""
        if "app_settings" not in self.history_data:
            self.history_data["app_settings"] = {}
        self.history_data["app_settings"][key] = value
        self._save_history()
    
    def get_app_setting(self, key: str, default=None):
        """Gibt eine App-Einstellung zurück."""
        return self.history_data.get("app_settings", {}).get(key, default)
    
    def get_all_app_settings(self) -> dict:
        """Gibt alle App-Einstellungen zurück."""
        return self.history_data.get("app_settings", {})
    
    def save_user_preference(self, key: str, value):
        """Speichert eine User-Preference."""
        if "user_preferences" not in self.history_data:
            self.history_data["user_preferences"] = {}
        self.history_data["user_preferences"][key] = value
        self._save_history()
    
    def get_user_preference(self, key: str, default=None):
        """Gibt eine User-Preference zurück."""
        return self.history_data.get("user_preferences", {}).get(key, default)
    
    def get_all_user_preferences(self) -> dict:
        """Gibt alle User-Preferences zurück."""
        return self.history_data.get("user_preferences", {})
    
    def save_initial_config(self, config: dict):
        """
        Speichert die Initial-Konfiguration aus dem Installation-Wizard.
        Diese wird NUR beim ersten Start nach Wizard-Abschluss geladen.
        
        Args:
            config: Dictionary mit allen Wizard-Einstellungen
        """
        self.history_data["initial_config"] = {
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "applied": False  # Flag ob bereits angewendet
        }
        self._save_history()
        logger.info(f"Initial config saved: {list(config.keys())}")
    
    def get_initial_config(self) -> Optional[dict]:
        """
        Gibt die Initial-Konfiguration zurück, wenn noch nicht angewendet.
        
        Returns:
            Dictionary mit Wizard-Konfiguration oder None
        """
        initial = self.history_data.get("initial_config")
        if initial and not initial.get("applied", False):
            return initial.get("config")
        return None
    
    def mark_initial_config_applied(self):
        """Markiert initial_config als angewendet."""
        if self.history_data.get("initial_config"):
            self.history_data["initial_config"]["applied"] = True
            self._save_history()
            logger.info("Initial config marked as applied")
