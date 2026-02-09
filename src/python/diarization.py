"""
Speaker Diarization Module für V-SpeechFlow

Nutzt pyannote.audio 4.0+ für Speaker-Segmentierung.
Erfordert Hugging Face Token für Modell-Download.

Kompatibilität:
- pyannote.audio 4.0+ (nutzt torchcodec statt deprecated torchaudio APIs)
- Python 3.10+
- torchaudio 2.8+
"""

import sys
from pathlib import Path
from typing import List, Tuple, Optional
import warnings

import hf_token as hf_token_container

# pyannote.audio ist optional
try:
    from pyannote.audio import Pipeline
    import torch
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False


class SpeakerSegment:
    """Ein Segment mit Sprecher-Information"""
    def __init__(self, start: float, end: float, speaker: str):
        self.start = start  # Sekunden
        self.end = end      # Sekunden
        self.speaker = speaker
    
    def __repr__(self):
        return f"SpeakerSegment({self.start:.2f}s - {self.end:.2f}s, {self.speaker})"
    
    def duration(self) -> float:
        return self.end - self.start


class SpeakerDiarizer:
    """
    Speaker Diarization mit pyannote.audio - Optimiert für deutsche Sprache
    
    Features:
    - Optimierte Parameter für deutsche Konversationen
    - Multi-Speaker-Erkennung (2-10 Sprecher)
    - Robust gegen Dialekte und Akzente
    - Apple Silicon MPS-Beschleunigung
    
    Erfordert:
    - pip install pyannote.audio torch torchaudio
    - Hugging Face Token mit Zugriff auf pyannote/speaker-diarization-3.1
    """
    
    def __init__(self, hf_token: Optional[str] = None, device: str = "cpu", 
                 optimize_for_german: bool = True):
        """
        Args:
            hf_token: Hugging Face Token (oder via HF_TOKEN env var)
            device: "cpu" oder "cuda" (MPS für Mac wird automatisch erkannt)
            optimize_for_german: Nutzt optimierte Parameter für deutsche Sprache
        """
        if not DIARIZATION_AVAILABLE:
            raise ImportError(
                "pyannote.audio not installed. Install with:\n"
                "  pip install pyannote.audio torch torchaudio"
            )
        
        # Resolve token from CLI/env/Keychain (cached) if not explicitly provided
        self.hf_token = hf_token_container.get_hf_token(hf_token)
        self.pipeline = None
        self.optimize_for_german = optimize_for_german
        
        # Device-Erkennung für Apple Silicon
        if device == "cpu" and torch.backends.mps.is_available():
            self.device = "mps"
            print("Using Apple Silicon MPS acceleration for diarization")
        else:
            self.device = device
    
    def initialize(self) -> bool:
        """
        Lädt das Diarization-Modell von Hugging Face
        Optimiert für deutsche Sprache mit angepassten Hyperparametern
        
        Returns:
            True bei Erfolg
        """
        try:
            # Warnung unterdrücken für torchaudio backend
            warnings.filterwarnings("ignore", category=UserWarning)
            
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.hf_token
            )
            
            # Optimierte Parameter für deutsche Sprache
            if self.optimize_for_german:
                # Segmentierung: Kürzere Min-Dauer für schnellere deutsche Sprechwechsel
                self.pipeline._segmentation.min_duration_off = 0.3  # Standard: 0.5811
                
                # Clustering: Konservativer Threshold für bessere Sprecher-Trennung
                # Deutsche Sprecher haben oft ähnlichere Stimmcharakteristiken
                if hasattr(self.pipeline, '_embedding'):
                    # Niedrigerer Threshold = strengere Trennung
                    self.pipeline._embedding.min_cluster_size = 12  # Standard: 15
            
            # Pipeline auf Device verschieben
            if self.device != "cpu":
                try:
                    self.pipeline.to(torch.device(self.device))
                except Exception as e:
                    print(f"Warning: Could not move to {self.device}, using CPU: {e}")
                    self.device = "cpu"
            
            optimization_status = "optimiert für Deutsch" if self.optimize_for_german else "Standard"
            print(f"Diarization model loaded (device: {self.device}, {optimization_status})")
            return True
            
        except Exception as e:
            print(f"Error loading diarization model: {e}", file=sys.stderr)
            print("\nMake sure you have:", file=sys.stderr)
            print("1. Accepted the model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1", file=sys.stderr)
            print("2. Provide your HF token:", file=sys.stderr)
            print("   export HF_TOKEN='your_token'", file=sys.stderr)
            print("   # or store in Keychain service: HF_V-Speechflow", file=sys.stderr)
            print("   export HF_TOKEN=\"$(security find-generic-password -s HF_V-Speechflow -w)\"", file=sys.stderr)
            print("   # or pass it via --hf-token argument", file=sys.stderr)
            return False
    
    def diarize(self, audio_file: Path, num_speakers: Optional[int] = None,
                min_speakers: Optional[int] = None, max_speakers: Optional[int] = None) -> List[SpeakerSegment]:
        """
        Führt Speaker Diarization durch - Optimiert für deutsche Sprache
        
        Args:
            audio_file: Pfad zur Audio-Datei
            num_speakers: Exakte Anzahl Sprecher (None = auto-detect)
            min_speakers: Minimale Anzahl Sprecher (für auto-detect)
            max_speakers: Maximale Anzahl Sprecher (für auto-detect)
        
        Returns:
            Liste von SpeakerSegments
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        print(f"Analyzing speakers in: {audio_file}")
        if num_speakers:
            print(f"Expected speakers: {num_speakers}")
        elif min_speakers or max_speakers:
            range_str = f"{min_speakers or 1} bis {max_speakers or 10}"
            print(f"Auto-detecting speakers (range: {range_str})...")
        else:
            print("Auto-detecting number of speakers (optimiert für deutsche Konversationen)...")
        
        # Parameter für Diarization
        diarization_params = {}
        
        if num_speakers:
            diarization_params['num_speakers'] = num_speakers
        else:
            # Für deutsche Sprache: Typische Bereiche
            # Interview/Dialog: 2, Diskussion: 2-4, Konferenz: 3-6, Podcast: 2-5
            diarization_params['min_speakers'] = min_speakers or 1
            diarization_params['max_speakers'] = max_speakers or 10
        
        # Diarization durchführen
        diarization = self.pipeline(
            str(audio_file),
            **diarization_params
        )
        
        # Ergebnisse konvertieren - Handle alte und neue API
        segments = []
        
        # Alte API: Direktes Annotation-Objekt mit itertracks
        if hasattr(diarization, 'itertracks'):
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker
                )
                segments.append(segment)
        # Neue API: DiarizeOutput mit .speaker_diarization Attribut
        else:
            for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker
                )
                segments.append(segment)
        
        # Post-Processing für deutsche Sprache
        if self.optimize_for_german and segments:
            segments = self._post_process_german(segments)
        
        # Statistik ausgeben
        speakers = set(seg.speaker for seg in segments)
        total_duration = sum(seg.duration() for seg in segments)
        print(f"Found {len(speakers)} speaker(s): {', '.join(sorted(speakers))}")
        
        # Sprecher-Statistik
        speaker_stats = {}
        for seg in segments:
            if seg.speaker not in speaker_stats:
                speaker_stats[seg.speaker] = 0
            speaker_stats[seg.speaker] += seg.duration()
        
        print("\nSpeaker statistics:")
        for speaker in sorted(speaker_stats.keys()):
            duration = speaker_stats[speaker]
            percentage = (duration / total_duration * 100) if total_duration > 0 else 0
            print(f"  {speaker}: {duration:.1f}s ({percentage:.1f}%)")
        
        return segments
    
    def _post_process_german(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """
        Post-Processing speziell für deutsche Sprache
        
        - Filtert sehr kurze Segmente (< 0.5s) die oft Artefakte sind
        - Merged aufeinanderfolgende Segmente desselben Sprechers
        - Berücksichtigt typische deutsche Sprechpausen
        """
        if not segments:
            return segments
        
        # 1. Filtern sehr kurzer Segmente (oft false positives)
        MIN_SEGMENT_DURATION = 0.5  # Sekunden
        filtered = [seg for seg in segments if seg.duration() >= MIN_SEGMENT_DURATION]
        
        # 2. Merge aufeinanderfolgende Segmente desselben Sprechers
        # Deutsche Sprecher machen oft kurze Pausen (0.1-0.3s)
        MAX_MERGE_GAP = 0.4  # Sekunden
        
        merged = []
        current = None
        
        for seg in filtered:
            if current is None:
                current = SpeakerSegment(seg.start, seg.end, seg.speaker)
            elif seg.speaker == current.speaker and (seg.start - current.end) <= MAX_MERGE_GAP:
                # Merge: Erweitere aktuelles Segment
                current.end = seg.end
            else:
                # Neuer Sprecher oder zu große Lücke
                merged.append(current)
                current = SpeakerSegment(seg.start, seg.end, seg.speaker)
        
        if current:
            merged.append(current)
        
        return merged
    
    @staticmethod
    def format_segments(segments: List[SpeakerSegment], indent: str = "") -> str:
        """
        Formatiert Segmente für Text-Ausgabe
        
        Args:
            segments: Liste von SpeakerSegments
            indent: Einrückung
        
        Returns:
            Formatierter String
        """
        lines = []
        for seg in segments:
            lines.append(
                f"{indent}[{seg.start:7.2f}s - {seg.end:7.2f}s] {seg.speaker}"
            )
        return "\n".join(lines)
    
    @staticmethod
    def merge_with_transcript(
        speaker_segments: List[SpeakerSegment],
        transcript_segments: List[Tuple[float, float, str]]
    ) -> List[Tuple[float, float, str, str]]:
        """
        Kombiniert Sprecher-Segmente mit Transkript-Segmenten
        
        Args:
            speaker_segments: Liste von SpeakerSegments
            transcript_segments: Liste von (start, end, text) Tupeln
        
        Returns:
            Liste von (start, end, speaker, text) Tupeln
        """
        result = []
        
        for t_start, t_end, text in transcript_segments:
            # Finde überlappende Sprecher-Segmente
            t_mid = (t_start + t_end) / 2  # Mittelpunkt des Transkripts
            
            # Finde Sprecher zur Mitte des Segments
            speaker = "UNKNOWN"
            for seg in speaker_segments:
                if seg.start <= t_mid <= seg.end:
                    speaker = seg.speaker
                    break
            
            result.append((t_start, t_end, speaker, text))
        
        return result


def check_diarization_available() -> bool:
    """Prüft ob Diarization verfügbar ist"""
    return DIARIZATION_AVAILABLE


def print_diarization_help():
    """Gibt Hilfe-Text für Diarization-Setup aus"""
    print("\n=== Speaker Diarization Setup ===\n")
    print("1. Install dependencies:")
    print("   pip install pyannote.audio torch torchaudio")
    print()
    print("2. Accept model terms:")
    print("   https://huggingface.co/pyannote/speaker-diarization-3.1")
    print("   https://huggingface.co/pyannote/segmentation-3.0")
    print()
    print("3. Get Hugging Face token:")
    print("   https://huggingface.co/settings/tokens")
    print()
    print("4. Set token:")
    print("   export HF_TOKEN='your_token_here'")
    print("   # recommended (macOS Keychain service: HF_V-Speechflow):")
    print("   export HF_TOKEN=\"$(security find-generic-password -s HF_V-Speechflow -w)\"")
    print("   # or pass via --hf-token argument")
    print()
