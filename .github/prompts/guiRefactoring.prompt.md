# Plan: GUI Code-Smell-Bereinigung & Refactoring

Umfassendes Refactoring des `src/gui/`-Moduls: Entfernung von Redundanzen, Dead Code, Magic Numbers, hardcodierten Strings und Zerlegung der God Class `MainWindow` in handhabbare Controller-Klassen. Zwei Bugs (Tab-Mismatch, fehlender f-String) werden ebenfalls gefixt. Ziel: sauberer, wartbarer, verständlicher Code ohne Funktionsänderung.

---

## Phase 1 — Infrastruktur & Shared Utilities

### Schritt 1.1: Neue Datei `src/gui/constants.py` erstellen
- Zentrale Konstanten für alle Magic Numbers:
  - Farben: `COLOR_SUCCESS = "#4CAF50"`, `COLOR_ERROR = "#f44336"`, etc.
  - Font-Größen: `SECTION_TITLE_FONT_SIZE = 13`
  - Timings: `ONBOARDING_DELAY_MS = 500`, `MODEL_CHECK_DELAY_MS = 3000`, `STATUS_TIMER_MS = 5000`, etc.
  - Window-Dimensionen: `MAIN_WINDOW_SIZE = (1400, 900)`, `WIZARD_SIZE = (700, 500)`, etc.
  - `SUPPORTED_AUDIO_FORMATS = ("mp3", "m4a", "wav", "flac", "ogg")` (aktuell doppelt in `batch_panel.py:37` und `input_panel.py:46`)

### Schritt 1.2: UI-Helper-Funktionen in `src/gui/utils.py` erweitern
- `create_section_title(text: str) -> QLabel` — ersetzt 8+ identische 5-Zeilen-Blöcke in `model_panel.py`, `diarization_panel.py`, `output_panel.py`, `settings_panel.py`
- `create_hint_label(text: str) -> QLabel` — ersetzt 10+ identische 3-Zeilen-Blöcke
- `create_action_button(text, color, ...) -> QPushButton` — ersetzt duplizierte Start/Stop-Button-Styles

---

## Phase 2 — Dead Code entfernen

### Schritt 2.1: Deprecated/Dead Methods löschen
- `history.py:262-266`: `save_hf_token()` — body ist `pass`
- `history.py:268-273`: `get_hf_token()` — return `None`
- `history.py:290-292`: `set_user_preference()` — redundanter Alias
- `main_window.py:845`: `load_last_settings()` — deprecated wrapper
- `main_window.py:1232-1235`: `on_cli_progress()` — body ist `pass`
- `main_window.py:984-986`: `update_status()` — body ist `pass`, Timer-Aufruf entfernen

### Schritt 2.2: Broken/Dead Code in InputPanel löschen
- `input_panel.py:391-416`: `load_hf_token_from_keychain()` — referenziert nicht existierendes `self.hf_token_input`
- `input_panel.py:419`: `get_hf_token()` — gleiche Referenz auf nicht existierendes Attribut

### Schritt 2.3: Dead Branch in `append_output` bereinigen
- `main_window.py:1473-1478`: if/else mit identischen Branches → vereinfachen zu einem Aufruf

### Schritt 2.4: `findChild`-Bug in BatchPanel
- `batch_panel.py:287`: `findChild(QPushButton, "➕ Dateien hinzufügen")` sucht nach `objectName`, nicht Button-Text → direkte Referenz auf Button verwenden statt `findChild`

### Schritt 2.5: Überflüssige lokale Re-Imports entfernen
- `main_window.py:506` und `main_window.py:1489`: Doppelter `from pathlib import Path` Import

---

## Phase 3 — Duplikate eliminieren

### Schritt 3.1: `CollapsibleSection` tatsächlich nutzen
- Die vorhandene Klasse in `collapsible_section.py` an die tatsächlichen Anforderungen anpassen
- Copy-Paste-Boilerplate in `model_panel.py:67-84`, `diarization_panel.py:58-76`, `output_panel.py:48-66`, `settings_panel.py:62-80` durch Nutzung der `CollapsibleSection` ersetzen
- Jeweils auch `toggle_content()` Methoden entfernen (nun in `CollapsibleSection` gekapselt)

