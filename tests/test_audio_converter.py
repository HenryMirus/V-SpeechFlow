import sys
import unittest
from pathlib import Path
import io
import contextlib
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
PY_SRC = REPO_ROOT / "src" / "python"
sys.path.insert(0, str(PY_SRC))

import stt_cli  # noqa: E402


class TestAudioConverter(unittest.TestCase):
    def test_convert_to_wav_builds_expected_ffmpeg_command(self) -> None:
        input_file = Path("/tmp/in.mp3")
        output_file = Path("/tmp/out.wav")

        with mock.patch("stt_cli.subprocess.run") as run:
            run.return_value = mock.Mock(stdout=b"", stderr=b"")
            ok = stt_cli.AudioConverter.convert_to_wav(input_file, output_file)

        self.assertTrue(ok)
        args, kwargs = run.call_args
        cmd = args[0]

        # Ensure core flags are present and ordered as expected
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("-i", cmd)
        self.assertIn(str(input_file), cmd)
        self.assertIn("-ar", cmd)
        self.assertIn("16000", cmd)
        self.assertIn("-ac", cmd)
        self.assertIn("1", cmd)
        self.assertIn("-sample_fmt", cmd)
        self.assertIn("s16", cmd)
        self.assertIn("-y", cmd)
        self.assertEqual(cmd[-1], str(output_file))

        self.assertTrue(kwargs.get("check"))

    def test_convert_to_wav_returns_false_on_failure(self) -> None:
        input_file = Path("/tmp/in.mp3")
        output_file = Path("/tmp/out.wav")

        with (
            mock.patch("stt_cli.subprocess.run", side_effect=stt_cli.subprocess.CalledProcessError(1, "ffmpeg", stderr=b"boom")),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            ok = stt_cli.AudioConverter.convert_to_wav(input_file, output_file)

        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
