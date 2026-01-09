#!/usr/bin/env python3
"""
V-SpeechFlow CLI - Komfortables Speech-to-Text Tool

Konvertiert Audio-Dateien automatisch ins richtige Format und ruft
das native STT-Binary auf. Optional mit Speaker Diarization.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple

import hf_token as hf_token_container

# Füge src/python zum Pfad hinzu für Modul-Imports
_script_dir = Path(__file__).parent.resolve()
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# Diarization-Modul (optional)
try:
    from diarization import (
        SpeakerDiarizer, 
        check_diarization_available, 
        print_diarization_help
    )
    DIARIZATION_MODULE_AVAILABLE = True
except ImportError:
    DIARIZATION_MODULE_AVAILABLE = False

# Live-Recording-Modul (optional)
try:
    from live_recorder import LiveRecorder
    LIVE_RECORDING_AVAILABLE = True
except ImportError:
    LIVE_RECORDING_AVAILABLE = False


class AudioConverter:
    """Konvertiert Audio-Dateien mit ffmpeg nach 16kHz mono WAV"""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Prüft ob ffmpeg installiert ist"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def convert_to_wav(input_file: Path, output_file: Path) -> bool:
        """
        Konvertiert Audio-Datei nach 16kHz, mono, 16-bit PCM WAV

        Args:
            input_file: Quell-Audiodatei
            output_file: Ziel-WAV-Datei

        Returns:
            True bei Erfolg
        """
        try:
            cmd = [
                "ffmpeg",
                "-i", str(input_file),
                "-ar", "16000",        # 16kHz
                "-ac", "1",            # Mono
                "-sample_fmt", "s16",  # 16-bit
                "-y",                  # Überschreiben
                str(output_file)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error: ffmpeg conversion failed: {e.stderr.decode()}", file=sys.stderr)
            return False


class STTClient:
    """Client für das native STT-Binary"""

    def __init__(self, binary_path: Path, model_path: Path):
        self.binary_path = binary_path
        self.model_path = model_path

    def transcribe(
        self,
        wav_file: Path,
        language: str = "de",
        num_threads: int = 4,
        show_segments: bool = False,
        translate: bool = False,
        output_file: Optional[Path] = None
    ) -> Optional[str]:
        """
        Ruft das native STT-Binary auf

        Args:
            wav_file: Pfad zur WAV-Datei (16kHz, mono)
            language: Sprach-Code
            num_threads: Anzahl Threads
            show_segments: Segmente mit Timestamps ausgeben
            translate: Ins Englische übersetzen
            output_file: Optional: Ausgabe in Datei schreiben

        Returns:
            Transkript oder None bei Fehler
        """
        if not self.binary_path.exists():
            print(f"Error: STT binary not found at {self.binary_path}", file=sys.stderr)
            return None

        if not self.model_path.exists():
            print(f"Error: Model file not found at {self.model_path}", file=sys.stderr)
            return None

        cmd = [
            str(self.binary_path),
            "-m", str(self.model_path),
            "-f", str(wav_file),
            "-l", language,
            "-t", str(num_threads)
        ]

        if show_segments:
            cmd.append("-s")

        if translate:
            cmd.append("--translate")

        if output_file:
            cmd.extend(["-o", str(output_file)])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            # STDERR für Logs, STDOUT für Transkript (wenn nicht in Datei)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"Error: Transcription failed: {e.stderr}", file=sys.stderr)
            return None
    
    def parse_segments_from_output(self, output: str) -> List[Tuple[float, float, str]]:
        """
        Parst Transkript-Segmente aus stt_native Ausgabe
        
        Format: [HH:MM:SS.mmm --> HH:MM:SS.mmm] Text
        
        Returns:
            Liste von (start_sec, end_sec, text) Tupeln
        """
        segments = []
        pattern = r'\[(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})\]\s*(.+)'
        
        for line in output.split('\n'):
            match = re.match(pattern, line)
            if match:
                h1, m1, s1, ms1, h2, m2, s2, ms2, text = match.groups()
                
                start = int(h1)*3600 + int(m1)*60 + int(s1) + int(ms1)/1000.0
                end = int(h2)*3600 + int(m2)*60 + int(s2) + int(ms2)/1000.0
                
                segments.append((start, end, text.strip()))
        
        return segments


def format_timestamp(seconds: float) -> str:
    """Formatiert Sekunden als HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def main():
    parser = argparse.ArgumentParser(
        description="V-SpeechFlow - Offline Speech-to-Text mit Speaker Diarization für deutsche Sprache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einfache Transkription (Deutsch)
  %(prog)s -i audio.mp3 -m models/ggml-small.bin

  # Mit Speaker Diarization (2 Sprecher)
  %(prog)s -i interview.mp3 -m models/ggml-small.bin --diarize --num-speakers 2

  # Diskussion mit Auto-Detection
  %(prog)s -i meeting.m4a -m models/ggml-small.bin --diarize --min-speakers 2 --max-speakers 4
        """
    )

    # Input-Gruppe: Audio-Datei ODER Live-Aufnahme (nicht erforderlich für --list-devices/--diarization-help)
    input_group = parser.add_mutually_exclusive_group(required=False)
    
    input_group.add_argument(
        "-i", "--input",
        dest="file",
        type=Path,
        help="Audio-Datei (mp3, m4a, wav, ...)"
    )
    
    input_group.add_argument(
        "--live",
        action="store_true",
        help="Live vom Mikrofon aufnehmen (Ctrl+C zum Stoppen)"
    )
    
    # Live-Recording Optionen
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Verfügbare Audio-Eingabegeräte auflisten und beenden"
    )
    
    parser.add_argument(
        "--device",
        type=int,
        help="Audio-Geräte-Index für Live-Aufnahme (Standard: System-Default)"
    )

    parser.add_argument(
        "-m", "--model",
        type=Path,
        required=False,  # Optional für --list-devices und --diarization-help
        help="Pfad zum ggml-Whisper-Modell (.bin)"
    )

    parser.add_argument(
        "-l", "--language",
        type=str,
        default="de",
        help="Sprach-Code (de, en, fr, ...) (default: de)"
    )

    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=4,
        help="Anzahl Threads (default: 4)"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Transkript in Datei schreiben"
    )

    parser.add_argument(
        "-s", "--segments",
        action="store_true",
        help="Segmente mit Timestamps ausgeben"
    )

    parser.add_argument(
        "--translate",
        action="store_true",
        help="Ins Englische übersetzen"
    )

    parser.add_argument(
        "--binary",
        type=Path,
        default=None,
        help="Pfad zum stt_native Binary (default: auto-detect)"
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Temporäre WAV-Datei behalten (Debug)"
    )

    # Speaker Diarization Optionen
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Speaker Diarization aktivieren (erfordert pyannote.audio)"
    )

    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Erwartete Anzahl Sprecher (None = auto-detect)"
    )

    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Minimale Anzahl Sprecher für Auto-Detection"
    )

    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Maximale Anzahl Sprecher für Auto-Detection"
    )

    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face Token für pyannote Modelle (oder via HF_TOKEN env var)"
    )

    parser.add_argument(
        "--diarization-help",
        action="store_true",
        help="Zeigt Setup-Hilfe für Speaker Diarization"
    )

    args = parser.parse_args()

    # Diarization-Hilfe
    if args.diarization_help:
        if DIARIZATION_MODULE_AVAILABLE:
            print_diarization_help()
        else:
            print("Error: diarization.py module not found", file=sys.stderr)
        sys.exit(0)
    
    # Geräte-Liste anzeigen
    if args.list_devices:
        if not LIVE_RECORDING_AVAILABLE:
            print("Fehler: Live-Recording nicht verfügbar.", file=sys.stderr)
            print("Installation:", file=sys.stderr)
            print("  brew install portaudio", file=sys.stderr)
            print("  pip install pyaudio", file=sys.stderr)
            sys.exit(1)
        
        try:
            recorder = LiveRecorder()
            recorder.list_devices()
            recorder.cleanup()
        except Exception as e:
            print(f"Fehler: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Model ist erforderlich für normale Operationen
    if not args.model and not args.list_devices and not args.diarization_help:
        print("Error: -m/--model ist erforderlich", file=sys.stderr)
        sys.exit(1)
    
    # Input ist erforderlich für normale Operationen
    if not args.file and not args.live and not args.list_devices and not args.diarization_help:
        print("Error: -i/--input oder --live ist erforderlich", file=sys.stderr)
        sys.exit(1)

    # Validierung für Datei-Input
    if args.file and not args.file.exists():
        print(f"Error: Audio file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if not args.model.exists():
        print(f"Error: Model file not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    # Binary-Pfad ermitteln
    if args.binary:
        binary_path = args.binary
    else:
        # Auto-detect: build/bin/stt_native oder src/native/stt_native
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent.parent
        
        candidates = [
            repo_root / "build" / "bin" / "stt_native",
            repo_root / "bin" / "stt_native",
        ]
        
        binary_path = None
        for candidate in candidates:
            if candidate.exists():
                binary_path = candidate
                break
        
        if not binary_path:
            print("Error: stt_native binary not found. Build the project first.", file=sys.stderr)
            print("Tried:", file=sys.stderr)
            for c in candidates:
                print(f"  - {c}", file=sys.stderr)
            sys.exit(1)

    print(f"V-SpeechFlow CLI\n")
    print(f"Using binary: {binary_path}")
    print(f"Using model:  {args.model}")
    if args.file:
        print(f"Input file:   {args.file}\n")
    elif args.live:
        print(f"Input:        Live-Mikrofon\n")

    # Temporäre WAV-Datei vorbereiten
    temp_wav = None
    cleanup_temp = False
    
    # Live-Recording-Modus
    if args.live:
        if not LIVE_RECORDING_AVAILABLE:
            print("Fehler: Live-Recording nicht verfügbar.", file=sys.stderr)
            print("Installation:", file=sys.stderr)
            print("  brew install portaudio", file=sys.stderr)
            print("  pip install pyaudio", file=sys.stderr)
            sys.exit(1)
        
        print("=== Live-Aufnahme ===\n")
        
        # Temporäre Datei für Aufnahme
        if args.keep_temp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_wav = Path(f"recording_{timestamp}.wav")
        else:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_wav = Path(temp_file.name)
            temp_file.close()
            cleanup_temp = True
        
        # Live-Recorder initialisieren
        recorder = LiveRecorder()
        
        try:
            recorder.start_recording(device_index=args.device)
            
            # Aufnehmen bis Ctrl+C
            while True:
                recorder.record_chunk()
        
        except KeyboardInterrupt:
            print("\n\nStoppe Aufnahme...")
        
        except Exception as e:
            print(f"\nFehler bei Aufnahme: {e}", file=sys.stderr)
            recorder.cleanup()
            sys.exit(1)
        
        finally:
            recorder.stop_recording()
            
            # Prüfe ob Audio aufgenommen wurde
            if not recorder.frames:
                print("Keine Audio-Daten aufgenommen!", file=sys.stderr)
                recorder.cleanup()
                sys.exit(1)
            
            recorder.save_wav(temp_wav)
            recorder.cleanup()
        
        wav_file = temp_wav
        print()
    
    # Datei-basierter Modus
    else:
        # ffmpeg prüfen
        if not AudioConverter.is_ffmpeg_available():
            print("Error: ffmpeg not found. Install with: brew install ffmpeg", file=sys.stderr)
            sys.exit(1)

        # Dateiendung prüfen - WAV direkt verwenden, sonst konvertieren
        needs_conversion = args.file.suffix.lower() != ".wav"
        
        if needs_conversion:
            print("Converting audio to 16kHz mono WAV...")
            
            if args.keep_temp:
                temp_wav = args.file.with_suffix(".temp.wav")
            else:
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_wav = Path(temp_file.name)
                temp_file.close()
            
            cleanup_temp = True

            converter = AudioConverter()
            if not converter.convert_to_wav(args.file, temp_wav):
                sys.exit(2)
            
            wav_file = temp_wav
            print(f"Converted to: {wav_file}\n")
        else:
            wav_file = args.file
            print("Using WAV file directly (ensure it's 16kHz mono!)\n")

    # Speaker Diarization (optional)
    speaker_segments = None
    if args.diarize:
        if not DIARIZATION_MODULE_AVAILABLE:
            print("Error: Diarization module not available.", file=sys.stderr)
            print("Install with: pip install pyannote.audio torch torchaudio", file=sys.stderr)
            print("Or run: --diarization-help for setup instructions", file=sys.stderr)
            sys.exit(4)
        
        if not check_diarization_available():
            print("Error: pyannote.audio not installed.", file=sys.stderr)
            print("Install with: pip install pyannote.audio torch torchaudio", file=sys.stderr)
            sys.exit(4)
        
        print("=== Speaker Diarization ===\n")
        
        # HF Token aus CLI/env/Keychain (cached)
        hf_token_value = hf_token_container.get_hf_token(args.hf_token)
        if not hf_token_value:
            print("Error: Hugging Face token required for diarization", file=sys.stderr)
            print("Set via: export HF_TOKEN='your_token'", file=sys.stderr)
            print("Or use: --hf-token argument", file=sys.stderr)
            print("Or store in Keychain service: HF_V-Speechflow", file=sys.stderr)
            print("  export HF_TOKEN=\"$(security find-generic-password -s HF_V-Speechflow -w)\"", file=sys.stderr)
            print("\nRun --diarization-help for setup instructions", file=sys.stderr)
            sys.exit(4)
        
        # Diarizer initialisieren
        diarizer = SpeakerDiarizer(hf_token=hf_token_value, optimize_for_german=True)
        if not diarizer.initialize():
            sys.exit(4)
        
        # Diarization durchführen
        speaker_segments = diarizer.diarize(
            wav_file, 
            num_speakers=args.num_speakers,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers
        )
        
        print(f"\n=== Speaker Timeline ===\n")
        print(diarizer.format_segments(speaker_segments))
        print()

    # Transkription
    print("=== Transcription ===\n")
    
    # Bei Diarization: Segmente erzwingen für Alignment
    needs_segments = args.segments or args.diarize
    
    # Temporäre Ausgabe-Datei für Segment-Parsing
    temp_transcript = None
    if args.diarize and not args.output:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_transcript = Path(temp_file.name)
        temp_file.close()
    
    client = STTClient(binary_path, args.model)
    result = client.transcribe(
        wav_file=wav_file,
        language=args.language,
        num_threads=args.threads,
        show_segments=needs_segments,
        translate=args.translate,
        output_file=temp_transcript or args.output
    )

    # Bei Diarization: Segmente kombinieren
    if args.diarize and speaker_segments:
        print("\n=== Combined Transcript with Speakers ===\n")
        
        # Transkript aus Datei lesen
        if temp_transcript:
            with open(temp_transcript, 'r') as f:
                transcript_output = f.read()
        elif args.output:
            with open(args.output, 'r') as f:
                transcript_output = f.read()
        else:
            transcript_output = result or ""
        
        # Segmente parsen
        transcript_segments = client.parse_segments_from_output(transcript_output)
        
        if transcript_segments:
            # Sprecher mit Transkript kombinieren
            combined = SpeakerDiarizer.merge_with_transcript(
                speaker_segments, 
                transcript_segments
            )
            
            # Ausgabe formatieren
            output_lines = []
            current_speaker = None
            
            for start, end, speaker, text in combined:
                # Sprecher-Wechsel anzeigen
                if speaker != current_speaker:
                    output_lines.append(f"\n=== {speaker} ===\n")
                    current_speaker = speaker
                
                timestamp_str = f"[{format_timestamp(start)} --> {format_timestamp(end)}]"
                output_lines.append(f"{timestamp_str} {text}")
            
            combined_output = "\n".join(output_lines)
            
            # Ausgabe
            print(combined_output)
            
            # In Datei schreiben
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(combined_output + "\n")
                print(f"\nTranscript with speakers saved to: {args.output}")
        else:
            print("Warning: Could not parse transcript segments", file=sys.stderr)
        
        # Temp-Datei aufräumen
        if temp_transcript:
            temp_transcript.unlink(missing_ok=True)

    # Temporäre WAV aufräumen
    if cleanup_temp and temp_wav and temp_wav.exists():
        temp_wav.unlink(missing_ok=True)

    if result is None:
        sys.exit(3)

    # Erfolg
    sys.exit(0)


if __name__ == "__main__":
    main()
