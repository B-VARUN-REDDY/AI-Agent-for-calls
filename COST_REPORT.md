# Cost Report

Actual charges incurred building and running this project (12+ real calls).
**Total: ≈ $1.73** — well under the challenge's "typically less than $20" guideline.

| Service | Used for | Actual charge | Notes |
|---|---|---|---|
| **Twilio** | Outbound calls + phone number | **$1.15** | Month-to-date (June 2026), pay-as-you-go. ~13 calls × 1–3 min + the `+1 971-389-3480` number. |
| **Anthropic (Claude)** | Patient-persona LLM (Sonnet 4.6) | **$0.58** | Dedicated "Pretty Good AI" API key (`sk-ant-…i7s…eQAA`). Bug analysis was done by hand, so no extra Opus spend. |
| **Deepgram** | Speech-to-text | **$0.00** | Covered by the $200 free signup credit. |
| **Cartesia** | Text-to-speech (voices: Ronald, Cathy) | **$0.00** | Free plan includes **20,000 credits/month**; we used only **~7,000**, so it stayed under the limit and **nothing was billed**. |
| **ngrok** | Public tunnel for Twilio media | **$0.00** | Free plan (one static domain). |
| | | **≈ $1.73 total** | |

## Deposit vs. spend (Twilio)
Twilio requires a **$20 minimum starting balance** to upgrade from trial. That
$20 is a **prepaid deposit, not a charge** — only **$1.15** of it was actually
consumed, and **$18.85 remains** as available balance. So out-of-pocket spend on
the assessment was ~$1.73; the rest of the Twilio deposit is still your money.

## Why it stayed cheap
- A **pipeline** (STT → LLM → TTS) instead of a speech-to-speech model — far
  lower per-minute cost.
- **Sonnet** (not Opus) for the live patient, and **manual** bug analysis.
- **Free tiers** for Deepgram, Cartesia, and ngrok covered STT/TTS/tunneling.
  Cartesia in particular bills only *above* 20,000 credits/month — our ~7,000
  credits of speech sat well under that ceiling, so TTS cost nothing.
- A **`MAX_CALL_SECONDS=240`** cap and an `end_call` tool to avoid dead-air minutes.

## Business view

**Marginal cost per call ≈ $0.10–0.15.** Breaking down one ~2-minute call once
every service is on a paid plan: Twilio ~$0.03, Anthropic (Sonnet) ~$0.045,
Deepgram ~$0.015, Cartesia ~$0.015. This run averaged ~$0.13/call all-in,
including the fixed ~$1.15/month phone number; STT/TTS/tunnel were free.

**Scales linearly, no infrastructure.** It's commodity pay-as-you-go APIs — no
servers to run. Rough monthly cost of continuous testing:

| Volume | Est. cost / month |
|---|---|
| 100 calls | ~$10 + $1.15 number |
| 1,000 calls | ~$100 + $1.15 number |

**ROI.** This single QA pass — 12 patient scenarios — surfaced a **critical
safety bug** (a caller reporting chest pain is run through ID collection and
dead-ended before anyone ever asks why they called) for **under $2**. One such
failure reaching a real patient is a serious safety and liability event;
catching it pre-production for the price of a coffee is the entire value
proposition.

**Regression safety net.** The 12-scenario suite can be re-run on every change to
the agent — nightly or in CI — for ~$1–2 per run, turning ad-hoc QA into an
automated guardrail that flags new regressions before patients hit them.

**Cost discipline by design.** Sonnet (not Opus) for the live patient, manual
bug analysis, a 4-minute call cap, and free-tier STT/TTS keep per-call cost at
~10¢ rather than dollars — so quality testing isn't gated by budget.

## Sources
Figures read from provider dashboards on 2026-06-20: Twilio Billing Overview
(month-to-date spend) and the Anthropic Console API-keys cost column. Deepgram /
Cartesia / ngrok remained within their free allowances (no invoiced charge).