### Schritt 3.2: Timestamp-Parsing vereinheitlichen
- Gemeinsame Funktion `parse_timestamp(line: str)` in `utils.py` erstellen
- Doppelte Implementierung in `workers.py:40-57` und `progress_tracker.py:235-253` ersetzen

### Schritt 3.3: `History.add_*` generisch machen
- Interne Methode `_add_to_list(list_key, entry, match_key)` in `history.py` erstellen
- `add_input_file()`, `add_model()`, `add_output_path()` darauf reduzieren

### Schritt 3.4: Keychain-Token-Loading zusammenführen
- Gemeinsame Funktion `load_token_from_keychain(service_name, ...)` in `utils.py` oder `macos_utils.py` erstellen
- Duplizierte Logik in `diarization_panel.py:287-302` und `input_panel.py:391-416` ersetzen (bzw. die in InputPanel ist bereits dead code → nur noch die in DiarizationPanel refactoren)

### Schritt 3.5: `update_recent_*_menu` in MainWindow vereinheitlichen
- Generische Methode `_update_recent_menu(menu, items, callback)` für `main_window.py:718-735` und `main_window.py:737-756`

---

## Phase 4 — Bugs fixen

### Schritt 4.1: Tab-Index-Mismatch in `get_input_mode()`
- `input_panel.py:505-514`: Tab-Reihenfolge ist Live(0), File(1), Batch(2), aber `get_input_mode()` mapped falsch
- Korrektur: Index 0 → `'live'`, Index 1 → `'file'`, Index 2 → `'batch'`
- Verifizieren, dass alle Aufrufer von `get_input_mode()` korrekt damit arbeiten (möglicherweise hat sich der Code um den Bug herum entwickelt)

### Schritt 4.2: Fehlender f-String-Prefix
- `input_panel.py:493`: `"✅ Gespeichert: {path.name} ({size_mb:.1f}MB)"` → f-String-Prefix hinzufügen

---

## Phase 5 — MainWindow aufteilen (God Class)

Die 2266-Zeilen-Klasse `main_window.py` wird in folgende Controller zerlegt:

### Schritt 5.1: `src/gui/menu_manager.py` erstellen
- Extrahiert Menübar-Erstellung (~L586–756)
- `MenuManager(main_window)` erhält Referenz auf `MainWindow` für Callbacks
- Enthält: `create_menu_bar()`, `_update_recent_menu()`, Language-Dropdown-Styling

### Schritt 5.2: `src/gui/profile_controller.py` erstellen
- Extrahiert alle Profil-Operationen (~300 Zeilen)
- `ProfileController(history_manager, callback)` 
- Enthält: `save_profile()`, `delete_profile()`, `duplicate_profile()`, `export_profile()`, `import_profile()`, `toggle_favorite()`, `apply_profile()`

### Schritt 5.3: `src/gui/transcription_controller.py` erstellen
- Extrahiert CLI-Argument-Building und Transkriptions-Orchestrierung
- `TranscriptionController(panels, worker_factory)`
- Enthält: `build_cli_arguments()`, `start_transcription()`, `stop_transcription()`, `on_transcription_finished()`

### Schritt 5.4: `src/gui/session_manager.py` erstellen
- Extrahiert Session-Persistenz und Wiederherstellung
- `SessionManager(history_manager)`
- Enthält: `save_session()`, `load_session()`, `apply_wizard_settings()`

### Schritt 5.5: `HistoryManager` zum Singleton machen
- Statt 3 separate Instanzen (`app.py:26`, `main_window.py:70`, `onboarding.py:147`) eine zentrale Instanz verwenden, die von `app.py` erstellt und durchgereicht wird

