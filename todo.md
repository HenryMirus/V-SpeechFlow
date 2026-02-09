# GUI Development - TODO Liste

## **🎯 PFLICHT-FEATURES** (direkt aus CLI ableitbar)

### 1. **Kern-UI & Projekt-Setup**
- [x] Framework auswählen (React/Electron, PyQt, Flutter, etc.) → **PyQt6 gewählt**
- [x] Grundlegende Fenster-Struktur → `src/gui/main_window.py` erstellt
- [x] Verbindung zur CLI etablieren (subprocess-Handling) → `src/gui/workers.py` mit CLIWorker

### **macOS-Kompatibilität** (Verbesserungen)
- [x] Drop-Feedback (visuelles Highlighting beim Hovern) → Green/Red Border in input_panel
- [x] Keychain-Integration für HF-TOKEN → `macos_utils.py` mit `get_hf_token_from_keychain()`
- [x] Better Error-Handling bei Permission-Denied → MessageBox-Popups mit Anleitung
- [x] HF-Token Input im Live-Tab → Mit "Aus Keychain laden"-Button

### 2. **Input-Management** 
- [x] Datei-Auswahl-Dialog → `input_panel.py` File-Tab
- [x] Drag & Drop für Audio-Dateien → `dragEnterEvent` & `dropEvent` implementiert
- [x] Audio-Format-Support anzeigen (mp3, m4a, wav, etc.) → Anzeige in UI
- [x] Live-Aufnahme-Modus (--live starten) → Live-Tab mit Recording-Controls
- [x] Mikrofon-Auswahl mit Device-Picker → ComboBox mit `refresh_devices()`
- [x] Mikrofon-Liste auslesen (--list-devices) → `utils.list_audio_devices()` erstellt
- [x] Volume-Anzeige während Live-Recording → QProgressBar mit RecordingWorker integriert
- [x] Recording-Steuerung (Start/Stop/Pause) → Vollständig integriert mit LiveRecorder

### 3. **Modell-Management**
- [x] Modell-Pfad wählen → `model_panel.py` mit File-Dialog
- [x] Modell-Vorschläge (ggml-base, ggml-small, ggml-medium, ggml-large-v3) → ComboBox mit Vorschlägen
- [x] Modell-Download-Link anzeigen (Größe: 150MB–3GB) → Info-Box mit HuggingFace Links
- [x] Modell-Validierung (existiert, korrekte Größe?) → `model_utils.validate_model_file()`

### 4. **Verarbeitung-Optionen**
- [x] Thread-Anzahl konfigurieren (Slider/Input) → `settings_panel.py` mit Slider + SpinBox
- [x] Empfehlungen je nach Mac-Modell (M1/M2/M3 + Kerne) → `system_utils.py` erkennt CPU + gibt Empfehlung
- [x] Sprache wählen (-l, default: de) → ComboBox mit de/en/fr/es/auto
- [x] Ins Englische übersetzen (--translate Checkbox) → CheckBox mit Flag
- [x] Temp-Dateien behalten (--keep-temp) → CheckBox

### 5. **Speaker Diarization**
- [x] Diarization aktivieren/deaktivieren (Checkbox) → `diarization_panel.py` mit Enable-Checkbox
- [x] **Modus wählen:** → Radio Buttons für Exact/Auto
  - Exakte Sprecheranzahl (--num-speakers) → SpinBox für Anzahl
  - Auto-Erkennung mit Min/Max (--min-speakers, --max-speakers) → Min/Max SpinBoxes
- [x] Sprecher-Zahl Input → SpinBoxes mit Validierung
- [x] HuggingFace Token-Eingabe oder aus Keychain laden → Input + Keychain-Button
- [x] Token-Validierung vor Prozessstart → `validate_settings()` und `validate_token_format()`

### 6. **Ausgabe-Verwaltung**
- [x] Ausgabedatei-Pfad wählen → `output_panel.py` mit File-Dialog und Auto-Pfad
- [x] Segmente mit Timestamps (-s) als Checkbox → Checkbox mit Preview
- [x] Plain-Text oder strukturierte Ausgabe wählen → Radio Buttons mit Live-Preview
- [x] Vorschau/Live-Output während Transkription → QTextEdit in MainWindow mit `append_output()`
- [x] Export-Pfad validieren → `validate_settings()` prüft Schreibbarkeit

### 7. **Prozessausführung**
- [x] Start-Button mit allen Parametern → `build_cli_arguments()` sammelt alle Settings
- [x] Echtzeit-Konsolen-Output anzeigen → Threading in CLIWorker für stdout/stderr
- [x] Fortschrittsbalken / Status-Anzeige → QProgressBar (indeterminate mode)
- [x] Fehlerbehandlung & aussagekräftige Fehlermeldungen → Vollständige Validierung vor Start
- [x] Prozess abbrechen (Ctrl+C) → Stop-Button mit Bestätigungs-Dialog
- [x] „Done."-Meldung & Resultat-Preview → Success/Error Messages + Auto-Open Option

