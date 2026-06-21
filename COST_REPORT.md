# Cost Report

Actual charges incurred building and running this project (12+ real calls).
**Total: ≈ $1.73** — well under the challenge's "typically less than $20" guideline.

| Service | Used for | Actual charge | Notes |
|---|---|---|---|
| **Twilio** | Outbound calls + phone number | **$1.15** | Month-to-date (June 2026), pay-as-you-go. ~13 calls × 1–3 min + the `+1 971-389-3480` number. |
| **Anthropic (Claude)** | Patient-persona LLM (Sonnet 4.6) | **$0.58** | Dedicated "Pretty Good AI" API key (`sk-ant-…i7s…eQAA`). Bug analysis was done by hand, so no extra Opus spend. |
| **Deepgram** | Speech-to-text | **$0.00** | Covered by the $200 free signup credit. |
| **Cartesia** | Text-to-speech (voices: Ronald, Cathy) | **$0.00** | Free plan (20,000 credits/mo); ~13 calls stayed within the allowance. |
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
- A **`MAX_CALL_SECONDS=240`** cap and an `end_call` tool to avoid dead-air minutes.

## Sources
Figures read from provider dashboards on 2026-06-20: Twilio Billing Overview
(month-to-date spend) and the Anthropic Console API-keys cost column. Deepgram /
Cartesia / ngrok remained within their free allowances (no invoiced charge).