### Schritt 5.6: `refresh_ui()` vereinfachen
- `main_window.py:1983-2105`: Die ~120 Zeilen manuelles Text-Update refactoren — jedes Panel erhält eigene `refresh_translations()` Methode, `MainWindow.refresh_ui()` delegiert nur noch

---

## Phase 6 — Hardcodierte Strings & Übersetzungen

### Schritt 6.1: Fehlende Übersetzungskeys zu `translations.py` hinzufügen
- ~15+ identifizierte hardcodierte deutsche Strings (z.B. aus `main_window.py:116`, `batch_window.py:52`, `input_panel.py:348`)
- Für jeden String: DE- und EN-Übersetzung in `TRANSLATIONS` einfügen
- Hardcodierten String durch `tr("key")` Aufruf ersetzen

### Schritt 6.2: CLI-Invokation vereinheitlichen
- `batch_window.py:87`: `"python3"` → `sys.executable` (wie in `workers.py:80-82`)

---

## Phase 7 — Kleinere Bereinigungen

### Schritt 7.1: Theme-Persistenz vereinheitlichen
- Entscheiden: Theme nur noch über `history.py` `user_preferences` ODER nur über `theme.py` `theme.json` — nicht beides
- Doppelte Persistenz in `installation_wizard.py` bereinigen

### Schritt 7.2: Token-Validierung aus UI extrahieren
- `diarization_panel.py:275-276`: `validate_token_format()` Logic nach `utils.py` verschieben

### Schritt 7.3: `sys.path`-Manipulation in RecordingWorker bereinigen
- `workers.py:182-187`: Durch ordentlichen relativen Import ersetzen

### Schritt 7.4: Code-Sprache konsistent machen
- Docstrings und Print-Statements auf eine Sprache (Deutsch oder Englisch) vereinheitlichen

### Schritt 7.5: `parent().parent()` Kette in InstallationWizard absichern
- `installation_wizard.py:144`: Explizite Wizard-Referenz im Konstruktor übergeben statt fragile Parent-Chain

---

## Empfohlene Reihenfolge

| Reihenfolge | Phase | Risiko | Abhängigkeiten |
|---|---|---|---|
| 1 | Phase 1 (Infrastruktur) | Niedrig | — |
| 2 | Phase 2 (Dead Code) | Niedrig | — |
| 3 | Phase 4 (Bugfixes) | Mittel | Verifizierung nötig |
| 4 | Phase 3 (Duplikate) | Mittel | Phase 1 |
| 5 | Phase 6 (Übersetzungen) | Niedrig | Phase 1 |
| 6 | Phase 5 (MainWindow) | **Hoch** | Phase 2, 3 |
| 7 | Phase 7 (Cleanup) | Niedrig | Phase 5 |

---

## Verification

- **Unit-Tests**: Bestehende Tests in `tests/` ausführen nach jeder Phase (`python -m pytest tests/`)
- **Manuelle Tests**: App starten (`python run_dev.py`), folgende Flows prüfen:
  - Datei-Transkription, Live-Aufnahme, Batch-Verarbeitung
  - Profil speichern/laden/exportieren
  - Theme-Wechsel Light/Dark
  - Sprache DE↔EN umschalten
  - Collapsible Sections auf/zuklappen
  - Installation Wizard (History-Datei löschen zum Testen)
- **Regressions-Check `get_input_mode()`**: Nach Bugfix verifizieren, dass kein anderer Code sich auf die falsche Reihenfolge verlässt

---

## Decisions

- **MainWindow aufteilen**: Vollständige Zerlegung in 4 Controller-Klassen statt nur Bereinigung
- **Bugs fixen**: Tab-Index und f-String werden korrigiert (trotz "keine Funktionsänderung"-Prämisse, da es echte Fehler sind)
- **Übersetzungen**: Alle hardcodierten Strings in `translations.py` verschieben
- **`CollapsibleSection`**: Vorhandene, ungenutzte Klasse wird endlich verwendet statt gelöscht
- **HistoryManager**: Singleton-Pattern statt 3 separate Instanzen