### 8. **UX-Essentials**
- [x] Voreingestellte Profile (z.B. „Schnelles Interview", „Hochqualitäts-Meeting") → `profiles.py` mit 4 Default-Profilen
- [x] Validierung: Pflichtfelder prüfen vor Start → Vollständige Validierung in `start_transcription()`
- [x] Tastenkürzel (z.B. Enter = Start, Cmd+Q = Quit) → Strg+Enter, Escape, Strg+S, Strg+L, Strg+Q
- [x] Logs speichern (für Debugging) → Logging-System mit Datei in ~/.vspeechflow/logs/

---

## **🌟 OPTIONALE FEATURES** (Neue Ideen für bessere UX)

### **Komfort & Workflow**
- [x] History/Zuletzt verwendet (letzte Dateien, Einstellungen merken) → `history.py` mit HistoryManager + Menu-Bar Integration
- [x] Favoriten-Profile speichern & laden → Profile mit Favoriten-Markierung, Export/Import, Duplizieren
- [x] Batch-Processing (mehrere Dateien nacheinander) → `batch_panel.py` + `batch_window.py` mit Worker
- [x] Dunkelmodus / Hell-Modus Toggle → `theme.py` mit ThemeManager + Toggle im Settings-Menu

### **Fortgeschrittene Ausgabe**
- [ ] Export-Formate: JSON, SRT (Untertitel), VTT, CSV
- [ ] Zeitformat-Optionen (HH:MM:SS vs ms)
- [ ] Speakerfarben in der Vorschau
- [ ] PDF-Export mit Formatierung
- [ ] Direkter Kopieren-Button (Text in Clipboard)

### **Qualität & Monitoring**
- [ ] Audio-Qualitäts-Check vor Transkription
- [ ] Diarization-Qualitäts-Score anzeigen
- [x] Zeitschätzung (wie lange dauert die Verarbeitung?) → `time_estimator.py` mit dynamischer ETA, Progress % und Speed-Info
- [ ] RAM-Monitoring (modellabhängig)
- [ ] Modell-Benchmark (Geschwindigkeit testen)

### **Integration & Automatisierung**
- [x] Transkript automatisch in Texteditor öffnen
- [ ] Direkt in Notion/Obsidian/Apple Notes exportieren
- [ ] Automatische Correktion häufiger Fehler (z.B. deutsche Umlaute)
- [ ] Webhook/API für externe Systeme
- [ ] Keyboard-Hotkey für Live-Recording (backgrounded)

### **Visualisierung & Analyse**
- [ ] Sprecher-Statistik (Redezeit-Prozentual)
- [ ] Wörter-Häufigkeit-Analyse
- [ ] Suchfunktion im Transkript
- [ ] Timeline-Visualisierung mit Speaker-Timeline
- [ ] Echtzeit-Wellenform während Recording

### **Accessibility & Erwerbbarkeit**
- [x] Mehrsprachige UI (Deutsch, Englisch, ...) → `translations.py` mit DE/EN Support
- [x] Kontexthilfe / Tooltips für alle Optionen → 36 Tooltips in allen Panels
- [x] Auto-Update-Check für Modelle → `model_utils.py` mit Update-Check und Caching
- [x] Installation-Wizard beim ersten Start → `installation_wizard.py` mit History-Integration
- [x] Video-Tutorial / onboarding → `onboarding.py` mit interaktivem Tutorial

---

## **Verbesserungen**
- [ ] Intuitivere UI/UX
  - [ ] Logische Reihenfolge
  - [ ] Ausklappbare Menüs
  - [ ] Hilfe-Fenster
  - [x] Menubar
  - [x] Hell-Dunkel-Theme schalter
  - [ ] Funktionierendes Umschalten zwischen DE und EN der UI
  - [ ] Warning bei diarization mit mehr als 10 Personen, dass Mikrofon limitierender Faktor ist
- [x] Onboarding visuell fixen = automatisches "scrollen" um dem Onboarding zu folgen
- [x] Onboarding Fenster schließen = überspringnen / rausklicken und scrollen in der app ermöglichen
- [x] Batch-Fenster einblenden und testen
- [x] Progressbar fixen
- [x] ERROR im Output bei funktionierender Transkription entfernen/Fixen
- [x] Standard-System-Mikrofon automatisch auswählen
- [ ] Bad Smells entfernen, Code schön machen
- [ ] Exe erstellen, die automatisch alles buildet und die APP startet.