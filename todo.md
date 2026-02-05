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
- [ ] Volume-Anzeige während Live-Recording → QProgressBar vorbereitet, benötigt Audio-Thread-Integration
- [ ] Recording-Steuerung (Start/Stop/Pause) → Buttons erstellt, benötigt Live-Recorder-Integration

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
- [ ] Diarization aktivieren/deaktivieren (Checkbox)
- [ ] **Modus wählen:**
  - Exakte Sprecheranzahl (--num-speakers)
  - Auto-Erkennung mit Min/Max (--min-speakers, --max-speakers)
- [ ] Sprecher-Zahl Input
- [ ] HuggingFace Token-Eingabe oder aus Keychain laden
- [ ] Token-Validierung vor Prozessstart

### 6. **Ausgabe-Verwaltung**
- [ ] Ausgabedatei-Pfad wählen
- [ ] Segmente mit Timestamps (-s) als Checkbox
- [ ] Plain-Text oder strukturierte Ausgabe wählen
- [ ] Vorschau/Live-Output während Transkription
- [ ] Export-Pfad validieren

### 7. **Prozessausführung**
- [ ] Start-Button mit allen Parametern
- [ ] Echtzeit-Konsolen-Output anzeigen
- [ ] Fortschrittsbalken / Status-Anzeige
- [ ] Fehlerbehandlung & aussagekräftige Fehlermeldungen
- [ ] Prozess abbrechen (Ctrl+C)
- [ ] „Done."-Meldung & Resultat-Preview

### 8. **UX-Essentials**
- [ ] Voreingestellte Profile (z.B. „Schnelles Interview", „Hochqualitäts-Meeting")
- [ ] Validierung: Pflichtfelder prüfen vor Start
- [ ] Tastenkürzel (z.B. Enter = Start, Cmd+Q = Quit)
- [ ] Logs speichern (für Debugging)

---

## **🌟 OPTIONALE FEATURES** (Neue Ideen für bessere UX)

### **Komfort & Workflow**
- [ ] History/Zuletzt verwendet (letzte Dateien, Einstellungen merken)
- [ ] Favoriten-Profile speichern & laden
- [ ] Batch-Processing (mehrere Dateien nacheinander)
- [ ] Dunkelmodus / Hell-Modus Toggle
- [ ] Vollständiger Audio-Editor mit Wellenform-Anzeige

### **Fortgeschrittene Ausgabe**
- [ ] Export-Formate: JSON, SRT (Untertitel), VTT, CSV
- [ ] Zeitformat-Optionen (HH:MM:SS vs ms)
- [ ] Speakerfarben in der Vorschau
- [ ] PDF-Export mit Formatierung
- [ ] Direkter Kopieren-Button (Text in Clipboard)

### **Qualität & Monitoring**
- [ ] Audio-Qualitäts-Check vor Transkription
- [ ] Diarization-Qualitäts-Score anzeigen
- [ ] Zeitschätzung (wie lange dauert die Verarbeitung?)
- [ ] RAM-Monitoring (modellabhängig)
- [ ] Modell-Benchmark (Geschwindigkeit testen)

### **Integration & Automatisierung**
- [ ] Transkript automatisch in Texteditor öffnen
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
- [ ] Mehrsprachige UI (Deutsch, Englisch, ...)
- [ ] Kontexthilfe / Tooltips für alle Optionen
- [ ] Auto-Update-Check für Modelle
- [ ] Installation-Wizard beim ersten Start
- [ ] Video-Tutorial / onboarding

---

## **📊 Implementierungs-Reihenfolge (empfohlen)**

**Phase 1 (MVP – Single Audio):**  
Grundgerüst → Input → Modell → Ausgabe → Start-Button → Resultat

**Phase 2 (Live + Diarization):**  
Live-Recording → Mikrofone → Diarization-UI → HF-Token

**Phase 3 (Polish):**  
Profile → History → Fehlerbehandlung → UX-Verbesserungen

**Phase 4 (Optionales):**  
Export-Formate → Batch → Visualisierung → Advanced Features
