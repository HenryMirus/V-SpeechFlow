# V-SpeechFlow

Lokales, offline Speech-to-Text-System für **deutsche Sprache** mit Speaker Diarization. Optimiert für macOS (Apple Silicon), basierend auf [whisper.cpp](https://github.com/ggerganov/whisper.cpp).

## Features

- ✅ **Komplett offline** – keine Cloud-Verbindung erforderlich
- ✅ **Live-Aufnahme** – Direkt vom macOS Mikrofonarray transkribieren
- ✅ **Optimiert für deutsche Sprache** – Speaker Diarization für deutsche Konversationen
- ✅ **Apple Silicon optimiert** (M1/M2/M3) mit MPS-Acceleration
- ✅ **Multi-Format-Support** – mp3, m4a, wav, etc. (via ffmpeg)
- ✅ **Speaker Diarization** – Automatische Sprechererkennung mit deutschen Parametern
- ✅ **Flexible Ausgabe** – Plain-Text oder Segmente mit Timestamps und Sprecher-Zuordnung
- ✅ **Zwei-Schicht-Architektur** – Native C++-Engine + Python-CLI

## Architektur

```
┌─────────────────────────────────────┐
│   Python CLI (stt_cli.py)          │
│   - Audio-Konvertierung (ffmpeg)   │
│   - Benutzerfreundliche Argumente  │
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

### Software
- **CMake** 3.20+: `brew install cmake`
- **Python** 3.10+: `brew install python@3.11`
- **ffmpeg**: `brew install ffmpeg`
- **Xcode Command Line Tools**: `xcode-select --install`

### Live-Recording (für --live Modus)
- **PortAudio**: `brew install portaudio`
- **PyAudio**: `pip install pyaudio`

### Speaker Diarization (empfohlen)
- **pyannote.audio**: `pip install -r requirements.txt`
- **Hugging Face Account**: Kostenlos registrieren auf [huggingface.co](https://huggingface.co)
- **HF Token**: Nach Registrierung unter Settings → Access Tokens erstellen

## Installation

### 1. Repository klonen

```bash
git clone <dein-repo-url> V-SpeechFlow
cd V-SpeechFlow
git submodule update --init --recursive
```

### 2. Whisper-Modell herunterladen

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

### 3. Projekt kompilieren

```bash
# Automatischer Build (empfohlen)
./build.sh

# Oder manuell
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j
cd ..
```

### 4. Python-Dependencies installieren

```bash
# Alle Dependencies (Diarization + Live-Recording)
pip install -r requirements.txt

# Hugging Face Token setzen (benötigt für Diarization)
export HF_TOKEN=hf-1231245123123
```

**Hinweis zu PyAudio (Live-Recording):**
```bash
# Falls PyAudio-Installation fehlschlägt:
brew install portaudio
pip install pyaudio

# Bei Problemen mit M1/M2/M3:
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install pyaudio
```

## Nutzung

### Live vom Mikrofon (NEU!)

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

# Bestimmtes Mikrofon wählen
python3 src/python/stt_cli.py \
  --live \
  --device 0 \
  -m models/ggml-small.bin
```

**Live-Workflow:**
1. Starte Aufnahme mit `--live`
2. Sprich ins Mikrofon (Volume-Anzeige: 🔊 ████████)
3. Stoppe mit `Ctrl+C`
4. Transkription wird automatisch verarbeitet

### Grundlegende Transkription

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
  --diarize \
  --hf-token $HF_TOKEN
```

**Wichtige Optionen:**
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



## Speaker Diarization - Deutsche Optimierung

V-SpeechFlow ist speziell für **deutsche Sprache** optimiert:

### Optimierungen für Deutsch
- **Kürzere Pausenerkennung**: `min_duration_off=0.3s` (statt 0.5s Standard)
- **Smart-Merging**: Berücksichtigt typische deutsche Sprechpausen (0.4s)
- **Konservativeres Clustering**: Bessere Trennung bei ähnlichen Stimmen
- **Post-Processing**: Eliminiert kurze Füllwörter ("äh", "hmm")

### Anwendungsszenarien

**Interview (2 Personen):**
```bash
python3 src/python/stt_cli.py \
  -i interview.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --num-speakers 2
```

**Diskussion (2-4 Personen):**
```bash
python3 src/python/stt_cli.py \
  -i diskussion.mp3 \
  -m models/ggml-small.bin \
  --diarize \
  --min-speakers 2 \
  --max-speakers 4
```

**Meeting/Podcast (unbekannt):**
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

**Setup:**
1. Hugging Face Account erstellen: [huggingface.co/join](https://huggingface.co/join)
2. Access Token erstellen unter Settings → Access Tokens
3. Modell-Zugriff akzeptieren: [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
4. Token setzen: `export HF_TOKEN=hf_your_token_here`

## Schnellstart - Deutsches Interview transkribieren

```bash
# 1. Projekt aufsetzen
git clone <repo-url> V-SpeechFlow
cd V-SpeechFlow
git submodule update --init --recursive
./build.sh
./download_model.sh  # Wähle Option 3: ggml-small.bin

# 2. Python Dependencies
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
├── .gitignore
│
├── src/
│   ├── native/                 # C++-Komponente
│   │   ├── CMakeLists.txt
│   │   ├── main.cpp            # CLI-Argumente, Hauptprogramm
│   │   ├── wav_reader.{h,cpp}  # WAV-Datei-Handling
│   │   └── stt_engine.{h,cpp}  # Whisper.cpp Wrapper
│   │
│   └── python/                 # Python-CLI
│       ├── stt_cli.py          # Komfortable CLI mit ffmpeg
│       ├── diarization.py      # Speaker Diarization Modul
│       └── live_recorder.py    # Live-Mikrofonaufnahme (NEU)
│
├── third_party/
│   └── whisper.cpp/            # Git-Submodul
│
├── models/                     # Whisper-Modelle (.bin)
│   └── .gitkeep
│
├── test_data/                  # Test-Audiodateien
│   └── .gitkeep
│
└── build/                      # Build-Artefakte (gitignored)
    └── bin/
        └── stt_native          # Kompiliertes Binary
```

## Performance-Tipps für deutsche Sprache

### Modell-Wahl
- **Empfohlen**: `ggml-small.bin` (~500 MB) – Bester Kompromiss für Deutsch
- **Schneller**: `ggml-base.bin` (~150 MB) – Gut für einfache Aufnahmen
- **Genauer**: `ggml-medium.bin` (~1.5 GB) – Für komplexe Dialekte/Akzente

### Thread-Anzahl
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

## Troubleshooting

### Binary nicht gefunden
```bash
# Prüfen ob kompiliert wurde
ls -la build/bin/stt_native

# Falls nicht: neu kompilieren
cd build
cmake --build . --config Release
```

### ffmpeg-Fehler
```bash
# ffmpeg installieren
brew install ffmpeg

# Version prüfen
ffmpeg -version
```

### Submodul fehlt
```bash
# Submodule initialisieren
git submodule update --init --recursive
```

### CMake-Fehler
```bash
# Sauberer Build
rm -rf build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
```

### Modell-Download schlägt fehl
- Manueller Download von [Hugging Face](https://huggingface.co/ggerganov/whisper.cpp/tree/main)
- Datei nach `models/` kopieren
- Dateigröße prüfen (z.B. `ggml-small.bin` sollte ~500 MB sein)

### Diarization-Fehler

**"DIARIZATION_AVAILABLE = False":**
```bash
# Dependencies installieren
pip install -r requirements.txt

# Testen
python3 src/python/stt_cli.py --diarization-help
```

**"Hugging Face Token fehlt":**
```bash
# Token setzen
export HF_TOKEN=hf_your_token_here

# Oder direkt beim Aufruf
python3 src/python/stt_cli.py -i audio.mp3 --diarize --hf-token hf_xxx
```

**"Modell-Zugriff verweigert":**
1. Besuche [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
2. "Agree and access repository" akzeptieren
3. Token neu erstellen falls nötig

### Live-Recording-Fehler

**"PyAudio nicht verfügbar":**
```bash
# Installation
brew install portaudio
pip install pyaudio

# Bei M1/M2/M3 Problemen:
CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install pyaudio
```

**"Mikrofonzugriff verweigert":**
1. Systemeinstellungen → Datenschutz & Sicherheit → Mikrofon
2. Terminal (oder Python) Zugriff erlauben
3. Terminal neu starten

**"Keine Audio-Daten aufgenommen":**
- Mikrofon-Pegel in macOS Systemeinstellungen prüfen
- Anderes Mikrofon mit `--list-devices` und `--device N` wählen
- Volume-Anzeige während Aufnahme beobachten (sollte █ zeigen)

## Entwicklung

Detaillierte Informationen für Entwickler finden sich in `.github/copilot-instructions.md`.

### Architektur
- **C++ Layer** (`src/native/`): Performance-kritische Audio-Verarbeitung
- **Python Layer** (`src/python/`): CLI, ffmpeg-Integration, Diarization
- **whisper.cpp**: Git-Submodul für STT-Engine

### Code-Erweiterungen
- Neue Ausgabeformate: `src/native/stt_engine.cpp` erweitern
- Diarization-Optimierung: `src/python/diarization.py` anpassen
- Build-System: `CMakeLists.txt` für Dependencies

## Credits & Lizenz

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) von Georgi Gerganov (MIT License)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) für Speaker Diarization (MIT License)
- [OpenAI Whisper](https://github.com/openai/whisper) – Original-Modelle

**V-SpeechFlow** – Optimiert für deutsche Sprache mit offline-first Ansatz
