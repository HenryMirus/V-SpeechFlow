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


class _DummyRecorder:
    def list_devices(self) -> None:
        return

    def cleanup(self) -> None:
        return


class TestCliArgs(unittest.TestCase):
    def test_argparse_rejects_both_live_and_input(self) -> None:
        argv = [
            "prog",
            "--live",
            "-i",
            "x.mp3",
            "-m",
            "models/ggml-medium.bin",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as cm:
                stt_cli.main()
        self.assertEqual(cm.exception.code, 2)  # argparse usage error

    def test_list_devices_does_not_require_model_or_input(self) -> None:
        argv = ["prog", "--list-devices"]
        # On CI, PyAudio is typically not installed, so stt_cli may not define LiveRecorder.
        # In that case, the correct behavior is to exit with code 1 and a helpful message.
        if hasattr(stt_cli, "LiveRecorder"):
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(stt_cli, "LIVE_RECORDING_AVAILABLE", True),
                mock.patch.object(stt_cli, "LiveRecorder", _DummyRecorder),
            ):
                with self.assertRaises(SystemExit) as cm:
                    stt_cli.main()
            self.assertEqual(cm.exception.code, 0)
        else:
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(stt_cli, "LIVE_RECORDING_AVAILABLE", False),
            ):
                with self.assertRaises(SystemExit) as cm:
                    stt_cli.main()
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
