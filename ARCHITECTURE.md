# Architecture

The bot is a **patient simulator** that calls the clinic's voice agent and
role-plays realistic callers to surface bugs. A call flows as a streaming
pipeline: `dialer.py` places an outbound Twilio call to the assessment test
line and hands the audio to a `<Connect><Stream>` WebSocket served by
`server.py`. From there `bot.py` runs a Pipecat pipeline —
**Twilio audio → Deepgram STT → Claude (patient persona) → Cartesia TTS →
Twilio audio** — with Silero VAD handling turn-taking. The persona comes from a
small JSON *scenario* (`scenarios/`) that fixes the caller's identity, goal, and
the specific bug hypothesis being probed; the prompt is tuned for voice (short
turns, listen-first, active steering, then a clean goodbye via an `end_call`
tool). Calls are recorded by Twilio in **dual-channel** mode so each speaker is
isolated on its own track.

Two key design choices. First, a **pipeline (STT→LLM→TTS) over a speech-to-speech
model**: it keeps per-minute cost well under the budget and, more importantly,
gives full control over the patient persona so each call actively steers toward
its test case instead of drifting. Second, the bot can only ever dial one number
— the approved destination is a hard-coded constant funneled through
`config.assert_dialable()`, so a stray `.env` value can never cause a misdial.
After a call, `transcribe.py` transcribes each recorded channel with Deepgram and
merges them into one speaker-labeled, timestamped transcript, and `analyze.py`
runs an LLM rubric over the transcripts to surface *candidate* bugs that a human
then confirms against the recording and a ground-truth sheet before they reach
the final bug report.
