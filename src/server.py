"""FastAPI app that serves TwiML and the media WebSocket for live calls.

Run with:  uvicorn src.server:app --port 8000
(then expose port 8000 with ngrok and set PUBLIC_HOST to the ngrok host).

Note: the live voice pipeline depends on pipecat-ai, whose import paths move
between releases. If an import here fails after `pip install`, check the
version pinned in requirements.txt against your installed pipecat — this is
the one part of the codebase best validated once your keys are in place.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import PlainTextResponse

from . import config

app = FastAPI(title="patient-bot media server")


@app.get("/twiml")
@app.post("/twiml")
async def twiml(request: Request) -> PlainTextResponse:
    """Tell Twilio to stream the call audio to our WebSocket.

    We do NOT play a greeting — the patient bot must listen first and let the
    clinic agent speak before responding.
    """
    scenario = request.query_params.get("scenario", "simple_scheduling")
    ws_url = f"wss://{config.PUBLIC_HOST}/ws"
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}">
      <Parameter name="scenario" value="{scenario}" />
    </Stream>
  </Connect>
</Response>"""
    return PlainTextResponse(content=response, media_type="application/xml")


@app.websocket("/ws")
async def media_ws(websocket: WebSocket) -> None:
    await websocket.accept()

    # Twilio sends a "connected" then a "start" message carrying streamSid and
    # our custom <Parameter> values before any audio frames arrive.
    from .bot import run_bot

    await run_bot(websocket)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
