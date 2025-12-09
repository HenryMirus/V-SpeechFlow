#!/usr/bin/env python3
"""
Live Microphone Recording für V-SpeechFlow

Ermöglicht Echtzeit-Aufnahme vom macOS Mikrofonarray.
Optimiert für Kompatibilität mit whisper.cpp (16kHz, mono, 16-bit PCM).
"""

import sys
import wave
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class LiveRecorder:
    """
    Nimmt Audio vom macOS Mikrofon in Echtzeit auf.
    
    Technische Spezifikation:
    - Sample Rate: 16kHz (whisper.cpp Standard)
    - Channels: Mono (gemischt wenn Multi-Channel-Gerät)
    - Format: 16-bit PCM
    - Chunk Size: 1024 Frames (~64ms bei 16kHz)
    """
    
    # Audio-Format-Konstanten
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
    
    def __init__(self):
        """Initialisiert PyAudio-Interface."""
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio nicht verfügbar. Installieren mit:\n"
                "  brew install portaudio\n"
                "  pip install pyaudio"
            )
        
        self.audio: pyaudio.PyAudio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.frames: list = []
        self.is_recording: bool = False
        self.input_channels: int = self.CHANNELS  # Tatsächlich verwendete Kanäle
    
    def list_devices(self) -> None:
        """Zeigt alle verfügbaren Audio-Eingabegeräte an."""
        print("\n=== Verfügbare Audio-Eingabegeräte ===\n")
        
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            
            # Nur Eingabegeräte anzeigen
            if device_info.get('maxInputChannels') > 0:
                print(f"[{i}] {device_info.get('name')}")
                print(f"    Kanäle: {device_info.get('maxInputChannels')}")
                print(f"    Sample Rate: {int(device_info.get('defaultSampleRate'))} Hz")
                print()
    
    def get_default_device(self) -> int:
        """
        Ermittelt das Standard-Eingabegerät von macOS.
        
        Returns:
            Device-Index des Standard-Mikrofons
        """
        default_device = self.audio.get_default_input_device_info()
        device_index = default_device['index']
        
        print(f"Verwende Standard-Gerät: {default_device['name']}")
        print(f"  Kanäle: {default_device['maxInputChannels']}")
        print(f"  Sample Rate: {int(default_device['defaultSampleRate'])} Hz")
        
        return device_index
    
    def start_recording(self, device_index: Optional[int] = None) -> None:
        """
        Startet Audio-Aufnahme vom Mikrofon.
        
        Args:
            device_index: Geräte-Index (None = Standard-Gerät verwenden)
        
        Raises:
            RuntimeError: Wenn bereits aufgenommen wird
            OSError: Bei Mikrofonzugriffs-Problemen (z.B. Permissions)
        """
        if self.is_recording:
            raise RuntimeError("Aufnahme läuft bereits!")
        
        if device_index is None:
            device_index = self.get_default_device()
        
        # Geräte-Info abrufen für Kanal-Kompatibilität
        device_info = self.audio.get_device_info_by_index(device_index)
        max_input_channels = int(device_info.get('maxInputChannels', 1))
        
        # Verwende min(1, max_channels) für Mono-Aufnahme
        # Wenn Gerät nur Stereo unterstützt, nehmen wir 2 Kanäle und mischen später
        channels = min(max_input_channels, self.CHANNELS) if max_input_channels > 0 else self.CHANNELS
        if channels != self.CHANNELS and max_input_channels >= 2:
            channels = 2  # Stereo aufnehmen, später zu Mono mischen
        
        try:
            # Audio-Stream öffnen
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=channels,
                rate=self.SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.CHUNK_SIZE,
                stream_callback=None  # Blocking Mode
            )
            self.input_channels = channels  # Merken für spätere Verarbeitung
        except OSError as e:
            raise OSError(
                "Mikrofonzugriff fehlgeschlagen. Mögliche Ursachen:\n"
                "  - Mikrofonberechtigung verweigert (Systemeinstellungen → Datenschutz & Sicherheit → Mikrofon)\n"
                "  - Gerät nicht verfügbar oder bereits verwendet\n"
                f"  - Technischer Fehler: {e}"
            ) from e
        
        self.frames = []
        self.is_recording = True
        
        print(f"\n🎙️  Aufnahme gestartet (16kHz, mono)")
        print("Drücke Ctrl+C zum Stoppen\n")
    
    def record_chunk(self) -> bytes:
        """
        Nimmt einen Audio-Chunk auf (blocking).
        
        Returns:
            Audio-Daten als Bytes (16-bit PCM)
        
        Raises:
            RuntimeError: Wenn Aufnahme nicht gestartet wurde
        """
        if not self.is_recording or not self.stream:
            raise RuntimeError("Aufnahme nicht gestartet. Rufe start_recording() auf.")
        
        # Einen Chunk lesen (blockiert bis Daten verfügbar)
        data = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
        self.frames.append(data)
        
        # Volume-Indikator berechnen und anzeigen
        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_data).mean()
        
        # Skalierung für Terminal-Anzeige (max. 50 Zeichen)
        bar_length = int(volume / 500)  # Experimenteller Skalierungsfaktor
        bar = '█' * min(bar_length, 50)
        
        # Überschreibe vorherige Zeile
        print(f"\r🔊 {bar:<50}", end='', flush=True)
        
        return data
    
    def stop_recording(self) -> None:
        """Stoppt die Aufnahme und schließt den Stream."""
        if not self.is_recording:
            return
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.is_recording = False
        print("\n\n✅ Aufnahme gestoppt")
    
    def save_wav(self, output_path: Path) -> None:
        """
        Speichert aufgenommenes Audio als WAV-Datei.
        
        Args:
            output_path: Pfad zur Ausgabe-WAV-Datei
        
        Raises:
            ValueError: Wenn keine Audio-Daten vorhanden sind
        """
        if not self.frames:
            raise ValueError("Keine Audio-Daten zum Speichern vorhanden!")
        
        # Wenn Stereo aufgenommen wurde, zu Mono konvertieren
        if self.input_channels == 2:
            # Stereo → Mono: beide Kanäle mitteln
            mono_frames = []
            for frame in self.frames:
                audio_data = np.frombuffer(frame, dtype=np.int16)
                # Reshapen zu (samples, 2) und mitteln
                stereo = audio_data.reshape(-1, 2)
                mono = stereo.mean(axis=1).astype(np.int16)
                mono_frames.append(mono.tobytes())
            frames_to_save = mono_frames
        else:
            frames_to_save = self.frames
        
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)  # Immer Mono speichern
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(b''.join(frames_to_save))
        
        # Dauer berechnen
        total_frames = len(self.frames) * self.CHUNK_SIZE
        duration = total_frames / self.SAMPLE_RATE
        
        print(f"💾 Gespeichert: {output_path.name} ({duration:.1f}s)")
    
    def get_duration(self) -> float:
        """
        Berechnet die Dauer der bisherigen Aufnahme.
        
        Returns:
            Dauer in Sekunden
        """
        if not self.frames:
            return 0.0
        
        total_frames = len(self.frames) * self.CHUNK_SIZE
        return total_frames / self.SAMPLE_RATE
    
    def cleanup(self) -> None:
        """Gibt PyAudio-Ressourcen frei."""
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        
        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass


def main():
    """Test-Funktion für Live-Recording."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="V-SpeechFlow Live Recorder - Test-Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Verfügbare Mikrofone auflisten
  %(prog)s --list-devices
  
  # Aufnahme mit Standard-Mikrofon
  %(prog)s -o test.wav
  
  # Aufnahme mit spezifischem Gerät
  %(prog)s -o test.wav --device 1
        """
    )
    
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='Verfügbare Audio-Eingabegeräte auflisten und beenden'
    )
    
    parser.add_argument(
        '--device',
        type=int,
        help='Geräte-Index (Standard: System-Default-Mikrofon)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('test_recording.wav'),
        help='Ausgabe-WAV-Datei (Standard: test_recording.wav)'
    )
    
    args = parser.parse_args()
    
    # Prüfe ob PyAudio verfügbar ist
    if not PYAUDIO_AVAILABLE:
        print("Fehler: PyAudio nicht installiert.", file=sys.stderr)
        print("\nInstallation:", file=sys.stderr)
        print("  brew install portaudio", file=sys.stderr)
        print("  pip install pyaudio", file=sys.stderr)
        return 1
    
    recorder = LiveRecorder()
    
    try:
        # Nur Geräte auflisten
        if args.list_devices:
            recorder.list_devices()
            return 0
        
        # Aufnahme starten
        print("=== V-SpeechFlow Live Recorder ===\n")
        recorder.start_recording(device_index=args.device)
        
        # Aufnehmen bis Ctrl+C
        try:
            while True:
                recorder.record_chunk()
        except KeyboardInterrupt:
            print("\n\nStoppe Aufnahme...")
        
        # Aufnahme beenden und speichern
        recorder.stop_recording()
        recorder.save_wav(args.output)
        
        print(f"\n✅ Erfolgreich! Teste mit:")
        print(f"   ffplay {args.output}")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Fehler: {e}", file=sys.stderr)
        return 1
    
    finally:
        recorder.cleanup()


if __name__ == '__main__':
    sys.exit(main())
