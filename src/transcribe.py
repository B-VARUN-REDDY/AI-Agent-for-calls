"""Turn a recorded call into a speaker-labeled, timestamped transcript.

Pipeline:
  1. download the dual-channel recording from Twilio (channel 0 = agent,
     channel 1 = patient)
  2. transcribe each channel with Deepgram into (start, text) segments
  3. persist each channel to a small CSV so we never re-pay for STT
  4. merge the two channels back into one chronological transcript

The merge is what produces the final "[M:SS] Speaker: text" file the bug
report cites (e.g. "transcript-03.txt at 1:14").
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = ROOT / "recordings"
TRANSCRIPTS_DIR = ROOT / "transcripts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def _format_timecode(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes}:{secs:02d}"


def write_channel_csv(path: Path, segments: list[dict]) -> None:
    """Persist one channel's (start, text) segments to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["start", "text"])
        writer.writeheader()
        for seg in segments:
            writer.writerow({"start": seg["start"], "text": seg["text"]})


def load_channel_csv(path: Path, speaker: str) -> list[dict]:
    """Load one channel's segments, tagging each with its speaker."""
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({"start": row["start"], "speaker": speaker, "text": row["text"]})
    return rows


def merge_transcript(agent_rows: list[dict], patient_rows: list[dict]) -> list[dict]:
    """Interleave both speakers into one chronological list of turns."""
    combined = agent_rows + patient_rows
    combined.sort(key=lambda row: float(row["start"]))
    return combined


def render_transcript(entries: list[dict]) -> str:
    lines = []
    for entry in entries:
        timecode = _format_timecode(float(entry["start"]))
        lines.append(f"[{timecode}] {entry['speaker']}: {entry['text']}")
    return "\n".join(lines)


def download_recording(call_sid: str, index: int, retries: int = 8) -> "Path | None":
    """Download a call's Twilio recording as mp3 (recordings become ready a few
    seconds after the call ends, so we poll briefly)."""
    import time

    import requests  # lazy import
    from twilio.rest import Client  # lazy import

    from . import config

    client = Client(config.require("TWILIO_ACCOUNT_SID"), config.require("TWILIO_AUTH_TOKEN"))
    recordings = []
    for _ in range(retries):
        recordings = client.recordings.list(call_sid=call_sid, limit=1)
        if recordings:
            break
        time.sleep(3)
    if not recordings:
        print(f"[recording] not available yet for {call_sid}")
        return None

    rec_sid = recordings[0].sid
    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Recordings/{rec_sid}.mp3"
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    out = RECORDINGS_DIR / f"recording-{index:02d}.mp3"
    resp = requests.get(url, auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN))
    out.write_bytes(resp.content)
    print(f"[recording] wrote {out} ({len(resp.content)} bytes)")
    return out


def finalize() -> None:
    """Produce the deliverable set: transcripts captured live during each call are
    renamed transcript-NN.txt (in call order), and each call's mp3 is downloaded
    as recording-NN.mp3."""
    import re
    import shutil

    raw = sorted(TRANSCRIPTS_DIR.glob("*_CA*.txt"), key=lambda p: p.stat().st_mtime)
    if not raw:
        print("No raw call transcripts found in transcripts/ — make some calls first.")
        return
    for index, tpath in enumerate(raw, 1):
        match = re.search(r"(CA[0-9a-fA-F]{32})", tpath.name)
        dest = TRANSCRIPTS_DIR / f"transcript-{index:02d}.txt"
        shutil.copyfile(tpath, dest)
        print(f"[finalize] {tpath.name} -> {dest.name}")
        if match:
            download_recording(match.group(1), index)


def demo() -> str:
    """Offline demo: merge the bundled sample channels, no API keys required."""
    entries = merge_transcript(
        load_channel_csv(FIXTURES_DIR / "demo_agent.csv", "Agent"),
        load_channel_csv(FIXTURES_DIR / "demo_patient.csv", "Patient"),
    )
    text = render_transcript(entries)
    print(text)
    return text
