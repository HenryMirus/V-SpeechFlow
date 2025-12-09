#!/bin/bash
# Download-Skript für Whisper-Modelle

set -e

echo "======================================="
echo "  Whisper Model Downloader"
echo "======================================="
echo ""

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

BASE_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

# Verfügbare Modelle
echo "Available models:"
echo ""
echo "  Multilingual (includes German):"
echo "    1) tiny       (~75 MB)   - Fast, low accuracy"
echo "    2) base       (~150 MB)  - Good balance"
echo "    3) small      (~500 MB)  - Recommended for German"
echo "    4) medium     (~1.5 GB)  - Higher accuracy"
echo "    5) large-v3   (~3 GB)    - Best quality"
echo ""
echo "  English-only:"
echo "    6) tiny.en    (~75 MB)"
echo "    7) base.en    (~150 MB)"
echo "    8) small.en   (~500 MB)"
echo "    9) medium.en  (~1.5 GB)"
echo ""
echo "  0) Exit"
echo ""

read -p "Select model to download (0-9): " choice

case $choice in
    1)
        MODEL="ggml-tiny.bin"
        ;;
    2)
        MODEL="ggml-base.bin"
        ;;
    3)
        MODEL="ggml-small.bin"
        ;;
    4)
        MODEL="ggml-medium.bin"
        ;;
    5)
        MODEL="ggml-large-v3.bin"
        ;;
    6)
        MODEL="ggml-tiny.en.bin"
        ;;
    7)
        MODEL="ggml-base.en.bin"
        ;;
    8)
        MODEL="ggml-small.en.bin"
        ;;
    9)
        MODEL="ggml-medium.en.bin"
        ;;
    0)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

TARGET="$MODELS_DIR/$MODEL"

if [ -f "$TARGET" ]; then
    echo ""
    echo "Model already exists: $TARGET"
    read -p "Overwrite? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Skipping download."
        exit 0
    fi
fi

echo ""
echo "Downloading $MODEL..."
echo "URL: $BASE_URL/$MODEL"
echo "Target: $TARGET"
echo ""

curl -L --progress-bar -o "$TARGET" "$BASE_URL/$MODEL"

echo ""
echo "Download complete!"
echo ""
echo "File: $TARGET"
echo "Size: $(ls -lh "$TARGET" | awk '{print $5}')"
echo ""
echo "Usage:"
echo "  ./src/python/stt_cli.py -f audio.mp3 -m $TARGET"
echo ""
