import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PY_SRC = REPO_ROOT / "src" / "python"
sys.path.insert(0, str(PY_SRC))

import diarization  # noqa: E402


class TestDiarizationLogic(unittest.TestCase):
    def test_merge_with_transcript_empty_inputs(self) -> None:
        self.assertEqual(diarization.SpeakerDiarizer.merge_with_transcript([], []), [])

    def test_merge_with_transcript_midpoint_matching(self) -> None:
        speaker_segments = [
            diarization.SpeakerSegment(0.0, 2.0, "SPEAKER_00"),
            diarization.SpeakerSegment(2.0, 5.0, "SPEAKER_01"),
        ]
        transcript_segments = [
            (0.0, 1.0, "a"),   # midpoint 0.5 -> SPEAKER_00
            (1.9, 2.1, "b"),   # midpoint 2.0 -> first segment that contains 2.0 (SPEAKER_00)
            (3.0, 4.0, "c"),   # midpoint 3.5 -> SPEAKER_01
            (6.0, 7.0, "d"),   # no overlap -> UNKNOWN
        ]

        combined = diarization.SpeakerDiarizer.merge_with_transcript(speaker_segments, transcript_segments)
        self.assertEqual(combined[0][2], "SPEAKER_00")
        self.assertEqual(combined[1][2], "SPEAKER_00")
        self.assertEqual(combined[2][2], "SPEAKER_01")
        self.assertEqual(combined[3][2], "UNKNOWN")

    def test_post_process_german_filters_and_merges(self) -> None:
        # We don't need pyannote for this: call method on a dummy instance
        dummy = object.__new__(diarization.SpeakerDiarizer)
        dummy.optimize_for_german = True

        segments = [
            diarization.SpeakerSegment(0.0, 0.2, "S0"),   # too short -> removed
            diarization.SpeakerSegment(0.2, 1.0, "S0"),   # kept
            diarization.SpeakerSegment(1.1, 2.0, "S0"),   # gap 0.1 -> merged
            diarization.SpeakerSegment(2.6, 3.2, "S0"),   # gap 0.6 -> not merged
        ]

        processed = diarization.SpeakerDiarizer._post_process_german(dummy, segments)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0].speaker, "S0")
        self.assertAlmostEqual(processed[0].start, 0.2)
        self.assertAlmostEqual(processed[0].end, 2.0)


if __name__ == "__main__":
    unittest.main()
