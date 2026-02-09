# Testing Guide - Neue Features

## 🧪 Test-Checkliste für neue Features

### Vorbereitung

```bash
cd /Users/henrymirus/V-Speech

# Dependencies installieren (falls noch nicht geschehen)
pip install requests

# History löschen um First-Run zu simulieren
rm -rf ~/.vspeechflow/history/

# Optional: Cache auch löschen
rm -rf ~/.vspeechflow/cache/
```

---

## ✅ Test 1: Installation Wizard

**Ziel**: Wizard beim ersten Start testen

1. **App starten**:
   ```bash
   python -m src.gui.app
   ```

2. **Erwartetes Verhalten**:
   - Wizard-Fenster erscheint automatisch
   - "Willkommen bei V-SpeechFlow!" Titel
   
3. **Durchlaufen**:
   - ✅ Seite 1: Willkommen → "Weiter"
   - ✅ Seite 2: Modell-Auswahl → Pfad eingeben oder leer lassen → "Weiter"
   - ✅ Seite 3: HF Token → Optional eingeben → "Weiter"
   - ✅ Seite 4: Präferenzen → Sprache/Theme/Threads wählen → "Weiter"
   - ✅ Seite 5: Abschluss → "Tutorial starten" oder "Tutorial überspringen"

4. **Prüfen**:
   - Hauptfenster öffnet sich nach Wizard
   - Wenn "Tutorial starten": Onboarding startet automatisch
   - Settings werden in History gespeichert

---

## ✅ Test 2: Onboarding Tutorial

**Ziel**: Tutorial-System testen

1. **Tutorial starten** (falls nicht automatisch):
   - Menü: **❓ Hilfe** → **🎓 Tutorial starten**

2. **Erwartetes Verhalten**:
   - Overlay erscheint (dunkler Hintergrund)
   - Dialog unten rechts mit Schritt-Info
   - UI-Element wird highlighted (grüner Rahmen)

3. **Navigation testen**:
   - ✅ "Weiter" → Nächster Schritt
   - ✅ "Zurück" → Vorheriger Schritt
   - ✅ "Überspringen" → Bestätigungs-Dialog → Tutorial beenden
   - ✅ "Fertig" (letzter Schritt) → Tutorial abschließen

4. **Prüfen**:
   - Overlay verschwindet nach Abschluss
   - Success-Message wird angezeigt
   - Tutorial kann erneut über Menü gestartet werden

---

## ✅ Test 3: Mehrsprachigkeit

**Ziel**: Language-Switcher testen

1. **Sprache wechseln**:
   - Menü: **⚙️ Einstellungen** → **🌍 Sprache / Language** → **🇺🇸 English**

2. **Erwartetes Verhalten**:
   - Info-Dialog: "Language has been changed..."
   - Nach Dialog-Schließen: Settings gespeichert

3. **App neu starten**:
   ```bash
   # App schließen und neu starten
   python -m src.gui.app
   ```

4. **Prüfen**:
   - UI ist jetzt auf Englisch
   - Menu-Einträge auf Englisch
   - Tooltips auf Englisch
   - Wizard/Onboarding auf Englisch (wenn erneut gestartet)

5. **Zurück auf Deutsch**:
   - Menü: **⚙️ Settings** → **🌍 Language** → **🇩🇪 Deutsch**
   - App neu starten

---

## ✅ Test 4: Tooltips

**Ziel**: Alle Tooltips prüfen

1. **Panels durchgehen**:
   - ✅ **Input Panel**: Hover über Datei-Input, Browse-Button, Mikrofon-Dropdown
   - ✅ **Model Panel**: Hover über Modell-Pfad, Browse-Button
   - ✅ **Settings Panel**: Hover über Thread-Slider, Sprache-Dropdown, Checkboxes
   - ✅ **Diarization Panel**: Hover über Enable-Checkbox, Token-Input, RadioButtons
   - ✅ **Output Panel**: Hover über Output-Pfad, Format-RadioButtons, Timestamps

