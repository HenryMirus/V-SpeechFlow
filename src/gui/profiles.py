"""
Profile-Management für V-SpeechFlow

Ermöglicht Speichern/Laden von Settings-Profilen.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ProfileManager:
    """Verwaltet Profile für GUI-Einstellungen."""
    
    def __init__(self):
        """Initialisiert den Profile-Manager."""
        self.profiles_dir = Path.home() / ".vspeechflow" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # User-Profile Datei
        self.user_profiles_file = self.profiles_dir / "user_profiles.json"
        
        # Vordefinierte Profile
        self.default_profiles = self._create_default_profiles()
    
    def _create_default_profiles(self) -> Dict[str, dict]:
        """Erstellt vordefinierte Standard-Profile."""
        return {
            "Schnelles Interview": {
                "description": "Optimiert für schnelle Verarbeitung, 2 Sprecher",
                "settings": {
                    "threads": 6,
                    "language": "de",
                    "translate": False,
                    "keep_temp": False,
                },
                "diarization": {
                    "enabled": True,
                    "mode": "exact",
                    "num_speakers": 2,
                    "min_speakers": None,
                    "max_speakers": None,
                    "hf_token": None,
                },
                "output": {
                    "output_path": None,
                    "timestamps": True,
                    "format": "structured",
                    "auto_open": True,
                }
            },
            "Hochqualitäts-Meeting": {
                "description": "Beste Qualität, 3-6 Sprecher, mit Timestamps",
                "settings": {
                    "threads": 8,
                    "language": "de",
                    "translate": False,
                    "keep_temp": False,
                },
                "diarization": {
                    "enabled": True,
                    "mode": "auto",
                    "num_speakers": None,
                    "min_speakers": 3,
                    "max_speakers": 6,
                    "hf_token": None,
                },
                "output": {
                    "output_path": None,
                    "timestamps": True,
                    "format": "structured",
                    "auto_open": True,
                }
            },
            "Einfache Transkription": {
                "description": "Basis-Transkription ohne Diarization",
                "settings": {
                    "threads": 6,
                    "language": "de",
                    "translate": False,
                    "keep_temp": False,
                },
                "diarization": {
                    "enabled": False,
                    "mode": None,
                    "num_speakers": None,
                    "min_speakers": None,
                    "max_speakers": None,
                    "hf_token": None,
                },
                "output": {
                    "output_path": None,
                    "timestamps": False,
                    "format": "plain",
                    "auto_open": True,
                }
            },
            "Englisch → Deutsch": {
                "description": "Englisches Audio mit deutscher Übersetzung",
                "settings": {
                    "threads": 8,
                    "language": "en",
                    "translate": True,
                    "keep_temp": False,
                },
                "diarization": {
                    "enabled": False,
                    "mode": None,
                    "num_speakers": None,
                    "min_speakers": None,
                    "max_speakers": None,
                    "hf_token": None,
                },
                "output": {
                    "output_path": None,
                    "timestamps": True,
                    "format": "structured",
                    "auto_open": True,
                }
            }
        }
    
    def get_all_profiles(self) -> Dict[str, dict]:
        """
        Gibt alle verfügbaren Profile zurück (Default + User).
        
        Returns:
            Dict mit allen Profilen
        """
        profiles = self.default_profiles.copy()
        
        # User-Profile laden
        user_profiles = self.load_user_profiles()
        profiles.update(user_profiles)
        
        return profiles
    
    def get_profile(self, name: str) -> Optional[dict]:
        """
        Lädt ein spezifisches Profil.
        
        Args:
            name: Name des Profils
        
        Returns:
            Profil-Dict oder None
        """
        all_profiles = self.get_all_profiles()
        return all_profiles.get(name)
    
    def save_profile(self, name: str, profile: dict) -> bool:
        """
        Speichert ein User-Profil.
        
        Args:
            name: Name des Profils
            profile: Profil-Daten
        
        Returns:
            True wenn erfolgreich
        """
        try:
            # Lade existierende User-Profile
            user_profiles = self.load_user_profiles()
            
            # Füge Metadaten hinzu
            profile['created_at'] = datetime.now().isoformat()
            profile['is_default'] = False
            
            # Speichere
            user_profiles[name] = profile
            
            with open(self.user_profiles_file, 'w', encoding='utf-8') as f:
                json.dump(user_profiles, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Profils: {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """
        Löscht ein User-Profil (Default-Profile können nicht gelöscht werden).
        
        Args:
            name: Name des Profils
        
        Returns:
            True wenn erfolgreich
        """
        if name in self.default_profiles:
            return False  # Default-Profile können nicht gelöscht werden
        
        try:
            user_profiles = self.load_user_profiles()
            
            if name in user_profiles:
                del user_profiles[name]
                
                with open(self.user_profiles_file, 'w', encoding='utf-8') as f:
                    json.dump(user_profiles, f, indent=2, ensure_ascii=False)
                
                return True
            return False
        except Exception as e:
            print(f"Fehler beim Löschen des Profils: {e}")
            return False
    
    def load_user_profiles(self) -> Dict[str, dict]:
        """
        Lädt alle User-Profile.
        
        Returns:
            Dict mit User-Profilen
        """
        if not self.user_profiles_file.exists():
            return {}
        
        try:
            with open(self.user_profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der User-Profile: {e}")
            return {}
    
    def get_profile_names(self) -> List[str]:
        """
        Gibt alle verfügbaren Profil-Namen zurück.
        
        Returns:
            Liste von Profil-Namen
        """
        return list(self.get_all_profiles().keys())
    
    def is_default_profile(self, name: str) -> bool:
        """
        Prüft ob ein Profil ein Default-Profil ist.
        
        Args:
            name: Name des Profils
        
        Returns:
            True wenn Default-Profil
        """
        return name in self.default_profiles
