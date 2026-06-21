"""Checks that a merged transcript reads in chronological order."""

from pathlib import Path

from src import transcribe

FIXTURES = Path(__file__).parent / "fixtures"


def test_merged_transcript_is_chronological():
    entries = transcribe.merge_transcript(
        transcribe.load_channel_csv(FIXTURES / "demo_agent.csv", "Agent"),
        transcribe.load_channel_csv(FIXTURES / "demo_patient.csv", "Patient"),
    )
    starts = [float(entry["start"]) for entry in entries]
    assert starts == sorted(starts), (
        "Merged transcript turns are not in chronological order:\n\n"
        + transcribe.render_transcript(entries)
    )