2. **Erwartetes Verhalten**:
   - Tooltip erscheint nach ~1 Sekunde Hover
   - Text ist in gewählter Sprache
   - Text erklärt Funktion des Elements

---

## ✅ Test 5: Model Update Check

**Ziel**: Auto-Update-Check testen

### Variante A: Mit echtem Modell

1. **Modell setzen**:
   - Model Panel → Modell-Pfad eingeben (z.B. `models/ggml-small.bin`)

2. **App neu starten**:
   ```bash
   python -m src.gui.app
   ```

3. **Erwartetes Verhalten**:
   - Nach ~3 Sekunden: HTTP-Request zu HuggingFace
   - Wenn Update verfügbar: Benachrichtigungs-Dialog
   - Wenn kein Update: Keine Meldung (silent check)

4. **Cache prüfen**:
   ```bash
   cat ~/.vspeechflow/cache/model_update_cache.json
   ```
   - Sollte Timestamp und Update-Status enthalten

### Variante B: Manual Trigger

1. **Python Console**:
   ```python
   from src.gui.model_utils import check_model_update_available
   
   result = check_model_update_available('models/ggml-small.bin')
   print(result)
   ```

2. **Erwartete Ausgabe**:
   ```python
   {
       'update_available': True/False,
       'local_size_mb': 500.0,
       'remote_size_mb': 500.0,
       'model_name': 'ggml-small.bin',
       'download_url': 'https://...',
       'error': None
   }
   ```

---

## ✅ Test 6: Persistente Settings

**Ziel**: History-Integration prüfen

1. **Settings einstellen**:
   - Modell auswählen
   - HF Token eingeben (Diarization Panel)
   - Threads ändern
   - Theme wechseln
   - Sprache wählen

2. **App schließen und neu starten**

3. **Erwartetes Verhalten**:
   - Alle Settings bleiben erhalten
   - Modell-Pfad ist vorausgefüllt
   - HF Token ist gespeichert (wird nicht nochmal abgefragt)
   - Thread-Wert wie eingestellt
   - Theme und Sprache wie gewählt

4. **History-Datei prüfen**:
   ```bash
   cat ~/.vspeechflow/history/history.json
   ```

---

## ✅ Test 7: Wizard-Settings in Main-App

**Ziel**: Settings aus Wizard werden korrekt angewendet

1. **History löschen**:
   ```bash
   rm -rf ~/.vspeechflow/history/
   ```

2. **App starten** → Wizard durchlaufen:
   - Modell setzen: `models/ggml-base.bin`
   - Token eingeben: `hf_test123`
   - Threads: 4
   - Sprache: English
   - Theme: Dark
   - Auto-Open: ✅

3. **Wizard abschließen** (Tutorial überspringen)

4. **Prüfen im Hauptfenster**:
   - ✅ Model Panel: Pfad ist `models/ggml-base.bin`
   - ✅ Diarization Panel: Token ist automatisch aus Keychain geladen!
   - ✅ Settings Panel: Threads ist 4
   - ✅ UI ist auf Englisch
   - ✅ Dark Mode ist aktiv
   - ✅ Output Panel: Auto-Open ist gecheckt

5. **Token in Keychain prüfen**:
   ```bash
   security find-generic-password -s HF_V-Speechflow -w
   ```
   - Sollte `hf_test123` ausgeben

---

## ✅ Test 8: HF-Token Keychain Management

**Ziel**: Token-Speicherung und Auto-Load testen

### Variante A: Token im Wizard eingeben

1. **History löschen**:
   ```bash
   rm -rf ~/.vspeechflow/history/
   ```

2. **App starten** → Wizard durchlaufen
3. **Token-Seite**: `hf_test_wizard_token` eingeben
4. **Wizard abschließen**

5. **Keychain prüfen**:
   ```bash
   security find-generic-password -s HF_V-Speechflow -w
   ```
   - Erwartete Ausgabe: `hf_test_wizard_token`

