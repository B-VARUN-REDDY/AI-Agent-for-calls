"""`python -m src.main check` — verify credentials before spending on a call.

Two layers:
  1. env presence  — every required value is set and not a placeholder (offline)
  2. live ping      — Twilio + Anthropic actually authenticate, and the caller
                      number really has Voice capability (needs deps installed)

Deepgram and Cartesia keys are presence-checked here and exercised live on the
first call.
"""

from __future__ import annotations

from . import config

PLACEHOLDER_HINTS = ("your_", "your-", "xxxx", "+1xxxx", "acxxxx")


def _is_placeholder(value: str) -> bool:
    if not value:
        return True
    low = value.lower()
    return any(hint in low for hint in PLACEHOLDER_HINTS)


def _env_checks() -> list[tuple[str, str]]:
    required = {
        "TWILIO_ACCOUNT_SID": config.TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": config.TWILIO_AUTH_TOKEN,
        "TWILIO_CALLER_NUMBER": config.CALLER_NUMBER,
        "DEEPGRAM_API_KEY": config.DEEPGRAM_API_KEY,
        "ANTHROPIC_API_KEY": config.ANTHROPIC_API_KEY,
    }
    if config.TTS_PROVIDER == "elevenlabs":
        required["ELEVENLABS_API_KEY"] = config.ELEVENLABS_API_KEY
        required["ELEVENLABS_VOICE_ID"] = config.ELEVENLABS_VOICE_ID
    else:
        required["CARTESIA_API_KEY"] = config.CARTESIA_API_KEY
        required["CARTESIA_VOICE_ID"] = config.CARTESIA_VOICE_ID

    rows = []
    for name, value in required.items():
        rows.append((name, "PASS" if not _is_placeholder(value) else "MISSING"))
    rows.append(
        (
            "PUBLIC_HOST",
            "PASS" if not _is_placeholder(config.PUBLIC_HOST) else "set before calling",
        )
    )
    return rows


def _live_twilio() -> tuple[str, str]:
    from twilio.rest import Client

    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    nums = client.incoming_phone_numbers.list(phone_number=config.CALLER_NUMBER, limit=1)
    if not nums:
        return "FAIL", f"{config.CALLER_NUMBER} is not on this account"
    caps = nums[0].capabilities or {}
    voice = caps.get("voice") if isinstance(caps, dict) else getattr(caps, "voice", None)
    return ("PASS", "voice capability confirmed") if voice else ("FAIL", "number lacks voice")


def _live_anthropic() -> tuple[str, str]:
    from anthropic import Anthropic

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    client.messages.create(
        model=config.PATIENT_LLM_MODEL,
        max_tokens=1,
        messages=[{"role": "user", "content": "ping"}],
    )
    return "PASS", config.PATIENT_LLM_MODEL


def run() -> int:
    failures = 0

    print("== environment ==")
    for name, status in _env_checks():
        mark = "[PASS]" if status == "PASS" else "[ -- ]" if "before calling" in status else "[FAIL]"
        print(f"  {mark} {name}: {status}")
        if status == "MISSING":
            failures += 1

    print("== live auth (needs `pip install -r requirements.txt`) ==")
    for label, fn in (("Twilio", _live_twilio), ("Anthropic", _live_anthropic)):
        try:
            status, detail = fn()
        except Exception as exc:  # noqa: BLE001 - report any failure cleanly
            status, detail = "FAIL", str(exc).splitlines()[0][:140]
        print(f"  {'[PASS]' if status == 'PASS' else '[FAIL]'} {label}: {detail}")
        if status != "PASS":
            failures += 1

    print()
    if failures == 0:
        print("All checks passed - safe to start the server and place a call.")
        return 0
    print(f"{failures} issue(s) to resolve before calling.")
    return 1
