# V-SpeechFlow App - Quick Start Guide

## � Voraussetzungen (vor Installation)

Bevor Sie starten, müssen folgende Tools **manuell installiert** sein:

### 1. Git
```bash
# Prüfen
git --version

# Installieren (falls nötig)
xcode-select --install
```

### 2. Homebrew
```bash
# Prüfen
brew --version

# Installieren (falls nötig)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. System-Tools
```bash
# Alle auf einmal installieren
brew install cmake python@3.11 ffmpeg portaudio
```

**Einzeln:**
- `brew install cmake` - Für C++ Kompilierung
- `brew install python@3.11` - Python Runtime
- `brew install ffmpeg` - Audio-Konvertierung
- `brew install portaudio` - Optional für Live-Recording

---

## �🚀 Einfachster Start

```bash
# Im Projektverzeichnis:
./start_app.sh
```

Das war's! Das Script:
- ✓ Prüft alle Voraussetzungen
- ✓ Erstellt ein Virtual Environment (`.venv`)
- ✓ Installiert fehlende Python-Pakete im Virtual Environment
- ✓ Kompiliert das Projekt automatisch
- ✓ Startet die GUI

**Modell-Download und Token-Konfiguration erfolgen in der App!**

---

## 📦 Vollständige .app Bundle erstellen

Für eine "richtige" macOS-App mit Icon im Finder:

```bash
./build_app.sh
```

Die fertige App: `dist/V-SpeechFlow.app`

### App installieren

```bash
# In /Applications verschieben
mv dist/V-SpeechFlow.app /Applications/

# Oder direkt öffnen
open dist/V-SpeechFlow.app
```

---

## 🔧 Voraussetzungen (werden geprüft)

Das `start_app.sh` Script prüft automatisch:

### System-Tools (müssen manuell installiert werden)
```bash
brew install cmake
brew install ffmpeg
brew install portaudio  # Optional für Live-Recording
```

### Python-Pakete (werden automatisch installiert)
- PyQt6 (GUI)
- PyTorch & torchaudio (KI-Engine)
- pyannote.audio (Speaker Diarization)
- Weitere siehe `requirements.txt`

---

## 🎯 Was kann die App?

1. **Live-Transkription** vom Mikrofon
2. **Audio-Dateien transkribieren** (MP3, M4A, WAV, etc.)
3. **Speaker Diarization** (Wer hat was gesagt?)
4. **Modell-Download** direkt in der App
5. **Token-Verwaltung** für Hugging Face (Speaker Diarization)
6. **Komplett offline** - keine Cloud-Verbindung nötig

---

## 📝 Erste Schritte in der App

1. **Installation Wizard** beim ersten Start:
   - Modell auswählen und herunterladen
   - Optional: HF-Token für Speaker Diarization eingeben
   - Tutorial durchgehen (empfohlen)

2. **Audio transkribieren**:
   - Datei auswählen
   - Modell wählen
   - Optional: Speaker Diarization aktivieren
   - "Start" klicken

3. **Live-Aufnahme**:
   - Mikrofon wählen
   - "Record" drücken
   - Mit Ctrl+C oder "Stop" beenden
   - Automatische Transkription

---

## 🆘 Troubleshooting

### App startet nicht

```bash
# Prüfe ob alle Dependencies installiert sind:
./start_app.sh
```

Die ausführliche Fehlerausgabe zeigt, was fehlt.

### "externally-managed-environment" Fehler

**Problem:** macOS Python (via Homebrew) erlaubt keine systemweiten pip-Installationen.

**Lösung:** Geschieht automatisch! Die Scripts erstellen ein Virtual Environment (`.venv`) und installieren alle Pakete dort. Sie müssen nichts tun.

Falls Sie manuell arbeiten möchten:
```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Pakete sind jetzt verfügbar
python3 launch_app.py
```

### "CMake not found"
```bash
brew install cmake
```

### "ffmpeg not found"
```bash
brew install ffmpeg
```

### "Git not found"
```bash
xcode-select --install
# oder
brew install git
```

### "Python not found"
```bash
brew install python@3.11
```

### "Mikrofon nicht verfügbar"
```bash
# PortAudio installieren
brew install portaudio

# PyAudio neu installieren
pip install --force-reinstall pyaudio
```

### "Kompilierung fehlgeschlagen"

```bash
# Xcode Command Line Tools installieren
xcode-select --install

# Build-Verzeichnis aufräumen
rm -rf build
./start_app.sh
```

---

## 📚 Weitere Dokumentation

- **Vollständige README**: [README.md](README.md)
- **CLI-Nutzung**: Für fortgeschrittene Nutzer siehe `README.md`
- **Entwickler-Dokumentation**: `.github/copilot-instructions.md`

---

## 🎨 Für Entwickler

### Development Mode mit Hot Reloading
```bash
./dev.sh
```

### Normaler Start ohne Build
```bash
python3 launch_app.py
```

### Tests ausführen
```bash
pytest tests/
```

---

## 💡 Tipps

- **Modell-Wahl**: `ggml-small.bin` ist der beste Kompromiss für Deutsch
- **Speaker Diarization**: Funktioniert am besten mit klaren Aufnahmen
- **Performance**: Auf Apple Silicon (M1/M2/M3) optimal
- **Offline**: Alles läuft lokal, keine Internet-Verbindung nötig

---

**Viel Erfolg mit V-SpeechFlow! 🎯**