6. **App neu starten**
7. **Diarization Panel öffnen**
   - ✅ Token ist automatisch geladen (ohne manuelle Eingabe!)

### Variante B: Token manuell in Keychain speichern

1. **Token in Keychain speichern**:
   ```bash
   security add-generic-password -s HF_V-Speechflow -a user -w "hf_manual_token_123"
   ```

2. **App starten**
3. **Diarization Panel öffnen**
   - ✅ Token ist automatisch im Eingabefeld!

4. **"🔑 Keychain" Button klicken**
   - ✅ Success-Meldung: "Token erfolgreich aus Keychain geladen!"

### Variante C: Kein Token vorhanden (Fehlerfall)

1. **Token aus Keychain löschen**:
   ```bash
   security delete-generic-password -s HF_V-Speechflow
   ```

2. **App starten**
3. **Diarization Panel öffnen**
   - ✅ Token-Feld ist leer (kein Auto-Load)

4. **"🔑 Keychain" Button klicken**
   - ✅ Warnmeldung erscheint:
     - "Token nicht gefunden"
     - Erklärt mögliche Ursachen
     - Gibt Terminal-Befehl zum Speichern

5. **Diarization aktivieren + Start Transkription klicken**
   - ✅ Validierungs-Fehler:
     - "HuggingFace Token ist erforderlich"
     - Erklärt dass Token nicht in Keychain gefunden wurde
     - Gibt Anweisungen zum Speichern

---

## 🐛 Bekannte Einschränkungen

1. **Sprach-Wechsel**: Erfordert App-Neustart für vollständige Anwendung
2. **Model-Update**: Nur für vordefinierte Modelle aus `AVAILABLE_MODELS`
3. **HF Token**: Keychain-Integration nur auf macOS verfügbar
4. **Onboarding**: Widget-Highlights funktionieren nur für sichtbare Elemente
4. **Onboarding**: Widget-Highlights funktionieren nur für sichtbare Elemente

---

## 🔍 Debugging

### Logs prüfen

```bash
# App-Logs
tail -f ~/.vspeechflow/logs/vspeechflow_*.log

# Nach Fehlern suchen
grep -i "error\|exception" ~/.vspeechflow/logs/vspeechflow_*.log
```

### History manuell editieren

```bash
# Backup erstellen
cp ~/.vspeechflow/history/history.json ~/.vspeechflow/history/history.json.bak

# Editieren
nano ~/.vspeechflow/history/history.json

# Oder komplett löschen für Reset
rm ~/.vspeechflow/history/history.json
```

### Cache löschen

```bash
# Model-Update-Cache
rm ~/.vspeechflow/cache/model_update_cache.json
```

---

## ✅ Success Criteria

Alle Tests müssen PASSED sein:

- [ ] Installation Wizard erscheint beim ersten Start
- [ ] Onboarding kann gestartet und durchlaufen werden
- [ ] Sprache kann gewechselt werden (DE ↔ EN)
- [ ] Tooltips erscheinen bei Hover in gewählter Sprache
- [ ] Model-Update-Check läuft beim Start (nach 3s)
- [ ] Settings werden persistent gespeichert
- [ ] Wizard-Settings werden in Main-App angewendet
- [ ] HF-Token wird in Keychain gespeichert (nicht in History!)
- [ ] Token wird automatisch beim Start geladen
- [ ] Intelligente Fehlermeldung wenn Token nicht gefunden
- [ ] Token kann manuell via Keychain-Button geladen werden
- [ ] Keine Python-Fehler in Logs
- [ ] Keine UI-Crashes oder Freezes

---

## 📞 Support

Bei Problemen:

1. **Logs prüfen**: `~/.vspeechflow/logs/`
2. **History prüfen**: `~/.vspeechflow/history/history.json`
3. **Cache löschen**: `rm -rf ~/.vspeechflow/cache/`
4. **Fresh Start**: History löschen und neu starten

---

**Status**: Tests bereit für Ausführung
**Version**: 0.1.0
**Datum**: 8. Februar 2026
