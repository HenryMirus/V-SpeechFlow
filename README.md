# V-SpeechFlow

Lokales, offline Speech-to-Text-System für **deutsche Sprache** mit Speaker Diarization. Optimiert für macOS (Apple Silicon), basierend auf [whisper.cpp](https://github.com/ggerganov/whisper.cpp).

## 🚀 Schnelleinstieg

**Voraussetzung:** Git, CMake, Python und ffmpeg müssen installiert sein (siehe [Voraussetzungen](#voraussetzungen))

```bash
# 1. Repository klonen
git clone <dein-repo-url> V-SpeechFlow
cd V-SpeechFlow

# 2. App starten (macht den Rest automatisch!)
./start_app.sh
```

**Das war's!** Die GUI startet mit einem Installation Wizard, der Sie durch das Setup führt.

---

## Features

- ✅ **Moderne GUI** – Intuitive PyQt6-Oberfläche für macOS
- ✅ **Komplett offline** – keine Cloud-Verbindung erforderlich
- ✅ **Live-Aufnahme** – Direkt vom macOS Mikrofonarray transkribieren
- ✅ **Optimiert für deutsche Sprache** – Speaker Diarization für deutsche Konversationen
- ✅ **Apple Silicon optimiert** (M1/M2/M3) mit MPS-Acceleration
- ✅ **Multi-Format-Support** – mp3, m4a, wav, etc. (via ffmpeg)
- ✅ **Speaker Diarization** – Automatische Sprechererkennung mit deutschen Parametern
- ✅ **Flexible Ausgabe** – Plain-Text oder Segmente mit Timestamps und Sprecher-Zuordnung
- ✅ **Installation Wizard** – Geführtes Setup beim ersten Start
- ✅ **CLI verfügbar** – Für fortgeschrittene Nutzer und Automatisierung

## Architektur

```
┌─────────────────────────────────────┐
│   PyQt6 GUI (app.py)                │
│   - Intuitive Benutzeroberfläche    │
│   - Installation Wizard             │
│   - Profilverwaltung                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Python Layer (stt_cli.py)         │
│   - Audio-Konvertierung (ffmpeg)    │
│   - Diarization & Live-Recording    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   C++ Binary (stt_native)           │
│   - Whisper.cpp Integration         │
│   - WAV-Processing                  │
│   - Speech-to-Text Engine           │
└─────────────────────────────────────┘
```

## Voraussetzungen

### System
- macOS 11.0+ (Big Sur oder neuer)
- Apple Silicon (M1/M2/M3) empfohlen
- Ca. 500 MB – 3 GB Speicher (je nach Modellgröße)

### ⚠️ Manuell zu installieren (VOR `./start_app.sh`)

Diese Tools müssen Sie **manuell installieren**, bevor Sie das Projekt nutzen können:

#### 1. Git (zum Klonen des Repositories)
```bash
# Prüfen ob Git installiert ist
git --version

# Falls nicht installiert:
xcode-select --install
# oder
brew install git
```

#### 2. Homebrew (empfohlener Paketmanager für macOS)
Falls noch nicht installiert:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 3. Erforderliche System-Tools
```bash
# CMake (für C++ Kompilierung)
brew install cmake

# Python 3.10+
brew install python@3.11

# ffmpeg (für Audio-Konvertierung)
brew install ffmpeg

# Xcode Command Line Tools (Compiler)
xcode-select --install
```

#### 4. Optional: PortAudio (für Live-Recording)
```bash
brew install portaudio
```

### ✅ Automatisch installiert (durch `./start_app.sh`)

Diese Komponenten werden **automatisch** vom Start-Script eingerichtet:
- Python Virtual Environment (`.venv`)
- Python-Pakete (PyQt6, PyTorch, pyannote.audio, etc.)
- Git-Submodule (whisper.cpp)
- C++ Binary (stt_native)

### Speaker Diarization (wird in der GUI konfiguriert)
- **Hugging Face Account**: Kostenlos registrieren auf [huggingface.co](https://huggingface.co)
- **HF Token**: Kann im Installation Wizard oder in den Einstellungen eingegeben werden
**Wichtig:** Stellen Sie sicher, dass Git, CMake, Python und ffmpeg installiert sind (siehe oben unter ["Manuell zu installieren"](#️-manuell-zu-installieren-vor-start_appsh))


## Installation & Schnellstart

### Einfachste Methode (Empfohlen für alle Nutzer)

```bash
# 1. Repository klonen
git clone <dein-repo-url> V-SpeechFlow
cd V-SpeechFlow

# 2. App starten (macht alles automatisch!)
./start_app.sh
```

**Das war's!** Das Script:
- ✓ Prüft alle System-Dependencies (CMake, ffmpeg, PortAudio)
- ✓ Initialisiert Git-Submodule automatisch
- ✓ Erstellt ein Virtual Environment (`.venv`)
- ✓ Installiert Python-Dependencies im Virtual Environment
- ✓ Kompiliert das C++ Binary bei Bedarf
- ✓ Startet die GUI mit Installation Wizard

**Der Installation Wizard in der App hilft bei:**
- Modell-Download (verschiedene Größen zur Auswahl)
- HF-Token Eingabe für Speaker Diarization (optional)
- Erste Schritte Tutorial

### Manuelle Installation (Für CLI-Nutzer & Entwickler)

<details>
<summary>Klicken für detaillierte manuelle Installation</summary>

#### 1. Repository klonen

```bash
git clone <dein-repo-url> V-SpeechFlow
cd V-SpeechFlow
git submodule update --init --recursive
```

#### 2. Whisper-Modell herunterladen

Empfohlen für deutsche Sprache: **ggml-small.bin** (~500 MB)

```bash
# Automatisch mit Script
./download_model.sh

# Oder manuell
cd models
curl -L -o ggml-small.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
cd ..
```

**Andere Modelle:**
- `ggml-base.bin` (~150 MB) – Schneller, weniger genau
- `ggml-medium.bin` (~1.5 GB) – Höhere Genauigkeit für komplexe Aufnahmen
- `ggml-large-v3.bin` (~3 GB) – Beste Qualität, benötigt mehr RAM

#### 3. Projekt kompilieren

```bash
# Automatischer Build (empfohlen)
./build.sh

# Oder manuell
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j
cd ..
```

#### 4. Python-Dependencies installieren

**Wichtig für macOS:** Verwenden Sie ein Virtual Environment, um "externally-managed-environment" Fehler zu vermeiden.

```bash
# Virtual Environment erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# Hugging Face Token setzen (benötigt für Diarization)
# Empfohlen (macOS Keychain): Token sicher speichern und bei Bedarf laden
# (Service-Name: HF_V-Speechflow)
export HF_TOKEN="$(security find-generic-password -s HF_V-Speechflow -w)"
```

**Hinweis:** Das Virtual Environment muss für jede CLI-Nutzung aktiviert werden:
```bash
source .venv/bin/activate
```

**Hinweis zu PyAudio (Live-Recording):**
```bash
# Falls PyAudio-Installation fehlschlägt:
brew install portaudio

# Virtual Environment aktivieren, dann:
pip install pyaudio

# Bei Problemen mit M1/M2/M3:
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install pyaudio
```

</details>

## Nutzung der GUI

### App starten

```bash
./start_app.sh
```

### Hauptfunktionen der GUI

#### 1. **Audio-Datei transkribieren**
- Datei auswählen (MP3, M4A, WAV, FLAC, etc.)
- Modell wählen (Small, Medium, Large)
- Optional: Speaker Diarization aktivieren
- Optional: Anzahl Sprecher angeben
- "Start" klicken
- Fortschritt live verfolgen
- Ergebnis kopieren oder exportieren

#### 2. **Live-Aufnahme vom Mikrofon**
- Mikrofon auswählen
- "Record" drücken
- Sprechen (Volume-Anzeige beobachten)
- "Stop" drücken
- Automatische Transkription startet

#### 3. **Batch-Verarbeitung**
- Mehrere Dateien gleichzeitig transkribieren
- Einheitliche Einstellungen für alle Dateien
- Automatische Ausgabe in Zielordner

#### 4. **Profile & Einstellungen**
- Profile für verschiedene Szenarien speichern
  - Z.B. "Interview (2 Sprecher)"
  - Z.B. "Podcast (3-5 Sprecher)"
  - Z.B. "Meeting (Auto-Detection)"
- Einstellungen pro Profil:
  - Modell
  - Sprache
  - Diarization-Parameter
  - Ausgabeformat
- Schneller Wechsel zwischen Profilen

#### 5. **History & Export**
- Alle Transkriptionen werden gespeichert
- Jederzeit abrufbar
- Export in verschiedene Formate:
  - Plain Text
  - Segmente mit Timestamps
  - Speaker-Labels

### Eigenständige .app Bundle erstellen

Für eine "echte" macOS-App mit Icon im Finder:

```bash
# 1. App Bundle erstellen
./build_app.sh

# 2. App testen
open dist/V-SpeechFlow.app

# 3. Nach /Applications verschieben (optional)
mv dist/V-SpeechFlow.app /Applications/
```

**App-Größe:** Ca. 1-2 GB (enthält Python, PyQt6, PyTorch, etc.)

---

## Erweiterte Nutzung (CLI für Fortgeschrittene)

Die CLI ist für fortgeschrittene Nutzer, Automatisierung und Scripting gedacht. **Für die meisten Anwendungsfälle ist die GUI einfacher und komfortabler!**

**Wichtig:** Wenn Sie `./start_app.sh` verwendet haben, wurden die Dependencies in einem Virtual Environment (`.venv`) installiert. Aktivieren Sie dieses vor der CLI-Nutzung:

```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Dann CLI normal nutzen
python3 src/python/stt_cli.py -i audio.mp3 -m models/ggml-small.bin

# Nach Nutzung deaktivieren (optional)
deactivate
```

### Grundlegende CLI-Nutzung

### Live vom Mikrofon

```bash
# Einfache Live-Transkription
python3 src/python/stt_cli.py \
  --live \
  -m models/ggml-small.bin

# Mit Speaker Diarization (2 Sprecher)
python3 src/python/stt_cli.py \
  --live \
  -m models/ggml-small.bin \
  --diarize \
  --num-speakers 2 \
  -o transcript.txt

# Verfügbare Mikrofone auflisten
python3 src/python/stt_cli.py --list-devices
```

### Audio-Datei transkribieren

```bash
# Einfache deutsche Transkription
python3 src/python/stt_cli.py \
  -i audio.mp3 \
  -m models/ggml-small.bin

# Mit Timestamps
python3 src/python/stt_cli.py \
  -i audio.mp3 \
  -m models/ggml-small.bin \
  -s \
  -o transcript.txt
```

### Mit Speaker Diarization (Hauptfunktion)

```bash
# Interview mit 2 Sprechern
python3 src/python/stt_cli.py \
  -i interview.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --num-speakers 2 \
  -o transcript.txt

# Diskussion mit automatischer Sprecher-Erkennung
python3 src/python/stt_cli.py \
  -i diskussion.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --min-speakers 2 \
  --max-speakers 4

# Podcast/Meeting (optimiert für deutsche Sprache)
python3 src/python/stt_cli.py \
  -i meeting.m4a \
  -m models/ggml-small.bin \
  --diarize
```

### CLI-Optionen (Referenz)

```
Input (eines erforderlich):
-i, --input PATH          Audio-Datei (mp3, m4a, wav, ...)
--live                    Live vom Mikrofon aufnehmen

Live-Recording:
--list-devices            Verfügbare Mikrofone anzeigen
--device N                Mikrofon-Index auswählen

Allgemein:
-m, --model PATH          Pfad zum ggml-Modell
-o, --output PATH         Transkript in Datei schreiben
-s, --segments            Segmente mit Timestamps ausgeben
-t, --threads N           Anzahl Threads [default: 4]

Speaker Diarization (optimiert für Deutsch):
--diarize                 Speaker Diarization aktivieren
--num-speakers N          Exakte Anzahl Sprecher (z.B. 2 für Interview)
--min-speakers N          Minimale Anzahl für Auto-Detection
--max-speakers N          Maximale Anzahl für Auto-Detection
--hf-token TOKEN          Hugging Face Token

Weitere:
-l, --language CODE       Sprach-Code [default: de]
--translate               Ins Englische übersetzen
--keep-temp               Temporäre WAV-Datei behalten
```

<details>
<summary><strong>CLI Beispiele (Command Cookbook)</strong></summary>

### 1) Schnell: Datei → deutsches Transkript

```bash
python3 src/python/stt_cli.py \
  -i audio.mp3 \
  -m models/ggml-medium.bin
```

### 2) Datei → Transkript mit Timestamps (Segmente)

```bash
python3 src/python/stt_cli.py \
  -i meeting.m4a \
  -m models/ggml-medium.bin \
  -s \
  -o transcript_segments.txt
```

### 3) Live vom Mikrofon (Built-in) → Transkript

```bash
# Geräte anzeigen
python3 src/python/stt_cli.py --list-devices

# Aufnahme starten (Beispiel: Device 3 = MacBook Pro Microphone)
# Stoppen mit Ctrl+C → danach startet automatisch die Transkription
python3 src/python/stt_cli.py \
  --live \
  --device 3 \
  -m models/ggml-medium.bin
```

### 4) Live + Speaker Diarization mit Speaker-Cap (empfohlen für Meetings)

Wenn du weißt, dass z.B. bis zu 13 Personen teilnehmen, aber nicht alle sprechen,
ist ein Cap sinnvoll (nicht "erzwingen" mit `--num-speakers 13`).

```bash
python3 src/python/stt_cli.py \
  --live \
  --device 3 \
  -m models/ggml-medium.bin \
  --diarize \
  --min-speakers 1 \
  --max-speakers 13 \
  -o transcript_with_speakers.txt
```

### 5) Speaker Diarization: Exakt bekannte Anzahl (z.B. Interview)

```bash
python3 src/python/stt_cli.py \
  -i interview.mp3 \
  -m models/ggml-medium.bin \
  --diarize \
  --num-speakers 2 \
  -o transcript_interview.txt
```

### 6) Speaker Diarization: Token aus macOS Keychain verwenden (HF_V-Speechflow)

```bash
export HF_TOKEN="$(security find-generic-password -s HF_V-Speechflow -w)"

python3 src/python/stt_cli.py \
  -i meeting.m4a \
  -m models/ggml-medium.bin \
  --diarize \
  --min-speakers 1 \
  --max-speakers 13
```

### 7) Übersetzen (Deutsch → Englisch)

```bash
python3 src/python/stt_cli.py \
  -i audio.mp3 \
  -m models/ggml-medium.bin \
  --translate \
  -o transcript_en.txt
```

</details>

---

## Speaker Diarization - Deutsche Optimierung

V-SpeechFlow ist speziell für **deutsche Sprache** optimiert. **Diese Funktion ist sowohl in der GUI als auch per CLI verfügbar.**

### In der GUI nutzen

1. Diarization aktivieren (Checkbox)
2. Anzahl Sprecher angeben oder Auto-Detection wählen
3. HF-Token wird automatisch aus den Einstellungen geladen

### Optimierungen für Deutsch
- **Kürzere Pausenerkennung**: `min_duration_off=0.3s` (statt 0.5s Standard)
- **Smart-Merging**: Berücksichtigt typische deutsche Sprechpausen (0.4s)
- **Konservativeres Clustering**: Bessere Trennung bei ähnlichen Stimmen
- **Post-Processing**: Eliminiert kurze Füllwörter ("äh", "hmm")

### Anwendungsszenarien

**Interview (2 Personen):**

*In der GUI:* Diarization aktivieren → "Anzahl Sprecher: 2" → Start

*Per CLI:*
```bash
python3 src/python/stt_cli.py \
  -i interview.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --num-speakers 2
```

**Diskussion (2-4 Personen):**

*In der GUI:* Diarization aktivieren → "Min: 2, Max: 4" → Start

*Per CLI:*
```bash
python3 src/python/stt_cli.py \
  -i diskussion.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --min-speakers 2 \
  --max-speakers 4
```

**Meeting/Podcast (unbekannt):**

*In der GUI:* Diarization aktivieren → "Auto-Detection" → Start

*Per CLI:*
```bash
python3 src/python/stt_cli.py \
  -i meeting.m4a \
  -m models/ggml-small.bin \
  --diarize
```

**Ausgabe-Beispiel:**
```
=== SPEAKER_00 (45.2%) ===
[00:00:01.230 --> 00:00:04.560] Guten Tag, willkommen zu unserem Podcast.

=== SPEAKER_01 (54.8%) ===
[00:00:04.780 --> 00:00:08.920] Vielen Dank für die Einladung.
```

### Setup für Speaker Diarization

**In der GUI (Empfohlen):**
1. Installation Wizard beim ersten Start folgen
2. HF-Token eingeben (oder später in den Einstellungen)
3. Fertig!

**Manuell (für CLI-Nutzer):**
1. Hugging Face Account erstellen: [huggingface.co/join](https://huggingface.co/join)
2. Access Token erstellen unter Settings → Access Tokens
3. Modell-Zugriff akzeptieren: [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
4. Token setzen: 
   ```bash
   export HF_TOKEN=hf_your_token_here
   # Oder in macOS Keychain speichern
   security add-generic-password -s HF_V-Speechflow -a $USER -w "hf_your_token_here"
   ```

---

## Schnellstart - Deutsches Interview transkribieren

### Option 1: Als macOS App (Empfohlen für Endanwender)

```bash
# 1. Repository klonen
git clone <repo-url> V-SpeechFlow
cd V-SpeechFlow

# 2. App starten (macht alles automatisch!)
./start_app.sh
```

Die App:
✓ Prüft und installiert alle Dependencies automatisch  
✓ Kompiliert das Projekt bei Bedarf  
✓ Startet die GUI  
✓ Modell-Download und Token-Eingabe erfolgen in der App

### Option 2: CLI für fortgeschrittene Nutzer

```bash
# 1. Projekt aufsetzen
git clone <repo-url> V-SpeechFlow
cd V-SpeechFlow
git submodule update --init --recursive
./build.sh
./download_model.sh  # Wähle Option 3: ggml-small.bin

# 2. Virtual Environment & Python Dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export HF_TOKEN=hf_your_token_here

# 3. Audio transkribieren mit Speaker Diarization
python3 src/python/stt_cli.py \
  -i interview.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --num-speakers 2 \
  -o transcript.txt

# 4. Ergebnis ansehen
cat transcript.txt
```

## Projektstruktur

```
V-SpeechFlow/
├── CMakeLists.txt              # Haupt-CMake-Konfiguration
├── README.md                   # Diese Datei
├── APP_QUICK_START.md          # Quick Start Guide für die App
├── .gitignore
│
├── start_app.sh                # App-Launcher (empfohlen!)
├── build_app.sh                # .app Bundle erstellen
├── launch_app.py               # Python Launcher-Script
├── setup.py                    # py2app Konfiguration
│
├── src/
│   ├── gui/                    # PyQt6 GUI (NEU!)
│   │   ├── app.py              # Haupteinstiegspunkt
│   │   ├── main_window.py      # Hauptfenster
│   │   ├── installation_wizard.py  # Setup-Assistent
│   │   ├── input_panel.py      # Audio-Eingabe
│   │   ├── output_panel.py     # Ergebnisse
│   │   ├── settings_panel.py   # Einstellungen
│   │   ├── profiles.py         # Profilverwaltung
│   │   ├── history.py          # Verlauf
│   │   └── ...                 # Weitere GUI-Komponenten
│   │
│   ├── native/                 # C++-Komponente
│   │   ├── CMakeLists.txt
│   │   ├── main.cpp            # CLI-Argumente, Hauptprogramm
│   │   ├── wav_reader.{h,cpp}  # WAV-Datei-Handling
│   │   └── stt_engine.{h,cpp}  # Whisper.cpp Wrapper
│   │
│   └── python/                 # Python Layer
│       ├── stt_cli.py          # CLI mit ffmpeg
│       ├── diarization.py      # Speaker Diarization
│       └── live_recorder.py    # Live-Mikrofonaufnahme
│
├── third_party/
│   └── whisper.cpp/            # Git-Submodul
│
├── models/                     # Whisper-Modelle (.bin)
│   └── .gitkeep
│
├── history/                    # GUI: Gespeicherte Transkriptionen
│   └── history.json
│
└── build/                      # Build-Artefakte (gitignored)
    └── bin/
        └── stt_native          # Kompiliertes Binary
```

## Performance-Tipps für deutsche Sprache

### Modell-Wahl

**In der GUI:** Einfach im Installation Wizard oder in Einstellungen auswählen

- **Empfohlen**: `ggml-small.bin` (~500 MB) – Bester Kompromiss für Deutsch
- **Schneller**: `ggml-base.bin` (~150 MB) – Gut für einfache Aufnahmen
- **Genauer**: `ggml-medium.bin` (~1.5 GB) – Für komplexe Dialekte/Akzente

### Thread-Anzahl

**In der GUI:** Wird automatisch optimiert basierend auf Ihrer CPU

**Per CLI:**
```bash
# M1 Pro (8-10 Kerne): 6-8 Threads optimal
python3 src/python/stt_cli.py -i audio.mp3 -m models/ggml-small.bin -t 8

# M2/M3 Pro: 8-10 Threads
python3 src/python/stt_cli.py -i audio.mp3 -m models/ggml-small.bin -t 10
```

### Audio-Qualität für Diarization
- **Wichtig**: Klare Aufnahmen ohne starke Hintergrundgeräusche
- **Sprecher-Trennung**: Funktioniert besser bei unterschiedlichen Stimmen
- **Mikrofon**: Nah-Aufnahmen erhöhen Genauigkeit
- **Format**: Beliebig (MP3, M4A, WAV) – ffmpeg konvertiert automatisch

---

## Troubleshooting

### App startet nicht

**Lösung:**
```bash
# Führe den Launcher aus - er zeigt detaillierte Fehler
./start_app.sh
```

Der Launcher zeigt genau, welche Voraussetzungen fehlen.

### "externally-managed-environment" Fehler

**Problem:** Python (via Homebrew) erlaubt keine systemweiten pip-Installationen mehr.

**Lösung:** Die Scripts verwenden automatisch ein Virtual Environment (`.venv`). Falls Sie manuell Pakete installieren möchten:

```bash
# Virtual Environment erstellen (falls nicht vorhanden)
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate

# Pakete installieren
pip install -r requirements.txt

# App starten
python3 launch_app.py
```

### GUI zeigt Fehler beim Modell-Download

**Lösung:**
1. Überprüfe Internet-Verbindung
2. Versuche Download mit `./download_model.sh` manuell
3. Platziere das Modell manuell in `models/` oder "Git not found"

**Problem:** Diese Tools müssen manuell installiert werden.

**Lösung:**
```bash
# Git installieren (falls nicht vorhanden)
xcode-select --install
# oder
brew install git

# CMake installieren
brew install cmake

# Python installieren
brew install python@3.11

# ffmpeg installieren
brew install ffmpeg

# Optional: PortAudio für Live-Recording
brew install portaudio
# ffmpeg installieren
brew install ffmpeg

# Dann App neu starten
./start_app.sh
```

### Binary nicht gefunden (fortgeschrittene Nutzer)

```bash
# Prüfen ob kompiliert wurde
ls -la build/bin/stt_native

# Falls nicht: neu kompilieren
./build.sh
# oder
cd build
cmake --build . --config Release
```

### Submodul fehlt

```bash
# Submodule initialisieren
git submodule update --init --recursive

# Dann neu starten
./start_app.sh
```

### CMake-Fehler (fortgeschrittene Nutzer)

```bash
# Sauberer Build
rm -rf build
./build.sh
```

### Modell-Download schlägt fehl

**In der GUI:**
1. Überprüfe Internet-Verbindung
2. Versuche anderen Mirror im Wizard
3. Oder manuell: [Hugging Face](https://huggingface.co/ggerganov/whisper.cpp/tree/main)
4. Datei nach `models/` kopieren
5. In GUI unter Einstellungen → Modelle auswählen

**Per CLI:**
```bash
./download_model.sh
```

### Diarization funktioniert nicht

**In der GUI:**
1. Überprüfe ob HF-Token in Einstellungen eingetragen ist
2. Stelle sicher, dass pyannote.audio installiert ist: `pip install -r requirements.txt`
3. Akzeptiere Modell-Zugriff: [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

**Per CLI - "DIARIZATION_AVAILABLE = False":**
```bash
# Dependencies installieren
pip install -r requirements.txt

# Testen
python3 src/python/stt_cli.py --diarization-help
```

**Per CLI - "Hugging Face Token fehlt":**
```bash
# Token setzen
export HF_TOKEN=hf_your_token_here

# Alternativ (macOS Keychain)
security add-generic-password -s HF_V-Speechflow -a $USER -w "hf_your_token_here"
export HF_TOKEN="$(security find-generic-password -s HF_V-Speechflow -w)"
```

### Live-Recording funktioniert nicht

**Mikrofonzugriff verweigert:**
1. macOS: Systemeinstellungen → Datenschutz & Sicherheit → Mikrofon
2. Erlaube Zugriff für Terminal/Python/V-SpeechFlow
3. App neu starten

**"PyAudio nicht verfügbar":**
```bash
# Installation
brew install portaudio
pip install pyaudio

# Bei M1/M2/M3 Problemen:
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install pyaudio

# Dann App neu starten
./start_app.sh
```

**Kein Audio aufgenommen:**
- Mikrofon-Pegel in macOS Systemeinstellungen prüfen
- In der GUI: Anderes Mikrofon aus Dropdown wählen
- Per CLI: `python3 src/python/stt_cli.py --list-devices`

---

## Entwicklung

Detaillierte Informationen für Entwickler finden sich in `.github/copilot-instructions.md`.

### Architektur (3-Schicht-System)
- **GUI Layer** (`src/gui/`): PyQt6-Benutzeroberfläche mit Wizard, Profilen, History
- **Python Layer** (`src/python/`): CLI, ffmpeg-Integration, Diarization, Live-Recording
- **C++ Layer** (`src/native/`): Performance-kritische Audio-Verarbeitung mit whisper.cpp

### Development Mode

```bash
# Hot Reloading während der Entwicklung
./dev.sh

# Normaler GUI-Start (verwendet automatisch .venv)
python3 launch_app.py

# Für manuelle Entwicklung: Virtual Environment aktivieren
source .venv/bin/activate

# Tests ausführen
pytest tests/
```

### Code-Erweiterungen
- Neue GUI-Features: In `src/gui/` neue Panels oder Komponenten hinzufügen
- Neue Ausgabeformate: `src/native/stt_engine.cpp` erweitern
- Diarization-Optimierung: `src/python/diarization.py` anpassen
- Build-System: `CMakeLists.txt` für neue Dependencies

---

## Credits & Lizenz

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) von Georgi Gerganov (MIT License)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) für Speaker Diarization (MIT License)
- [OpenAI Whisper](https://github.com/openai/whisper) – Original-Modelle

**V-SpeechFlow** – Optimiert für deutsche Sprache mit offline-first Ansatz
