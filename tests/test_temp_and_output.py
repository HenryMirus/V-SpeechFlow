import sys
import tempfile
import unittest
from pathlib import Path
import io
import contextlib
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
PY_SRC = REPO_ROOT / "src" / "python"
sys.path.insert(0, str(PY_SRC))

import stt_cli  # noqa: E402


class _FakeNamedTemporaryFile:
    def __init__(self, name: Path):
        self.name = str(name)

    def close(self) -> None:
        return


def _stub_transcribe_factory(write_text: str):
    def _stub_transcribe(self, wav_file, language="de", num_threads=4, show_segments=False, translate=False, output_file=None):
        if output_file is not None:
            Path(output_file).write_text(write_text, encoding="utf-8")
            return ""
        return write_text

    return _stub_transcribe


class _FakeDiarizer:
    def __init__(self, hf_token=None, optimize_for_german=True):
        self.hf_token = hf_token

    def initialize(self) -> bool:
        return True

    def diarize(self, audio_file, num_speakers=None, min_speakers=None, max_speakers=None):
        return [stt_cli.SpeakerDiarizer.SpeakerSegment(0.0, 10.0, "SPEAKER_00")]  # type: ignore[attr-defined]

    @staticmethod
    def format_segments(segments, indent: str = ""):
        return ""

    @staticmethod
    def merge_with_transcript(speaker_segments, transcript_segments):
        # Simplest: tag everything as SPEAKER_00
        merged = []
        for start, end, text in transcript_segments:
            merged.append((start, end, "SPEAKER_00", text))
        return merged


class TestTempAndOutput(unittest.TestCase):
    def test_file_conversion_temp_deleted_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            input_mp3 = tmp / "in.mp3"
            input_mp3.write_bytes(b"fake")
            model = tmp / "model.bin"
            model.write_bytes(b"x")
            binary = tmp / "stt_native"
            binary.write_bytes(b"x")

            temp_wav_path = tmp / "temp.wav"

            def fake_named_tempfile(*args, **kwargs):
                # Called for WAV temp
                temp_wav_path.write_bytes(b"")
                return _FakeNamedTemporaryFile(temp_wav_path)

            def fake_convert_to_wav(src: Path, dst: Path) -> bool:
                dst.write_bytes(b"wav")
                return True

            argv = [
                "prog",
                "-i",
                str(input_mp3),
                "-m",
                str(model),
                "--binary",
                str(binary),
            ]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(stt_cli.AudioConverter, "is_ffmpeg_available", return_value=True),
                mock.patch.object(stt_cli.AudioConverter, "convert_to_wav", side_effect=fake_convert_to_wav),
                mock.patch.object(stt_cli.tempfile, "NamedTemporaryFile", side_effect=fake_named_tempfile),
                mock.patch.object(stt_cli.STTClient, "transcribe", new=_stub_transcribe_factory("TRANSCRIPT")),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as cm:
                    stt_cli.main()
            self.assertEqual(cm.exception.code, 0)
            self.assertFalse(temp_wav_path.exists())

    def test_keep_temp_keeps_converted_wav(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            input_mp3 = tmp / "in.mp3"
            input_mp3.write_bytes(b"fake")
            model = tmp / "model.bin"
            model.write_bytes(b"x")
            binary = tmp / "stt_native"
            binary.write_bytes(b"x")

            expected_temp = input_mp3.with_suffix(".temp.wav")

            def fake_convert_to_wav(src: Path, dst: Path) -> bool:
                dst.write_bytes(b"wav")
                return True

            argv = [
                "prog",
                "-i",
                str(input_mp3),
                "-m",
                str(model),
                "--binary",
                str(binary),
                "--keep-temp",
            ]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(stt_cli.AudioConverter, "is_ffmpeg_available", return_value=True),
                mock.patch.object(stt_cli.AudioConverter, "convert_to_wav", side_effect=fake_convert_to_wav),
                mock.patch.object(stt_cli.STTClient, "transcribe", new=_stub_transcribe_factory("TRANSCRIPT")),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as cm:
                    stt_cli.main()
            self.assertEqual(cm.exception.code, 0)
            self.assertTrue(expected_temp.exists())

    def test_output_file_written(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            input_wav = tmp / "in.wav"
            input_wav.write_bytes(b"wav")
            model = tmp / "model.bin"
            model.write_bytes(b"x")
            binary = tmp / "stt_native"
            binary.write_bytes(b"x")
            out = tmp / "out.txt"

            argv = [
                "prog",
                "-i",
                str(input_wav),
                "-m",
                str(model),
                "--binary",
                str(binary),
                "-o",
                str(out),
            ]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(stt_cli.AudioConverter, "is_ffmpeg_available", return_value=True),
                mock.patch.object(stt_cli.STTClient, "transcribe", new=_stub_transcribe_factory("TRANSCRIPT")),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as cm:
                    stt_cli.main()

            self.assertEqual(cm.exception.code, 0)
            self.assertTrue(out.exists())
            self.assertIn("TRANSCRIPT", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
