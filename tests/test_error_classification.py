"""
Tests für die Fehler-Klassifikation bei der Transkription.

Testet classify_stderr_error(), is_whisper_debug_line() und is_stderr_error_line()
aus src/gui/utils.py.
"""

import sys
from pathlib import Path
import pytest

# Projektverzeichnis zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gui.utils import (classify_stderr_error, classify_process_error,
                      classify_process_warning, is_whisper_debug_line,
                      is_stderr_error_line)


class TestClassifyStderrError:
    """Tests für classify_stderr_error()."""

    def test_returns_none_for_empty_list(self):
        assert classify_stderr_error([]) is None

    def test_returns_none_for_no_errors(self):
        lines = [
            "whisper_init_from_file_with_params: loading model",
            "ggml_metal_init: found device: Apple M1",
            "Model loaded successfully: models/ggml-large.bin",
        ]
        assert classify_stderr_error(lines) is None

    # === WAV-Fehler ===

    def test_detects_cannot_open_wav(self):
        lines = [
            "ggml_metal_init: found device: Apple M1",
            "Error: Cannot open WAV file: /tmp/missing.wav",
        ]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Cannot open WAV file" in result

    def test_detects_invalid_wav(self):
        lines = ["Error: Not a valid WAV file (missing RIFF/WAVE)"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Not a valid WAV file" in result

    def test_detects_pcm_only(self):
        lines = ["Error: Only PCM format supported (audio_format=3)"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "PCM format" in result

    def test_detects_16bit_only(self):
        lines = ["Error: Only 16-bit samples supported (bits_per_sample=24)"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "16-bit" in result

    def test_detects_read_audio_failed(self):
        lines = ["Error: Failed to read audio data"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Failed to read audio data" in result

    # === Model-Fehler ===

    def test_detects_model_load_failed(self):
        lines = ["Error: Failed to load model from /models/broken.bin"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Failed to load model" in result

    def test_detects_invalid_model(self):
        lines = ["whisper_model_load: invalid model data (bad magic)"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "invalid model data" in result

    def test_detects_engine_not_initialized(self):
        lines = ["Error: Engine not initialized"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Engine not initialized" in result

    # === Transkriptions-Fehler (whisper.cpp) ===

    def test_detects_transcription_failed_code(self):
        lines = [
            "Processing 480000 samples...",
            "Error: Transcription failed with code -6",
        ]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Transcription failed with code" in result

    def test_detects_failed_to_encode(self):
        lines = ["whisper_full_with_state: failed to encode"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "failed to encode" in result

    def test_detects_failed_to_decode(self):
        lines = ["whisper_full_with_state: failed to decode"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "failed to decode" in result

    def test_detects_mel_spectrogram_failed(self):
        lines = ["whisper_full: failed to compute log mel spectrogram"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "log mel spectrogram" in result

    def test_detects_language_detection_failed(self):
        lines = ["whisper_full: failed to auto-detect language"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "auto-detect language" in result

    def test_detects_vad_failed(self):
        lines = ["whisper_full: failed to compute VAD"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "VAD" in result

    # === CLI-Fehler ===

    def test_detects_ffmpeg_failed(self):
        lines = ["Error: ffmpeg conversion failed: some detail"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "ffmpeg conversion failed" in result

    def test_detects_binary_not_found(self):
        lines = ["Error: STT binary not found at /path/to/stt_native"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "binary not found" in result.lower()

    def test_detects_model_not_found(self):
        lines = ["Error: Model file not found at /models/ggml-large.bin"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Model file not found" in result

    def test_detects_audio_not_found(self):
        lines = ["Error: Audio file not found: /tmp/test.wav"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Audio file not found" in result

    # === Diarization-Fehler ===

    def test_no_speakers_is_not_an_error(self):
        """'No speakers detected' ist jetzt ein Warning, kein Error."""
        lines = ["Warning: No speakers detected by diarization. No output file written."]
        result = classify_stderr_error(lines)
        assert result is None

    def test_detects_diarization_unavailable(self):
        lines = ["Error: Diarization module not available"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "Diarization" in result

    def test_detects_hf_token_required(self):
        lines = ["Error: HF token required for diarization"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "HF token required" in result

    # === Speicher-Fehler ===

    def test_detects_out_of_memory(self):
        lines = ["ggml: failed to allocate memory for tensor"]
        result = classify_stderr_error(lines)
        assert result is not None
        assert "failed to allocate memory" in result

    # === Priorität: Erster Fehler wird zurückgegeben ===

    def test_returns_first_error(self):
        lines = [
            "Error: Cannot open WAV file: /tmp/test.wav",
            "Error: Transcription failed with code -1",
        ]
        result = classify_stderr_error(lines)
        assert "Cannot open WAV file" in result

    # === Gemischte Ausgabe mit Debug-Zeilen ===

    def test_skips_debug_finds_error(self):
        lines = [
            "whisper_init_from_file_with_params: loading model",
            "ggml_metal_init: found device: Apple M1",
            "whisper_init_from_file_with_params: model loaded",
            "Error: Transcription failed with code -6",
        ]
        result = classify_stderr_error(lines)
        assert "Transcription failed with code -6" in result


class TestIsWhisperDebugLine:
    """Tests für is_whisper_debug_line()."""

    def test_normal_debug_line(self):
        assert is_whisper_debug_line("whisper_init_from_file: loading model") is True

    def test_ggml_debug_line(self):
        assert is_whisper_debug_line("ggml_metal_init: found device: Apple M1") is True

    def test_metal_debug_line(self):
        assert is_whisper_debug_line("metal_init: using GPU") is True

    def test_backend_debug_line(self):
        assert is_whisper_debug_line("backend_init: initializing") is True

    def test_not_debug_line(self):
        assert is_whisper_debug_line("Processing 480000 samples...") is False

    def test_error_line_not_debug(self):
        assert is_whisper_debug_line("Error: Something went wrong") is False

    # === Debug-Prefix mit Error-Keyword → KEIN Debug ===

    def test_whisper_failed_to_encode_is_not_debug(self):
        assert is_whisper_debug_line("whisper_full_with_state: failed to encode") is False

    def test_whisper_failed_to_decode_is_not_debug(self):
        assert is_whisper_debug_line("whisper_full_with_state: failed to decode") is False

    def test_whisper_invalid_model_is_not_debug(self):
        assert is_whisper_debug_line("whisper_model_load: invalid model data (bad magic)") is False

    def test_ggml_failed_allocate_is_not_debug(self):
        assert is_whisper_debug_line("ggml_backend: failed to allocate memory") is False

    def test_model_not_found_is_not_debug(self):
        assert is_whisper_debug_line("model_load: error loading file") is False

    def test_encoder_error_is_not_debug(self):
        assert is_whisper_debug_line("encoder_begin: cannot process") is False


class TestIsStderrErrorLine:
    """Tests für is_stderr_error_line()."""

    def test_error_colon(self):
        assert is_stderr_error_line("Error: Something bad happened") is True

    def test_failed_colon(self):
        assert is_stderr_error_line("Failed: to do something") is True

    def test_exception(self):
        assert is_stderr_error_line("Exception: ValueError") is True

    def test_traceback(self):
        assert is_stderr_error_line("Traceback (most recent call last):") is True

    def test_cannot(self):
        assert is_stderr_error_line("cannot open file") is True

    def test_unable_to(self):
        assert is_stderr_error_line("unable to initialize") is True

    def test_failed_to(self):
        assert is_stderr_error_line("failed to process audio") is True

    def test_not_found(self):
        assert is_stderr_error_line("file not found: /tmp/x.wav") is True

    def test_invalid(self):
        assert is_stderr_error_line("invalid model data") is True

    def test_not_a_valid(self):
        assert is_stderr_error_line("not a valid WAV file") is True

    def test_normal_output_not_error(self):
        assert is_stderr_error_line("Processing 480000 samples...") is False

    def test_model_loaded_not_error(self):
        assert is_stderr_error_line("Model loaded successfully") is False

    def test_empty_line_not_error(self):
        assert is_stderr_error_line("") is False


class TestClassifyProcessError:
    """Tests für classify_process_error() — kombinierte stderr + stdout Analyse."""

    def test_returns_none_for_empty(self):
        assert classify_process_error([], []) is None

    def test_stderr_has_priority(self):
        stderr = ["Error: Failed to load model from /models/broken.bin"]
        stdout = ["Found 0 speaker(s):"]
        result = classify_process_error(stderr, stdout)
        assert "Failed to load model" in result

    def test_finds_error_in_stdout(self):
        stderr = [
            "whisper_init_from_file_with_params: loading model",
            "ggml_metal_init: found device: Apple M1",
        ]
        stdout = [
            "V-SpeechFlow CLI",
            "Using binary: /path/to/stt_native",
            "Found 0 speaker(s):",
            "Speaker statistics:",
        ]
        result = classify_process_error(stderr, stdout)
        assert result is not None
        assert "Found 0 speaker(s)" in result

    def test_no_stdout_patterns_in_normal_output(self):
        stderr = []
        stdout = [
            "V-SpeechFlow CLI",
            "Found 3 speaker(s): SPEAKER_00, SPEAKER_01, SPEAKER_02",
            "Processing complete",
        ]
        result = classify_process_error(stderr, stdout)
        assert result is None

    def test_works_without_stdout(self):
        stderr = ["Error: Cannot open WAV file: /tmp/test.wav"]
        result = classify_process_error(stderr)
        assert result is not None
        assert "Cannot open WAV file" in result

    def test_returns_none_for_debug_only(self):
        stderr = [
            "whisper_init_from_file_with_params: loading model",
            "ggml_metal_init: found device: Apple M1",
        ]
        stdout = [
            "V-SpeechFlow CLI",
            "Model loaded successfully",
        ]
        result = classify_process_error(stderr, stdout)
        assert result is None


class TestClassifyProcessWarning:
    """Tests für classify_process_warning() — erkennt Warnungen in stderr/stdout."""

    def test_returns_none_for_empty(self):
        assert classify_process_warning([], []) is None

    def test_detects_no_speakers_in_stderr(self):
        stderr = ["Warning: No speakers detected by diarization. No output file written."]
        result = classify_process_warning(stderr)
        assert result is not None
        assert "No speakers detected" in result

    def test_detects_no_speakers_in_stdout(self):
        stdout = [
            "V-SpeechFlow CLI",
            "Found 0 speaker(s):",
            "Speaker statistics:",
        ]
        result = classify_process_warning([], stdout)
        assert result is not None
        assert "Found 0 speaker(s)" in result

    def test_detects_sample_rate_warning(self):
        stderr = ["Warning: Sample rate is 44100Hz, recommended is 16000Hz"]
        result = classify_process_warning(stderr)
        assert result is not None
        assert "Sample rate" in result

    def test_detects_channel_warning(self):
        stderr = ["Warning: Audio has 2 channel(s), mono recommended"]
        result = classify_process_warning(stderr)
        assert result is not None
        assert "Audio has" in result

    def test_no_warning_for_normal_output(self):
        stderr = [
            "whisper_init_from_file_with_params: loading model",
            "ggml_metal_init: found device: Apple M1",
        ]
        stdout = [
            "Found 3 speaker(s): SPEAKER_00, SPEAKER_01, SPEAKER_02",
            "Processing complete",
        ]
        result = classify_process_warning(stderr, stdout)
        assert result is None

    def test_does_not_confuse_found_speakers_with_warning(self):
        stdout = ["Found 2 speaker(s): SPEAKER_00, SPEAKER_01"]
        result = classify_process_warning([], stdout)
        assert result is None

    def test_detects_segment_parse_warning(self):
        stderr = ["Warning: Could not parse transcript segments"]
        result = classify_process_warning(stderr)
        assert result is not None
        assert "parse transcript segments" in result
