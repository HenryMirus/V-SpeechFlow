"""
Profile-Management für V-SpeechFlow

Ermöglicht Speichern/Laden von Settings-Profilen.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfileManager:
    """Verwaltet Profile für GUI-Einstellungen."""
    
    def __init__(self):
        """Initialisiert den Profile-Manager."""
        self.profiles_dir = Path.home() / "V-SpeechFlow" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # User-Profile Datei
        self.user_profiles_file = self.profiles_dir / "user_profiles.json"
        
        # Vordefinierte Profile
        self.default_profiles = self._create_default_profiles()
    
    def _create_default_profiles(self) -> Dict[str, dict]:
        """Erstellt vordefinierte Standard-Profile."""
        # Dynamischer Pfad zum models Ordner
        models_dir = Path(__file__).parent.parent.parent / "models" / "ggml-small.bin"
        
        return {
            "Leiterrunde": {
                "description": "Optimiert für Meetings mit mehreren Sprechern",
                "model": {
                    "model_path": str(models_dir),
                },
                "settings": {
                    "threads": 6,
                    "language": "de",
                    "translate": False,
                    "keep_temp": False,
                },
                "diarization": {
                    "enabled": True,
                    "mode": "auto",
                    "num_speakers": None,
                    "min_speakers": 1,
                    "max_speakers": 50,
                    "hf_token": None,
                },
                "output": {
                    "output_path": os.path.expanduser("~/Desktop/Leiterrunde_Transkripte"),
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
            logger.error(f"Failed to save profile: {e}")
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
            logger.error(f"Failed to delete profile: {e}")
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
            logger.error(f"Failed to load user profiles: {e}")
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
    
    def mark_as_favorite(self, name: str) -> bool:
        """
        Markiert ein Profil als Favorit.
        
        Args:
            name: Name des Profils
        
        Returns:
            True wenn erfolgreich
        """
        try:
            user_profiles = self.load_user_profiles()
            
            if name in user_profiles:
                user_profiles[name]['is_favorite'] = True
                
                with open(self.user_profiles_file, 'w', encoding='utf-8') as f:
                    json.dump(user_profiles, f, indent=2, ensure_ascii=False)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark profile as favorite: {e}")
            return False
    
    def unmark_as_favorite(self, name: str) -> bool:
        """
        Entfernt Favoriten-Markierung von einem Profil.
        
        Args:
            name: Name des Profils
        
        Returns:
            True wenn erfolgreich
        """
        try:
            user_profiles = self.load_user_profiles()
            
            if name in user_profiles:
                user_profiles[name]['is_favorite'] = False
                
                with open(self.user_profiles_file, 'w', encoding='utf-8') as f:
                    json.dump(user_profiles, f, indent=2, ensure_ascii=False)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unmark profile as favorite: {e}")
            return False
    
    def get_favorites(self) -> List[str]:
        """
        Gibt alle als Favorit markierten Profile zurück.
        
        Returns:
            Liste von Favoriten-Profil-Namen
        """
        user_profiles = self.load_user_profiles()
        return [
            name for name, profile in user_profiles.items()
            if profile.get('is_favorite', False)
        ]
    
    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """
        Dupliziert ein Profil.
        
        Args:
            source_name: Name des Quell-Profils
            new_name: Name des neuen Profils
        
        Returns:
            True wenn erfolgreich
        """
        source_profile = self.get_profile(source_name)
        
        if not source_profile:
            return False
        
        # Kopie erstellen
        new_profile = {
            'description': f"Kopie von {source_name}",
            'model': source_profile.get('model', {}).copy(),
            'settings': source_profile.get('settings', {}).copy(),
            'diarization': source_profile.get('diarization', {}).copy(),
            'output': source_profile.get('output', {}).copy(),
        }
        
        return self.save_profile(new_name, new_profile)
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """
        Exportiert ein Profil als JSON-Datei.
        
        Args:
            name: Name des Profils
            export_path: Pfad zur Export-Datei
        
        Returns:
            True wenn erfolgreich
        """
        profile = self.get_profile(name)
        
        if not profile:
            return False
        
        try:
            export_data = {
                'name': name,
                'profile': profile,
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to export profile: {e}")
            return False
    
    def import_profile(self, import_path: Path) -> tuple[bool, Optional[str]]:
        """
        Importiert ein Profil aus einer JSON-Datei.
        
        Args:
            import_path: Pfad zur Import-Datei
        
        Returns:
            Tuple (success: bool, profile_name: str or None)
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            name = import_data.get('name')
            profile = import_data.get('profile')
            
            if not name or not profile:
                return False, None
            
            # Wenn Profil bereits existiert, füge Suffix hinzu
            original_name = name
            counter = 1
            while name in self.get_all_profiles():
                name = f"{original_name} ({counter})"
                counter += 1
            
            if self.save_profile(name, profile):
                return True, name
            return False, None
        except Exception as e:
            logger.error(f"Failed to import profile: {e}")
            return False, None

