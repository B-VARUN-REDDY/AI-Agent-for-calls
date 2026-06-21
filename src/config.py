"""Central configuration and the hard safety guard for the patient bot.

Everything that touches money, telephony, or external APIs reads its
settings from here so there is exactly one place to audit.
"""

import os

# Loading a .env file is convenient but optional, so the offline demo and the
# unit tests can run without python-dotenv installed.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - convenience only
    pass


# --------------------------------------------------------------------------
# Hard safety guard
# --------------------------------------------------------------------------
# This bot is ONLY ever allowed to dial the assessment test line. The number on
# the pgai.us/athena confirmation screen must never be called. Keeping the
# allowed destination as a constant (not an env var) means a typo in .env can
# never cause the bot to dial somewhere it shouldn't.
TARGET_NUMBER = "+18054398008"


class ConfigError(RuntimeError):
    """Raised when configuration is missing or unsafe."""


def assert_dialable(number: str) -> str:
    """Return ``number`` only if it is the approved test line, else raise.

    Every code path that places a call must funnel through this.
    """
    normalized = "".join(ch for ch in number if ch.isdigit() or ch == "+")
    if normalized != TARGET_NUMBER:
        raise ConfigError(
            f"Refusing to dial {number!r}. This bot may only call the "
            f"assessment test line {TARGET_NUMBER}."
        )
    return normalized


# --------------------------------------------------------------------------
# Telephony / audio
# --------------------------------------------------------------------------
# Twilio Media Streams are 8 kHz mono mu-law. STT input and TTS output must be
# aligned to this rate or the agent will hear sped-up / garbled audio.
TELEPHONY_SAMPLE_RATE = 8000

# Single Twilio number used for ALL test calls (submitted on the form, E.164).
CALLER_NUMBER = os.getenv("TWILIO_CALLER_NUMBER", "")

# Public host that Twilio can reach (e.g. the ngrok host, no scheme/slash).
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "").replace("https://", "").replace("http://", "").rstrip("/")

# Safety cap so a runaway call can never burn the budget.
MAX_CALL_SECONDS = int(os.getenv("MAX_CALL_SECONDS", "240"))


# --------------------------------------------------------------------------
# API credentials (never commit real values; see .env.example)
# --------------------------------------------------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
# Text-to-speech: both providers are built in; switch with TTS_PROVIDER.
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "cartesia").strip().lower()

CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "")
CARTESIA_MODEL = os.getenv("CARTESIA_MODEL", "sonic-2")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
# Flash/Turbo models are ~half the credit cost and lower latency.
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")

# Model choices kept here so they are easy to tune.
PATIENT_LLM_MODEL = os.getenv("PATIENT_LLM_MODEL", "claude-sonnet-4-6")
ANALYSIS_LLM_MODEL = os.getenv("ANALYSIS_LLM_MODEL", "claude-opus-4-8")


def require(name: str) -> str:
    """Fetch a required env var or raise a clear ConfigError."""
    value = os.getenv(name, "")
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value
