#!/bin/bash
# V-SpeechFlow App Builder
# Erstellt eine eigenständige macOS .app Bundle

set -e  # Exit bei Fehler

echo "═══════════════════════════════════════════════════════════"
echo "V-SpeechFlow App Builder"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Prüfe Voraussetzungen
print_info "Prüfe System-Dependencies..."

if ! command -v cmake &> /dev/null; then
    print_error "CMake ist nicht installiert"
    echo "Installiere mit: brew install cmake"
    exit 1
fi
print_success "CMake gefunden"

if ! command -v ffmpeg &> /dev/null; then
    print_error "ffmpeg ist nicht installiert"
    echo "Installiere mit: brew install ffmpeg"
    exit 1
fi
print_success "ffmpeg gefunden"

# Prüfe ob PortAudio installiert ist
if ! brew list portaudio &> /dev/null; then
    print_warning "PortAudio nicht installiert (optional für Live-Recording)"
    echo "Installiere mit: brew install portaudio"
fi

# Prüfe Git-Submodule
print_info "Prüfe Git-Submodule..."
if [ ! -f "third_party/whisper.cpp/CMakeLists.txt" ]; then
    print_warning "whisper.cpp Submodul nicht initialisiert"
    print_info "Initialisiere Submodule..."
    git submodule update --init --recursive
fi
print_success "Submodule vorhanden"

# Erstelle Virtual Environment falls nicht vorhanden
print_info "Richte Virtual Environment ein..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Virtual Environment erstellt"
else
    print_success "Virtual Environment vorhanden"
fi

# Aktiviere Virtual Environment
source .venv/bin/activate

# Kompiliere C++ Binary
print_info "Kompiliere C++ Binary..."
if [ ! -d "build" ]; then
    mkdir build
fi

cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j
cd ..

if [ ! -f "build/bin/stt_native" ]; then
    print_error "Kompilierung fehlgeschlagen - Binary nicht gefunden"
    exit 1
fi
print_success "C++ Binary kompiliert"

# Python Dependencies installieren
print_info "Installiere Python Dependencies im Virtual Environment..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install -r requirements.txt
print_success "Python Dependencies installiert"

# App Bundle erstellen
print_info "Erstelle macOS App Bundle..."

# Aufräumen alter Builds
if [ -d "dist" ]; then
    rm -rf dist
fi
if [ -d "build_app" ]; then
    rm -rf build_app
fi

# py2app ausführen
python3 setup.py py2app

if [ ! -d "dist/V-SpeechFlow.app" ]; then
    print_error "App-Bundle konnte nicht erstellt werden"
    exit 1
fi

print_success "App Bundle erstellt"

# Prüfe App-Größe
APP_SIZE=$(du -sh dist/V-SpeechFlow.app | cut -f1)
print_info "App-Größe: $APP_SIZE"

echo ""
echo "═══════════════════════════════════════════════════════════"
print_success "Build erfolgreich abgeschlossen!"
echo "═══════════════════════════════════════════════════════════"
echo ""
print_info "Die App befindet sich hier: $(pwd)/dist/V-SpeechFlow.app"
echo ""
echo "Nächste Schritte:"
echo "  1. App testen:     open dist/V-SpeechFlow.app"
echo "  2. App verschieben: mv dist/V-SpeechFlow.app /Applications/"
echo "  3. DMG erstellen:   ./create_dmg.sh (optional)"
echo ""
