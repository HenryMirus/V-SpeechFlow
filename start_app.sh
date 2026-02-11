#!/bin/bash
# V-SpeechFlow Schnellstart
# Startet die App direkt ohne Build (nutzt launch_app.py)

set -e

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           V-SpeechFlow - Offline Speech-to-Text          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Info über Virtual Environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}ℹ Beim ersten Start wird ein Virtual Environment erstellt...${NC}"
    echo ""
fi

# Launcher ausführen
python3 launch_app.py
