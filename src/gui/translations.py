"""
Mehrsprachigkeits-System für V-SpeechFlow

Bietet Übersetzungen für Deutsch und Englisch.
"""

from typing import Dict


class TranslationManager:
    """Verwaltet Übersetzungen für mehrere Sprachen."""
    
    SUPPORTED_LANGUAGES = ["de", "en"]
    
    TRANSLATIONS = {
        "de": {
            # Allgemein
            "app_title": "V-SpeechFlow - Speech to Text mit Speaker Diarization",
            "start": "Transkription starten",
            "stop": "Abbrechen",
            "close": "Schließen",
            "save": "Speichern",
            "cancel": "Abbrechen",
            "ok": "OK",
            "yes": "Ja",
            "no": "Nein",
            "browse": "Durchsuchen...",
            "apply": "Anwenden",
            "reset": "Zurücksetzen",
            "next": "Weiter",
            "back": "Zurück",
            "finish": "Fertig",
            "skip": "Überspringen",
            
            # Menu Bar
            "menu_file": "Datei",
            "menu_edit": "Bearbeiten",
            "menu_view": "Ansicht",
            "menu_tools": "Tools",
            "menu_help": "Hilfe",
            "menu_quit": "Beenden",
            "menu_new": "Neues Projekt",
            "menu_open": "Öffnen...",
            "menu_recent": "Zuletzt verwendet",
            "menu_clear_history": "Verlauf löschen",
            "menu_batch": "Stapelverarbeitung",
            "menu_profiles": "Profile verwalten",
            "menu_settings": "Einstellungen",
            "menu_theme": "Design wechseln",
            "menu_language": "Sprache",
            "menu_about": "Über V-SpeechFlow",
            "menu_documentation": "Dokumentation",
            "menu_start_onboarding": "Tutorial starten",
            
            # Installation Wizard
            "wizard_title": "V-SpeechFlow Setup-Assistent",
            "wizard_welcome": "Willkommen bei V-SpeechFlow!",
            "wizard_welcome_text": "Dieser Assistent hilft Ihnen bei der Ersteinrichtung.\nLassen Sie uns die wichtigsten Einstellungen konfigurieren.",
            "wizard_model_title": "Modell auswählen",
            "wizard_model_text": "Welches Whisper-Modell möchten Sie verwenden?\n\nGrößere Modelle sind genauer, benötigen aber mehr RAM und Zeit.",
            "wizard_model_path": "Modell-Pfad:",
            "wizard_model_download": "Noch kein Modell? Laden Sie eines herunter:",
            "wizard_token_title": "HuggingFace Token (optional)",
            "wizard_token_text": "Für Speaker Diarization benötigen Sie einen HuggingFace Token.\nSie können dies auch später einrichten.",
            "wizard_token_input": "HuggingFace Token:",
            "wizard_token_help": "Token erhalten unter: https://huggingface.co/settings/tokens",
            "wizard_preferences_title": "Ihre Präferenzen",
            "wizard_preferences_text": "Passen Sie die App nach Ihren Wünschen an:",
            "wizard_language": "Sprache:",
            "wizard_theme": "Design:",
            "wizard_threads": "CPU-Threads:",
            "wizard_auto_open": "Transkript automatisch öffnen",
            "wizard_check_updates": "Nach Modell-Updates suchen",
            "wizard_complete_title": "Setup abgeschlossen!",
            "wizard_complete_text": "V-SpeechFlow wurde erfolgreich eingerichtet.\n\nMöchten Sie jetzt ein kurzes Tutorial durchlaufen?",
            "wizard_start_tutorial": "Tutorial starten",
            "wizard_skip_tutorial": "Tutorial überspringen",
            
            # Onboarding
            "onboarding_title": "V-SpeechFlow Tutorial",
            "onboarding_welcome": "Willkommen! Lassen Sie uns die wichtigsten Funktionen kennenlernen.",
            "onboarding_step": "Schritt {current} von {total}",
            "onboarding_input_title": "Audio-Input",
            "onboarding_input_text": "Hier wählen Sie Ihre Audio-Dateien aus:\n\n• Datei-Tab: Audio-Datei auswählen\n• Live-Tab: Direkt vom Mikrofon aufnehmen\n• Unterstützte Formate: MP3, M4A, WAV, etc.",
            "onboarding_model_title": "Modell-Auswahl",
            "onboarding_model_text": "Wählen Sie ein Whisper-Modell:\n\n• base: Schnell, weniger genau (~150 MB)\n• small: Gute Balance (~500 MB)\n• medium: Sehr genau (~1.5 GB)\n• large-v3: Höchste Qualität (~3 GB)",
            "onboarding_diarization_title": "Speaker Diarization",
            "onboarding_diarization_text": "Erkennt verschiedene Sprecher im Audio:\n\n• Aktivieren Sie das Häkchen\n• Geben Sie Sprecher-Anzahl an\n• Benötigt HuggingFace Token",
            "onboarding_profiles_title": "Profile",
            "onboarding_profiles_text": "Speichern Sie häufige Konfigurationen:\n\n• Schnelles Interview\n• Meeting mit Diarization\n• Hochqualitäts-Transkription\n• Eigene Profile erstellen",
            "onboarding_transcription_title": "Transkription starten",
            "onboarding_transcription_text": "Bereit für die Transkription:\n\n1. Alle Einstellungen prüfen\n2. 'Transkription starten' klicken\n3. Fortschritt live verfolgen\n4. Ergebnis wird automatisch gespeichert",
            "onboarding_complete": "Tutorial abgeschlossen!\n\nSie können dieses Tutorial jederzeit über das\nHilfe-Menü erneut starten.",
            
            # Input Panel
            "input_title": "Audio-Input",
            "input_file_tab": "Datei",
            "input_live_tab": "Live-Aufnahme",
            "input_file_label": "Audio-Datei:",
            "input_file_select": "Datei auswählen",
            "input_drag_drop": "...oder Datei per Drag & Drop hier ablegen",
            "input_supported_formats": "Unterstützte Formate: MP3, M4A, WAV, FLAC, OGG, OPUS",
            "input_device_label": "Mikrofon:",
            "input_refresh_devices": "Aktualisieren",
            "input_recording": "Aufnahme läuft...",
            "input_start_recording": "Aufnahme starten",
            "input_stop_recording": "Aufnahme stoppen",
            "input_volume": "Lautstärke:",
            
            # Model Panel
            "model_title": "Modell-Auswahl",
            "model_path_label": "Modell-Pfad:",
            "model_preset_label": "Vorschlag:",
            "model_info": "Modell-Info",
            "model_info_text": "**Empfohlene Modelle:**\n\n• ggml-base: ~150 MB (schnell)\n• ggml-small: ~500 MB (ausgeglichen)\n• ggml-medium: ~1.5 GB (genau)\n• ggml-large-v3: ~3 GB (beste Qualität)\n\nDownload: https://huggingface.co/ggerganov/whisper.cpp",
            
            # Settings Panel
            "settings_title": "Verarbeitungsoptionen",
            "settings_threads_label": "CPU-Threads:",
            "settings_language_label": "Sprache:",
            "settings_translate": "Ins Englische übersetzen",
            "settings_keep_temp": "Temporäre Dateien behalten",
            "settings_system_info": "System-Info:",
            
            # Diarization Panel
            "diarization_title": "Speaker Diarization",
            "diarization_enable": "Diarization aktivieren",
            "diarization_mode_exact": "Exakte Anzahl",
            "diarization_mode_auto": "Automatisch",
            "diarization_num_speakers": "Anzahl Sprecher:",
            "diarization_min_speakers": "Min. Sprecher:",
            "diarization_max_speakers": "Max. Sprecher:",
            "diarization_token_label": "HuggingFace Token:",
            "diarization_load_keychain": "Aus Keychain laden",
            "diarization_save_token": "Token speichern",
            "diarization_info": "ℹ️ Diarization erkennt verschiedene Sprecher im Audio und kennzeichnet diese im Transkript.",
            
            # Output Panel
            "output_title": "Ausgabe",
            "output_path_label": "Ausgabepfad:",
            "output_auto_path": "Automatisch",
            "output_segments": "Timestamps hinzufügen",
            "output_format_plain": "Plain-Text",
            "output_format_structured": "Strukturiert",
            "output_preview": "Vorschau:",
            
            # Batch Panel
            "batch_title": "Stapelverarbeitung",
            "batch_add_files": "Dateien hinzufügen",
            "batch_remove_selected": "Ausgewählte entfernen",
            "batch_clear_all": "Alle entfernen",
            "batch_start": "Batch-Verarbeitung starten",
            "batch_status": "Status:",
            "batch_progress": "Fortschritt:",
            
            # Status & Messages
            "status_ready": "Bereit.",
            "status_processing": "Verarbeitung läuft...",
            "status_completed": "Transkription abgeschlossen!",
            "status_error": "Fehler aufgetreten.",
            "status_stopped": "Verarbeitung abgebrochen.",
            
            "error_no_input": "Fehler: Keine Audio-Datei ausgewählt!",
            "error_no_model": "Fehler: Kein Modell ausgewählt!",
            "error_model_not_found": "Fehler: Modell nicht gefunden!",
            "error_invalid_token": "Fehler: Ungültiger HuggingFace Token!",
            "error_output_path": "Fehler: Ungültiger Ausgabepfad!",
            "error_process": "Fehler beim Starten der Transkription.",
            
            "success_transcription": "Transkription erfolgreich abgeschlossen!",
            "success_file_saved": "Datei gespeichert unter:\n{path}",
            "success_open_file": "Datei öffnen?",
            
            "confirm_stop_title": "Verarbeitung abbrechen?",
            "confirm_stop_message": "Möchten Sie die laufende Verarbeitung wirklich abbrechen?",
            "confirm_overwrite_title": "Datei überschreiben?",
            "confirm_overwrite_message": "Die Datei existiert bereits. Überschreiben?",
            
            # Tooltips
            "tooltip_input_file": "Wählen Sie eine Audio-Datei zur Transkription aus",
            "tooltip_input_live": "Nehmen Sie Audio direkt vom Mikrofon auf",
            "tooltip_model_path": "Pfad zum Whisper-Modell (.bin Datei)",
            "tooltip_threads": "Anzahl CPU-Threads für die Verarbeitung (mehr = schneller, aber mehr RAM)",
            "tooltip_language": "Sprache des Audio-Materials (auto = automatische Erkennung)",
            "tooltip_translate": "Übersetzt das Transkript ins Englische",
            "tooltip_diarization": "Erkennt und kennzeichnet verschiedene Sprecher",
            "tooltip_hf_token": "Benötigt für Speaker Diarization - erhältlich auf HuggingFace",
            "tooltip_segments": "Fügt Zeitstempel zu jedem Segment hinzu",
            "tooltip_output_path": "Wo soll das Transkript gespeichert werden?",
        },
        
        "en": {
            # General
            "app_title": "V-SpeechFlow - Speech to Text with Speaker Diarization",
            "start": "Start Transcription",
            "stop": "Cancel",
            "close": "Close",
            "save": "Save",
            "cancel": "Cancel",
            "ok": "OK",
            "yes": "Yes",
            "no": "No",
            "browse": "Browse...",
            "apply": "Apply",
            "reset": "Reset",
            "next": "Next",
            "back": "Back",
            "finish": "Finish",
            "skip": "Skip",
            
            # Menu Bar
            "menu_file": "File",
            "menu_edit": "Edit",
            "menu_view": "View",
            "menu_tools": "Tools",
            "menu_help": "Help",
            "menu_quit": "Quit",
            "menu_new": "New Project",
            "menu_open": "Open...",
            "menu_recent": "Recent Files",
            "menu_clear_history": "Clear History",
            "menu_batch": "Batch Processing",
            "menu_profiles": "Manage Profiles",
            "menu_settings": "Settings",
            "menu_theme": "Toggle Theme",
            "menu_language": "Language",
            "menu_about": "About V-SpeechFlow",
            "menu_documentation": "Documentation",
            "menu_start_onboarding": "Start Tutorial",
            
            # Installation Wizard
            "wizard_title": "V-SpeechFlow Setup Wizard",
            "wizard_welcome": "Welcome to V-SpeechFlow!",
            "wizard_welcome_text": "This wizard will help you with the initial setup.\nLet's configure the most important settings.",
            "wizard_model_title": "Choose Model",
            "wizard_model_text": "Which Whisper model would you like to use?\n\nLarger models are more accurate but require more RAM and time.",
            "wizard_model_path": "Model Path:",
            "wizard_model_download": "Don't have a model yet? Download one here:",
            "wizard_token_title": "HuggingFace Token (optional)",
            "wizard_token_text": "For Speaker Diarization you need a HuggingFace token.\nYou can also set this up later.",
            "wizard_token_input": "HuggingFace Token:",
            "wizard_token_help": "Get your token at: https://huggingface.co/settings/tokens",
            "wizard_preferences_title": "Your Preferences",
            "wizard_preferences_text": "Customize the app to your liking:",
            "wizard_language": "Language:",
            "wizard_theme": "Theme:",
            "wizard_threads": "CPU Threads:",
            "wizard_auto_open": "Automatically open transcript",
            "wizard_check_updates": "Check for model updates",
            "wizard_complete_title": "Setup Complete!",
            "wizard_complete_text": "V-SpeechFlow has been successfully set up.\n\nWould you like to go through a quick tutorial now?",
            "wizard_start_tutorial": "Start Tutorial",
            "wizard_skip_tutorial": "Skip Tutorial",
            
            # Onboarding
            "onboarding_title": "V-SpeechFlow Tutorial",
            "onboarding_welcome": "Welcome! Let's explore the most important features.",
            "onboarding_step": "Step {current} of {total}",
            "onboarding_input_title": "Audio Input",
            "onboarding_input_text": "Here you select your audio files:\n\n• File Tab: Choose audio file\n• Live Tab: Record directly from microphone\n• Supported formats: MP3, M4A, WAV, etc.",
            "onboarding_model_title": "Model Selection",
            "onboarding_model_text": "Choose a Whisper model:\n\n• base: Fast, less accurate (~150 MB)\n• small: Good balance (~500 MB)\n• medium: Very accurate (~1.5 GB)\n• large-v3: Highest quality (~3 GB)",
            "onboarding_diarization_title": "Speaker Diarization",
            "onboarding_diarization_text": "Detects different speakers in audio:\n\n• Enable the checkbox\n• Specify number of speakers\n• Requires HuggingFace token",
            "onboarding_profiles_title": "Profiles",
            "onboarding_profiles_text": "Save frequent configurations:\n\n• Quick Interview\n• Meeting with Diarization\n• High-quality Transcription\n• Create custom profiles",
            "onboarding_transcription_title": "Start Transcription",
            "onboarding_transcription_text": "Ready to transcribe:\n\n1. Review all settings\n2. Click 'Start Transcription'\n3. Monitor progress live\n4. Result is saved automatically",
            "onboarding_complete": "Tutorial complete!\n\nYou can restart this tutorial anytime from the\nHelp menu.",
            
            # Input Panel
            "input_title": "Audio Input",
            "input_file_tab": "File",
            "input_live_tab": "Live Recording",
            "input_file_label": "Audio File:",
            "input_file_select": "Select File",
            "input_drag_drop": "...or drag & drop file here",
            "input_supported_formats": "Supported formats: MP3, M4A, WAV, FLAC, OGG, OPUS",
            "input_device_label": "Microphone:",
            "input_refresh_devices": "Refresh",
            "input_recording": "Recording...",
            "input_start_recording": "Start Recording",
            "input_stop_recording": "Stop Recording",
            "input_volume": "Volume:",
            
            # Model Panel
            "model_title": "Model Selection",
            "model_path_label": "Model Path:",
            "model_preset_label": "Preset:",
            "model_info": "Model Info",
            "model_info_text": "**Recommended Models:**\n\n• ggml-base: ~150 MB (fast)\n• ggml-small: ~500 MB (balanced)\n• ggml-medium: ~1.5 GB (accurate)\n• ggml-large-v3: ~3 GB (best quality)\n\nDownload: https://huggingface.co/ggerganov/whisper.cpp",
            
            # Settings Panel
            "settings_title": "Processing Options",
            "settings_threads_label": "CPU Threads:",
            "settings_language_label": "Language:",
            "settings_translate": "Translate to English",
            "settings_keep_temp": "Keep temporary files",
            "settings_system_info": "System Info:",
            
            # Diarization Panel
            "diarization_title": "Speaker Diarization",
            "diarization_enable": "Enable Diarization",
            "diarization_mode_exact": "Exact Count",
            "diarization_mode_auto": "Automatic",
            "diarization_num_speakers": "Number of Speakers:",
            "diarization_min_speakers": "Min. Speakers:",
            "diarization_max_speakers": "Max. Speakers:",
            "diarization_token_label": "HuggingFace Token:",
            "diarization_load_keychain": "Load from Keychain",
            "diarization_save_token": "Save Token",
            "diarization_info": "ℹ️ Diarization detects different speakers in audio and labels them in the transcript.",
            
            # Output Panel
            "output_title": "Output",
            "output_path_label": "Output Path:",
            "output_auto_path": "Automatic",
            "output_segments": "Add Timestamps",
            "output_format_plain": "Plain Text",
            "output_format_structured": "Structured",
            "output_preview": "Preview:",
            
            # Batch Panel
            "batch_title": "Batch Processing",
            "batch_add_files": "Add Files",
            "batch_remove_selected": "Remove Selected",
            "batch_clear_all": "Remove All",
            "batch_start": "Start Batch Processing",
            "batch_status": "Status:",
            "batch_progress": "Progress:",
            
            # Status & Messages
            "status_ready": "Ready.",
            "status_processing": "Processing...",
            "status_completed": "Transcription completed!",
            "status_error": "Error occurred.",
            "status_stopped": "Processing cancelled.",
            
            "error_no_input": "Error: No audio file selected!",
            "error_no_model": "Error: No model selected!",
            "error_model_not_found": "Error: Model not found!",
            "error_invalid_token": "Error: Invalid HuggingFace token!",
            "error_output_path": "Error: Invalid output path!",
            "error_process": "Error starting transcription.",
            
            "success_transcription": "Transcription completed successfully!",
            "success_file_saved": "File saved at:\n{path}",
            "success_open_file": "Open file?",
            
            "confirm_stop_title": "Cancel Processing?",
            "confirm_stop_message": "Do you really want to cancel the running process?",
            "confirm_overwrite_title": "Overwrite File?",
            "confirm_overwrite_message": "The file already exists. Overwrite?",
            
            # Tooltips
            "tooltip_input_file": "Select an audio file for transcription",
            "tooltip_input_live": "Record audio directly from microphone",
            "tooltip_model_path": "Path to the Whisper model (.bin file)",
            "tooltip_threads": "Number of CPU threads for processing (more = faster, but more RAM)",
            "tooltip_language": "Language of the audio material (auto = automatic detection)",
            "tooltip_translate": "Translates the transcript to English",
            "tooltip_diarization": "Detects and labels different speakers",
            "tooltip_hf_token": "Required for Speaker Diarization - available on HuggingFace",
            "tooltip_segments": "Adds timestamps to each segment",
            "tooltip_output_path": "Where should the transcript be saved?",
        }
    }
    
    def __init__(self, language: str = "de"):
        """Initialisiert den Translation-Manager."""
        self.current_language = language if language in self.SUPPORTED_LANGUAGES else "de"
    
    def set_language(self, language: str):
        """Setzt die aktuelle Sprache."""
        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language
    
    def get(self, key: str, **kwargs) -> str:
        """
        Gibt übersetzten Text zurück.
        
        Args:
            key: Schlüssel für den Text
            **kwargs: Optionale Formatierungs-Parameter
        """
        translation = self.TRANSLATIONS.get(self.current_language, {}).get(key, key)
        
        # Formatierung anwenden wenn Parameter übergeben
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError:
                pass  # Falls Platzhalter fehlen, Original zurückgeben
        
        return translation
    
    def get_current_language(self) -> str:
        """Gibt die aktuelle Sprache zurück."""
        return self.current_language
    
    def get_supported_languages(self) -> list:
        """Gibt Liste der unterstützten Sprachen zurück."""
        return self.SUPPORTED_LANGUAGES.copy()


# Globale Instanz
_translation_manager = TranslationManager()


def tr(key: str, **kwargs) -> str:
    """
    Shortcut-Funktion für Übersetzungen.
    
    Usage:
        from .translations import tr
        text = tr("start")
    """
    return _translation_manager.get(key, **kwargs)


def set_language(language: str):
    """Setzt die globale Sprache."""
    _translation_manager.set_language(language)


def get_translation_manager() -> TranslationManager:
    """Gibt die globale TranslationManager-Instanz zurück."""
    return _translation_manager
