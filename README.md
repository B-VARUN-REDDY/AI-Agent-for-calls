# Patient Voice Bot — Pretty Good AI engineering challenge

An automated voice bot that **calls the assessment test line
(+1‑805‑439‑8008)**, role-plays realistic patient scenarios, records and
transcribes the calls, and surfaces bugs in the clinic agent's responses.

The bot only ever dials that one number — the destination is a hard-coded
constant guarded by `config.assert_dialable()`.

## Deliverables
- **Code:** `src/` (voice pipeline, dialer, transcription, analysis) + `scenarios/`
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — how it works + key design choices
- **[BUG_REPORT.md](BUG_REPORT.md)** — issues found in the agent's responses
- **[COST_REPORT.md](COST_REPORT.md)** — actual API/telephony spend (≈ $1.73)
- **12 calls:** `transcripts/transcript-01..12.txt` + `recordings/recording-01..12.mp3`
- **Loom walkthrough:** <!-- TODO: paste Loom link -->
- **AI-debugging screen recording:** <!-- TODO: paste link -->

Calls placed from a single number (`+1 971-389-3480`), each a distinct patient
scenario:

| # | Scenario | # | Scenario |
|---|---|---|---|
| 01 | routine refill | 07 | vague request |
| 02 | simple scheduling | 08 | reschedule |
| 03 | Sunday (closed day) | 09 | cancel |
| 04 | insurance question | 10 | office hours / location |
| 05 | controlled-substance refill | 11 | telehealth request |
| 06 | chest pain (escalation) | 12 | new-patient registration |

---

## Quick start

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate            # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. Configure
copy .env.example .env            # Windows  (use: cp on macOS/Linux)
# ...fill in your keys (see .env.example)

# 3. Try it offline — no API keys needed
python -m src.main transcribe --demo
pytest -q
```

## Make real calls

You need a public URL so Twilio can reach your machine:

```bash
# terminal 1: media server
python -m src.main serve

# terminal 2: expose port 8000 and put the host (no scheme) in .env as PUBLIC_HOST
ngrok http 8000

# terminal 3: place a call for a scenario
python -m src.main list                  # list scenarios
python -m src.main call sunday_closed_day
```

After the call, build the transcript and run the first-pass analysis:

```bash
python -m src.main transcribe --call-sid CAxxxxxxxx --index 3
python -m src.main analyze
```

## Layout

```
src/
  config.py       constants, credentials, and the dial safety guard
  scenarios.py    loads scenarios + builds the patient persona prompt
  dialer.py       places the outbound Twilio call (guarded)
  server.py       FastAPI: TwiML + media WebSocket
  bot.py          Pipecat pipeline (STT -> Claude -> TTS), listen-first
  transcribe.py   recording -> per-channel STT -> merged transcript
  analyze.py      LLM rubric -> candidate bug report
  main.py         CLI
scenarios/        one JSON per test case (add your own here)
tests/            offline tests + sample call fixtures
recordings/       call audio (mp3)         [git-ignored by default]
transcripts/      speaker-labeled transcripts
```

## Scenarios

Each file in `scenarios/` defines a caller identity, a goal, and the bug
hypothesis it probes (e.g. *will the agent book a Sunday when the office is
closed?*). Add a test case by dropping in a new JSON file — no code changes.

## Notes

- **Cost:** designed to stay well under $20 — a pipeline (not speech-to-speech),
  cheap TTS, and a `MAX_CALL_SECONDS` cap per call.
- **TTS:** Cartesia and ElevenLabs are both built in. Default is Cartesia
  (lowest latency + cheapest); switch by setting `TTS_PROVIDER=elevenlabs` in
  `.env` — no code change. A/B them after a real call and keep what sounds best.
- **Audio:** Twilio Media Streams are 8 kHz mono mu-law; STT/TTS are aligned to
  `TELEPHONY_SAMPLE_RATE` so the agent never hears sped-up/garbled audio.
- **Pipecat versions** move fast. If an import in `bot.py`/`server.py` fails
  after install, reconcile it with the pinned version in `requirements.txt`.
  The offline `transcribe`/`analyze`/tests paths don't depend on Pipecat.
- **Secrets** live only in `.env` (git-ignored). See `.env.example`.
