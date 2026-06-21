"""Places the outbound call via Twilio and points it at our media server.

Twilio answers the call leg, fetches TwiML from our /twiml endpoint, and
connects the audio to our WebSocket (see server.py + bot.py). Recording is
enabled in dual-channel mode so each party lands on its own track, which makes
speaker-labeled transcription clean.
"""

from __future__ import annotations

from . import config


def place_call(scenario_id: str) -> str:
    """Dial the assessment test line for one scenario. Returns the call SID."""
    from twilio.rest import Client  # lazy import so the demo/tests need no SDK

    if not config.PUBLIC_HOST:
        raise config.ConfigError(
            "PUBLIC_HOST is not set. Start your tunnel (e.g. ngrok) and set "
            "PUBLIC_HOST to the host it gives you, with no scheme."
        )
    caller = config.CALLER_NUMBER or config.require("TWILIO_CALLER_NUMBER")

    # The only place a destination is chosen — funneled through the guard.
    destination = config.assert_dialable(config.TARGET_NUMBER)

    client = Client(
        config.require("TWILIO_ACCOUNT_SID"),
        config.require("TWILIO_AUTH_TOKEN"),
    )

    twiml_url = f"https://{config.PUBLIC_HOST}/twiml?scenario={scenario_id}"

    call = client.calls.create(
        to=destination,
        from_=caller,
        url=twiml_url,
        method="GET",
        record=True,
        recording_channels="dual",
        time_limit=config.MAX_CALL_SECONDS,
    )
    print(f"[dialer] scenario={scenario_id} call_sid={call.sid} -> {destination}")
    return call.sid
