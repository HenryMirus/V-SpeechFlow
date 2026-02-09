# Neue Features - V-SpeechFlow GUI

## 📋 Übersicht der implementierten Features

### ✅ 1. **History-System erweitert** (`history.py`)
- Speicherung von App-Settings (first_run, wizard_completed, onboarding_completed)
- Persistente HuggingFace Token Speicherung
- User-Preferences (ui_language, theme, auto_open, check_updates)
- Neue Methoden:
  - `is_first_run()`, `is_wizard_completed()`, `is_onboarding_completed()`
  - `save_hf_token()`, `get_hf_token()`
  - `save_app_setting()`, `get_app_setting()`
  - `save_user_preference()`, `get_user_preference()`

### ✅ 2. **Mehrsprachigkeit** (`translations.py`)
- Vollständiges Übersetzungssystem für Deutsch und Englisch
- 100+ übersetzte Strings für alle UI-Elemente
- Einfache API: `tr("key")` für Übersetzungen
- Unterstützt String-Formatierung: `tr("onboarding_step", current=1, total=5)`
- Language-Switcher im Menü (⚙️ Einstellungen → 🌍 Sprache)

### ✅ 3. **Installation Wizard** (`installation_wizard.py`)
- Mehrstufiger Setup-Assistent für neue Benutzer
- 5 Schritte:
  1. **Willkommen** - Einführung
  2. **Modell-Auswahl** - Whisper-Modell konfigurieren
  3. **HF-Token** - Optional Token eingeben (wird in macOS Keychain gespeichert!)
  4. **Präferenzen** - Sprache, Theme, Threads, Auto-Open
  5. **Abschluss** - Tutorial-Angebot
- Alle Einstellungen werden automatisch gespeichert
- **HF-Token wird in macOS Keychain gespeichert** (NICHT in History!)
- Token wird automatisch bei Transkriptionen verwendet

### ✅ 4. **Onboarding Tutorial** (`onboarding.py`)
- Interaktives Tutorial durch die wichtigsten Funktionen
- 6 Schritte mit visuellen Highlights:
  1. Willkommen
  2. Audio-Input (Datei/Live)
  3. Modell-Auswahl
  4. Speaker Diarization
  5. Profile
  6. Transkription starten
- Overlay-System mit transparentem Hintergrund
- Highlight-Rahmen um aktuelle UI-Elemente
- Kann jederzeit über Hilfe-Menü gestartet werden

### ✅ 5. **Tooltips für alle UI-Elemente**
- **36 Tooltips** hinzugefügt in 5 Panels:
  - **input_panel.py**: 9 Tooltips (Dateiauswahl, Mikrofon, Recording)
  - **model_panel.py**: 3 Tooltips (Modellpfad, Browser)
  - **settings_panel.py**: 8 Tooltips (Threads, Sprache, Translate)
  - **diarization_panel.py**: 9 Tooltips (Diarization, Token, Sprecher)
  - **output_panel.py**: 7 Tooltips (Output-Pfad, Format, Timestamps)
- Alle Tooltips sind mehrsprachig über `translations.py`

### ✅ 6. **Auto-Update-Check für Modelle** (`model_utils.py`)
- Prüft automatisch auf neue Modell-Versionen
- HTTP HEAD-Request zu HuggingFace
- Vergleicht lokale und remote Dateigröße
- Caching-System (prüft nur alle 24h)
- Benachrichtigung mit Download-Link
- Kann in Settings deaktiviert werden

### ✅ 7. **App-Integration** (`app.py`, `main_window.py`)
- Wizard startet automatisch beim ersten App-Start
- Onboarding wird nach Wizard oder beim nächsten Start angeboten
- Sprach-Einstellung wird beim Start geladen
- Model-Update-Check läuft 3 Sekunden nach Start
- Neue Menu-Einträge:
  - 🌍 Sprache / Language (Deutsch/English)
  - 🎓 Tutorial starten (im Hilfe-Menü)

---

## 🚀 Verwendung

### Erster Start
1. **App starten** → Installation Wizard erscheint automatisch
2. **Modell auswählen** (optional, kann später gesetzt werden)
3. **HF-Token eingeben** (optional, für Diarization)
4. **Präferenzen einstellen** (Sprache, Theme, Threads)
5. **Tutorial starten** oder überspringen

### Sprache wechseln
1. Menü: **⚙️ Einstellungen** → **🌍 Sprache / Language**
2. Deutsch oder English auswählen
3. App neu starten um alle Änderungen zu sehen

### Tutorial erneut starten
1. Menü: **❓ Hilfe** → **🎓 Tutorial starten**
2. Durch 6 Schritte navigieren
3. Jederzeit mit "Überspringen" beenden

### HF-Token Management
- **Beim Wizard eingeben** → Wird in macOS Keychain gespeichert (NICHT in History!)
- **Auto-Load beim Start**: Wird automatisch aus Keychain geladen
- **Später ändern**: Diarization-Panel → Token-Eingabe
- **Aus Keychain laden** (macOS): "Aus Keychain laden" Button
- **Intelligente Fehlermeldungen**: Klare Anweisungen wenn Token nicht gefunden
- **Sicher**: Token wird nur in Keychain gespeichert, nicht in JSON-Dateien

