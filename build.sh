#!/bin/bash
# Build-Skript für V-SpeechFlow auf macOS (Apple Silicon)

set -e  # Bei Fehler abbrechen

echo "======================================="
echo "  V-SpeechFlow Build Script"
echo "======================================="
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Voraussetzungen prüfen
echo "Checking prerequisites..."

# CMake
if ! command -v cmake &> /dev/null; then
    echo -e "${RED}Error: CMake not found. Install with: brew install cmake${NC}"
    exit 1
fi
echo -e "${GREEN}✓ CMake found: $(cmake --version | head -n1)${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found. Install with: brew install python@3.11${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"

# ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}Warning: ffmpeg not found. Install with: brew install ffmpeg${NC}"
    echo -e "${YELLOW}         (Required for Python CLI)${NC}"
else
    echo -e "${GREEN}✓ ffmpeg found: $(ffmpeg -version | head -n1)${NC}"
fi

echo ""

# whisper.cpp Submodul prüfen
if [ ! -f "third_party/whisper.cpp/CMakeLists.txt" ]; then
    echo -e "${RED}Error: whisper.cpp submodule not found!${NC}"
    echo "Run: git submodule update --init --recursive"
    exit 1
fi
echo -e "${GREEN}✓ whisper.cpp submodule found${NC}"

echo ""
echo "======================================="
echo "  Building C++ Components"
echo "======================================="
echo ""

# Build-Verzeichnis erstellen
mkdir -p build
cd build

# CMake konfigurieren
echo "Configuring CMake..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES=arm64

echo ""
echo "Compiling (this may take a few minutes)..."

# Anzahl CPU-Kerne ermitteln
NPROC=$(sysctl -n hw.ncpu)
echo "Using $NPROC parallel jobs"

# Kompilieren
cmake --build . --config Release -j $NPROC

echo ""
echo "======================================="
echo "  Build Complete!"
echo "======================================="
echo ""

# Binary prüfen
if [ -f "bin/stt_native" ]; then
    echo -e "${GREEN}✓ Binary created: build/bin/stt_native${NC}"
    
    # Dateigröße anzeigen
    SIZE=$(ls -lh bin/stt_native | awk '{print $5}')
    echo "  Size: $SIZE"
    
    # Architektur prüfen
    ARCH=$(file bin/stt_native | grep -o "arm64" || echo "unknown")
    echo "  Architecture: $ARCH"
else
    echo -e "${RED}✗ Binary not found! Build may have failed.${NC}"
    exit 1
fi

echo ""

# Python-CLI ausführbar machen
cd ..
chmod +x src/python/stt_cli.py
echo -e "${GREEN}✓ Python CLI made executable${NC}"

echo ""
echo "======================================="
echo "  Next Steps"
echo "======================================="
echo ""
echo "1. Download a Whisper model:"
echo "   cd models"
echo "   curl -L -o ggml-small.bin \\"
echo "     https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
echo ""
echo "2. Test the binary:"
echo "   ./build/bin/stt_native --help"
echo ""
echo "3. Use the Python CLI:"
echo "   ./src/python/stt_cli.py -i audio.mp3 -m models/ggml-small.bin"
echo ""
echo "See README.md for more information."
echo ""
