import sys
import unittest
from pathlib import Path


# Allow importing from src/python without packaging
REPO_ROOT = Path(__file__).resolve().parents[1]
PY_SRC = REPO_ROOT / "src" / "python"
sys.path.insert(0, str(PY_SRC))

import stt_cli  # noqa: E402


class TestSTTCliParsing(unittest.TestCase):
    def test_format_timestamp_rounding_and_padding(self) -> None:
        self.assertEqual(stt_cli.format_timestamp(0.0), "00:00:00.000")
        self.assertEqual(stt_cli.format_timestamp(1.234), "00:00:01.234")
        self.assertEqual(stt_cli.format_timestamp(61.005), "00:01:01.005")
        self.assertEqual(stt_cli.format_timestamp(3661.999), "01:01:01.999")

    def test_parse_segments_from_output_basic(self) -> None:
        client = stt_cli.STTClient(binary_path=Path("/bin/echo"), model_path=Path("/tmp/model.bin"))
        output = """[00:00:01.000 --> 00:00:02.500] Hallo\n[00:00:02.500 --> 00:00:03.000] Welt\n"""
        segments = client.parse_segments_from_output(output)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0][0], 1.0)
        self.assertAlmostEqual(segments[0][1], 2.5)
        self.assertEqual(segments[0][2], "Hallo")

    def test_parse_segments_ignores_nonmatching_lines(self) -> None:
        client = stt_cli.STTClient(binary_path=Path("/bin/echo"), model_path=Path("/tmp/model.bin"))
        output = """noise line\n[00:00:00.000 --> 00:00:00.100] hi\n[bad timestamp] nope\n"""
        segments = client.parse_segments_from_output(output)
        self.assertEqual(segments, [(0.0, 0.1, "hi")])

    def test_parse_segments_trims_text(self) -> None:
        client = stt_cli.STTClient(binary_path=Path("/bin/echo"), model_path=Path("/tmp/model.bin"))
        output = "[00:00:00.000 --> 00:00:00.100]   hi there   \n"
        segments = client.parse_segments_from_output(output)
        self.assertEqual(segments[0][2], "hi there")


if __name__ == "__main__":
    unittest.main()