### Model-Updates
- Automatische Prüfung beim Start (alle 24h)
- Benachrichtigung wenn Update verfügbar
- Download-Link wird geöffnet
- In Settings deaktivierbar

---

## 📁 Neue Dateien

```
src/gui/
├── translations.py           # Mehrsprachigkeits-System
├── installation_wizard.py    # Setup-Wizard
└── onboarding.py            # Tutorial-System
```

## 🔧 Erweiterte Dateien

```
src/gui/
├── history.py               # + App Settings & User Preferences
├── model_utils.py           # + Update-Check Funktionen
├── main_window.py           # + Wizard/Onboarding Integration
├── app.py                   # + First-Run Logic
├── input_panel.py           # + Tooltips
├── model_panel.py           # + Tooltips, get_model_path()
├── settings_panel.py        # + Tooltips, set_threads()
├── diarization_panel.py     # + Tooltips, set_hf_token()
└── output_panel.py          # + Tooltips, set_auto_open()
```

## 📦 Dependencies

Neue Abhängigkeit in `requirements.txt`:
```
requests>=2.28.0  # HTTP requests for model update checks
```

Installation:
```bash
pip install requests
```

---

## 🎯 Persistente Einstellungen

Alle Einstellungen werden in `~/.vspeechflow/history/history.json` gespeichert:

```json
{
  "app_settings": {
    "first_run": false,
    "wizard_completed": true,
    "onboarding_completed": true,
    "default_language": "de",
    "default_model": "/path/to/model.bin",
    "default_threads": 8,
    "preferred_theme": "dark"
  },
  "user_preferences": {
    "auto_open_transcript": true,
    "show_tooltips": true,
    "ui_language": "de",
    "check_model_updates": true
  }
}
```

**Wichtig:** Der HuggingFace Token wird NICHT in der History gespeichert!  
Der Token wird ausschließlich in der **macOS Keychain** verwaltet für maximale Sicherheit.

---

## 🐛 Testing

Zum Testen des First-Run-Workflows:

```bash
# History löschen um First-Run zu simulieren
rm -rf ~/.vspeechflow/history/

# App starten
python -m src.gui.app
```

---

## 💡 Features im Detail

### Installation Wizard
- **Nicht-blockierend**: User kann Felder leer lassen
- **Validierung**: Optional - nur wenn Pfade angegeben werden
- **Token-Sicherheit**: Token wird verborgen eingegeben (Password-Feld)
- **Empfehlungen**: System erkennt CPU-Kerne und empfiehlt Thread-Anzahl

### Onboarding
- **Nicht-modal**: User kann während Tutorial mit UI interagieren
- **Visual Highlights**: Grüner Rahmen um aktuelle Elemente
- **Überspringbar**: Kann jederzeit übersprungen werden
- **Wiederholbar**: Über Hilfe-Menü erneut startbar

### Tooltips
- **Kontextsensitiv**: Erklärt was das Element macht
- **Mehrsprachig**: Automatisch in gewählter Sprache
- **Sichtbar auf Hover**: Standard Qt-Tooltip Verhalten

### Model-Update Check
- **Im Background**: Blockiert UI nicht
- **Cached**: Prüft nur alle 24h
- **Optional**: Kann in Preferences deaktiviert werden
- **Nicht-invasiv**: Nur Benachrichtigung bei Update

---

## 🎨 UI/UX Verbesserungen

- ✅ Wizard führt neue User durch Setup
- ✅ Tutorial erklärt wichtigste Funktionen
- ✅ Tooltips helfen bei jedem Schritt
- ✅ Mehrsprachigkeit für internationale User
- ✅ Auto-Update-Check hält Modelle aktuell
- ✅ Persistente Settings = keine Neueinrichtung nötig
- ✅ HF-Token muss nur einmal eingegeben werden

---

## 🔒 Sicherheit

- **HF-Token**: Wird ausschließlich in **macOS Keychain** gespeichert (NICHT in History/JSON!)
- **Keychain-Vorteile**: 
  - Verschlüsselt durch macOS
  - System-Level Sicherheit
  - Nicht im Dateisystem sichtbar
- **Auto-Load**: Token wird beim Start automatisch aus Keychain geladen
- **Keine Plain-Text Speicherung**: Token erscheint nie in JSON-Config-Dateien
- **Empfehlung**: Sicher für Verwendung auf persönlichen macOS-Systemen

---

## 📝 Nächste Schritte (Optional)

- [x] Token-Verschlüsselung → Verwendung von macOS Keychain (erledigt!)
- [ ] Modell-Download direkt aus GUI
- [ ] Weitere Sprachen (FR, ES, IT)
- [ ] Video-Tutorial aufnehmen
- [ ] Erweiterte Tooltip-Grafiken

---

**Status**: ✅ Alle Features erfolgreich implementiert und getestet
**Version**: 0.1.0
**Datum**: 8. Februar 2026
