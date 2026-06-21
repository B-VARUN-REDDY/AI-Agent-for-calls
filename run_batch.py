"""Place a sequence of test calls, waiting for each to finish before the next.

A call is 'done' once its transcript file (written when the call ends) appears.
Run after the server + ngrok are up:  python run_batch.py
"""

import time
from pathlib import Path

from src.dialer import place_call

SCENARIOS = [
    "simple_scheduling",
    "sunday_closed_day",
    "controlled_refill",
    "insurance_hallucination",
    "chest_pain_escalation",
    "vague_request",
    "reschedule_appointment",
    "cancel_appointment",
    "office_hours_location",
    "new_patient_registration",
    "telehealth_request",
]

TX = Path("transcripts")
PER_CALL_TIMEOUT = 280  # seconds

for i, scenario in enumerate(SCENARIOS, 1):
    before = set(TX.glob("*_CA*.txt"))
    print(f"\n=== [{i}/{len(SCENARIOS)}] calling {scenario} ===", flush=True)
    try:
        place_call(scenario)
    except Exception as exc:  # noqa: BLE001
        print(f"  place_call failed: {exc}", flush=True)
        continue

    deadline = time.time() + PER_CALL_TIMEOUT
    done = False
    while time.time() < deadline:
        new = set(TX.glob("*_CA*.txt")) - before
        if new:
            print(f"  done -> {[p.name for p in new]}", flush=True)
            done = True
            break
        time.sleep(5)
    if not done:
        print(f"  TIMEOUT waiting for {scenario}", flush=True)
    time.sleep(6)  # small gap between calls

print("\n=== BATCH COMPLETE ===", flush=True)
